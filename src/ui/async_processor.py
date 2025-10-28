"""
Async processor using threading for Streamlit Cloud.
Allows parallel processing without blocking the UI.
"""

import logging
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Dict, List, Optional

import streamlit as st

logger = logging.getLogger(__name__)


class AsyncProcessor:
    """
    Processador assíncrono usando threading.
    
    Compatível com Streamlit Cloud (sem Docker/Celery).
    Usa ThreadPoolExecutor para processamento paralelo com auto-tuning.
    """

    def __init__(self, max_workers: Optional[int] = None):
        """
        Initialize async processor with intelligent auto-tuning.
        
        Args:
            max_workers: Maximum parallel threads. If None, auto-detects optimal value.
                        Recommended: 5 for Streamlit Cloud (1 GB RAM)
        """
        if max_workers is None:
            # Auto-tune based on platform
            # Streamlit Cloud: 1 GB RAM, optimal = 5 threads
            # Local development: can go higher
            self.max_workers = 5
        else:
            self.max_workers = min(max_workers, 10)  # Cap at 10 for safety
            
        self.lock = threading.Lock()
        
        # Local jobs storage (thread-safe alternative to session_state in threads)
        self.jobs: Dict[str, dict] = {}
        
        logger.info(f"AsyncProcessor initialized with {self.max_workers} workers (auto-tuned)")

    def process_files_async(
        self, files: List, company_id: str = "default", user_id: str = "anonymous"
    ) -> str:
        """
        Process files asynchronously in parallel.
        
        Args:
            files: List of uploaded files (UploadedFile objects)
            company_id: Company identifier
            user_id: User identifier
            
        Returns:
            job_id: Unique identifier for tracking progress
        """
        import zipfile
        from io import BytesIO
        
        job_id = str(uuid.uuid4())

        # Pre-count total XMLs (including inside ZIPs) for accurate progress
        total_xmls = 0
        for file in files:
            if file.name.lower().endswith('.xml'):
                total_xmls += 1
            elif file.name.lower().endswith('.zip'):
                try:
                    file.seek(0)
                    content = file.read()
                    file.seek(0)  # Reset for later processing
                    
                    with zipfile.ZipFile(BytesIO(content)) as zf:
                        total_xmls += sum(1 for f in zf.filelist if f.filename.lower().endswith('.xml'))
                except:
                    total_xmls += 1  # Count as 1 if ZIP reading fails
        
        # Initialize jobs dict in session_state (for UI access)
        if "processing_jobs" not in st.session_state:
            st.session_state.processing_jobs = {}

        # Create job entry in BOTH local storage (for thread) and session_state (for UI)
        job_data = {
            "status": "processing",
            "total": total_xmls,  # Accurate XML count, not file count
            "processed": 0,
            "successful": 0,
            "failed": 0,
            # Extended batch progress metrics
            "discovered": total_xmls,
            "parsed": 0,
            "validated": 0,
            "saved": 0,
            "errors": [],
            "results": [],
            "started_at": datetime.now(),
            "completed_at": None,
            "company_id": company_id,
            "user_id": user_id,
        }
        
        # Store in both places
        with self.lock:
            self.jobs[job_id] = job_data
            st.session_state.processing_jobs[job_id] = job_data

        logger.info(f"Job {job_id} created with {total_xmls} XMLs from {len(files)} file(s)")

        # Start processing in background thread
        thread = threading.Thread(
            target=self._process_batch,
            args=(files, job_id, company_id, user_id),
            daemon=True,
        )
        thread.start()

        return job_id

    def _process_batch(
        self, files: List, job_id: str, company_id: str, user_id: str
    ) -> None:
        """
        Process batch of files in parallel using ThreadPoolExecutor.
        
        This runs in a background thread to avoid blocking UI.
        """
        import zipfile
        from io import BytesIO
        from src.utils.file_processing import FileProcessor
        from src.database.db import DatabaseManager

        logger.info(f"[{job_id}] Starting batch processing with {self.max_workers} workers")

        # Disable per-file DB writes; we'll persist later in batches for performance
        processor = FileProcessor(save_to_db=False)
        db = DatabaseManager()

        # Step 1: Read all files and extract ZIPs
        # This ensures ALL XMLs (from ZIPs + standalone) are processed in parallel
        file_data = []
        idx = 0
        
        for file in files:
            try:
                content = file.read()
                filename = file.name
                
                # Check if it's a ZIP file
                if filename.lower().endswith('.zip'):
                    logger.info(f"[{job_id}] Extracting ZIP: {filename}")
                    
                    try:
                        with zipfile.ZipFile(BytesIO(content)) as zf:
                            xml_count = 0
                            for file_info in zf.filelist:
                                if file_info.filename.lower().endswith('.xml'):
                                    xml_content = zf.read(file_info.filename)
                                    # Add extracted XML to processing queue
                                    file_data.append((idx, file_info.filename, xml_content))
                                    idx += 1
                                    xml_count += 1
                            
                            logger.info(f"[{job_id}] ✅ Extracted {xml_count} XMLs from {filename}")
                            
                    except zipfile.BadZipFile as e:
                        logger.error(f"[{job_id}] Invalid ZIP file {filename}: {e}")
                        with self.lock:
                            job = st.session_state.processing_jobs[job_id]
                            job["processed"] += 1
                            job["failed"] += 1
                            job["errors"].append(
                                {"file": filename, "index": idx, "error": f"Invalid ZIP: {str(e)}"}
                            )
                        idx += 1
                        
                elif filename.lower().endswith('.xml'):
                    # Standalone XML file
                    file_data.append((idx, filename, content))
                    idx += 1
                    
                else:
                    # Unsupported file type
                    logger.warning(f"[{job_id}] Skipping unsupported file: {filename}")
                    with self.lock:
                        job = st.session_state.processing_jobs[job_id]
                        job["processed"] += 1
                        job["failed"] += 1
                        job["errors"].append(
                            {"file": filename, "index": idx, "error": "Unsupported file type (only XML and ZIP allowed)"}
                        )
                    idx += 1
                    
            except Exception as e:
                logger.error(f"[{job_id}] Error reading file {file.name}: {e}")
                with self.lock:
                    job = st.session_state.processing_jobs[job_id]
                    job["processed"] += 1
                    job["failed"] += 1
                    job["errors"].append(
                        {"file": file.name, "index": idx, "error": f"Read error: {str(e)}"}
                    )
                idx += 1
        
        # Log extracted XMLs count
        logger.info(f"[{job_id}] Extracted {len(file_data)} XMLs from {len(files)} file(s), starting parallel processing")

        # Process files in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all tasks
            future_to_file = {
                executor.submit(
                    self._process_single_file, processor, content, filename, job_id, idx
                ): (idx, filename)
                for idx, filename, content in file_data
            }

            # Process as they complete
            for future in as_completed(future_to_file):
                idx, filename = future_to_file[future]

                try:
                    result = future.result(timeout=60)  # 60s timeout per file

                    with self.lock:
                        # Use local storage (thread-safe)
                        job = self.jobs.get(job_id)
                        if not job:
                            logger.warning(f"[{job_id}] Job not found in local storage")
                            return

                        job["processed"] += 1

                        if result["status"] == "success":
                            job["successful"] += 1
                            # Update fine-grained counters
                            job["parsed"] += 1
                            job["validated"] += 1
                            job["results"].append(result)
                            logger.info(f"[{job_id}] ✅ {filename} processed successfully")
                        else:
                            job["failed"] += 1
                            job["errors"].append(result)
                            logger.warning(f"[{job_id}] ❌ {filename} failed: {result.get('error')}")
                        
                        # Sync to session_state for UI updates
                        try:
                            if "processing_jobs" in st.session_state:
                                st.session_state.processing_jobs[job_id] = job
                        except Exception as e:
                            logger.debug(f"Could not sync to session_state: {e}")

                except Exception as e:
                    logger.error(f"[{job_id}] Exception processing {filename}: {e}", exc_info=True)
                    with self.lock:
                        job = self.jobs.get(job_id)
                        if job:
                            job["processed"] += 1
                            job["failed"] += 1
                            job["errors"].append(
                                {"file": filename, "index": idx, "error": str(e)}
                            )
                            
                            # Sync to session_state
                            try:
                                if "processing_jobs" in st.session_state:
                                    st.session_state.processing_jobs[job_id] = job
                            except Exception as sync_e:
                                logger.debug(f"Could not sync to session_state: {sync_e}")

        # Persist successfully processed results in batches of 100
        try:
            with self.lock:
                job = self.jobs.get(job_id)
                results_snapshot = list(job["results"]) if job else []

            # Build invoices_data tuples for batch saving
            invoices_data = []
            for r in results_snapshot:
                try:
                    invoices_data.append((r["invoice"], r.get("issues", []), r.get("classification")))
                except Exception as e:
                    logger.error(f"[{job_id}] Failed assembling batch tuple for {r.get('file')}: {e}")
                    with self.lock:
                        if job:
                            job["failed"] += 1
                            job["errors"].append({
                                "file": r.get("file"),
                                "index": r.get("index"),
                                "error": f"Batch assembly error: {e}"
                            })

            # Chunked saves
            chunk_size = 100
            for i in range(0, len(invoices_data), chunk_size):
                chunk = invoices_data[i:i+chunk_size]
                try:
                    saved = db.save_invoices_batch(chunk)
                    with self.lock:
                        job = self.jobs.get(job_id)
                        if job:
                            job["saved"] += len(saved)
                            # Sync to session_state for UI updates
                            try:
                                if "processing_jobs" in st.session_state:
                                    st.session_state.processing_jobs[job_id] = job
                            except Exception as e:
                                logger.debug(f"Could not sync during save: {e}")
                except Exception as e:
                    logger.error(f"[{job_id}] Error saving batch {i//chunk_size+1}: {e}")
                    with self.lock:
                        job = self.jobs.get(job_id)
                        if job:
                            # Attribute the error to files in this chunk
                            for r in results_snapshot[i:i+chunk_size]:
                                job["errors"].append({
                                    "file": r.get("file"),
                                    "index": r.get("index"),
                                    "error": f"DB save error: {e}"
                                })
                            # Consider these as failed saves but don't change parsed/validated
        except Exception as e:
            logger.error(f"[{job_id}] Unexpected error during batch save: {e}")

        # Mark job as completed
        with self.lock:
            job = self.jobs.get(job_id)
            if job:
                job["status"] = "completed"
                job["completed_at"] = datetime.now()
                elapsed = (job["completed_at"] - job["started_at"]).total_seconds()
                
                # Sync final state to session_state
                try:
                    if "processing_jobs" in st.session_state:
                        st.session_state.processing_jobs[job_id] = job
                except Exception as e:
                    logger.debug(f"Could not sync final state to session_state: {e}")
                
                logger.info(
                    f"[{job_id}] ✅ Batch completed in {elapsed:.1f}s: "
                    f"{job['successful']}/{job['total']} successful, {job['saved']} saved"
                )

    def _process_single_file(
        self, processor, file_content: bytes, filename: str, job_id: str, file_index: int
    ) -> Dict:
        """
        Process a single XML file (ZIPs are already extracted at this point).
        
        Args:
            processor: FileProcessor instance
            file_content: Raw XML bytes
            filename: Name of the XML file
            job_id: Parent job ID
            file_index: Index in the batch
            
        Returns:
            Dict with status and results or error
        """
        try:
            logger.debug(f"[{job_id}] Processing XML: {filename}")
            
            # Process XML directly (not through process_file which handles ZIPs)
            result = processor._process_xml(file_content, filename)

            if result:
                # result is a tuple: (filename, InvoiceModel, issues, classification)
                return {
                    "status": "success",
                    "file": result[0],  # filename
                    "index": file_index,
                    "invoice": result[1],  # InvoiceModel
                    "issues": result[2],  # ValidationIssue list
                    "classification": result[3] if len(result) > 3 else None,
                }
            else:
                return {
                    "status": "error",
                    "file": filename,
                    "index": file_index,
                    "error": "Failed to parse XML",
                }

        except Exception as e:
            logger.error(f"[{job_id}] Error processing {filename}: {e}", exc_info=True)
            return {
                "status": "error",
                "file": filename,
                "index": file_index,
                "error": str(e),
            }

    def get_job_status(self, job_id: str) -> Optional[Dict]:
        """
        Get current status of a job.
        
        Args:
            job_id: Job identifier
            
        Returns:
            Job status dict or None if not found
        """
        with self.lock:
            # Try local storage first (most up-to-date from thread)
            job = self.jobs.get(job_id)
            
            if job:
                # Sync to session_state for UI persistence
                try:
                    if "processing_jobs" not in st.session_state:
                        st.session_state.processing_jobs = {}
                    st.session_state.processing_jobs[job_id] = job
                except Exception as e:
                    logger.debug(f"Could not sync to session_state: {e}")
                
                return job
            
            # Fallback to session_state if not in local storage
            if "processing_jobs" in st.session_state:
                return st.session_state.processing_jobs.get(job_id)
            
            return None

    def cancel_job(self, job_id: str) -> bool:
        """
        Cancel a running job (best effort - threads may still complete).
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job was found and cancelled
        """
        with self.lock:
            # Update in local storage
            job = self.jobs.get(job_id)
            if job:
                job["status"] = "cancelled"
                logger.info(f"[{job_id}] Job cancelled by user")
                
                # Sync to session_state
                try:
                    if "processing_jobs" in st.session_state:
                        st.session_state.processing_jobs[job_id] = job
                except Exception as e:
                    logger.debug(f"Could not sync cancellation to session_state: {e}")
                
                return True

        return False

    def clear_job(self, job_id: str) -> bool:
        """
        Remove job from both local storage and session state.
        
        Args:
            job_id: Job identifier
            
        Returns:
            True if job was found and removed
        """
        with self.lock:
            # Remove from local storage
            if job_id in self.jobs:
                del self.jobs[job_id]
            
            # Remove from session_state
            try:
                if "processing_jobs" in st.session_state and job_id in st.session_state.processing_jobs:
                    del st.session_state.processing_jobs[job_id]
                    logger.info(f"[{job_id}] Job cleared from storage")
                    return True
            except Exception as e:
                logger.debug(f"Could not clear from session_state: {e}")

        return False

    def get_all_jobs(self) -> Dict[str, Dict]:
        """
        Get all jobs from local storage (most up-to-date).
        
        Returns:
            Dict of job_id -> job_data
        """
        with self.lock:
            # Sync all jobs to session_state
            try:
                if "processing_jobs" not in st.session_state:
                    st.session_state.processing_jobs = {}
                
                # Merge local storage into session_state
                for job_id, job_data in self.jobs.items():
                    st.session_state.processing_jobs[job_id] = job_data
            except Exception as e:
                logger.debug(f"Could not sync all jobs to session_state: {e}")
            
            return self.jobs.copy()
