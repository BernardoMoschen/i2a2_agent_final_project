"""
Real-time progress component that does not block the UI.
Uses placeholders and auto-update instead of full st.rerun().
"""

import logging
import time
from datetime import datetime

import streamlit as st

from src.ui.async_processor import AsyncProcessor

logger = logging.getLogger(__name__)


def render_live_progress(job_id: str, placeholder):
    """
    Renders real-time progress using placeholder.
    Does not reload the entire page, only updates the component.
    
    Args:
        job_id: Job ID
        placeholder: st.empty() placeholder for updating
    """
    processor = AsyncProcessor()
    
    max_iterations = 180  # ~3 min com sleep de 1s
    iteration = 0
    
    while iteration < max_iterations:
        job = processor.get_job_status(job_id)
        
        if not job:
            with placeholder.container():
                st.error("❌ Job not found")
            break
        
        status = job["status"]
        
        # Renderizar progresso no placeholder (sem recarregar página)
        with placeholder.container():
            # Use 'saved' as main progress to reflect DB persistence
            progress = job.get("saved", 0) / job["total"] if job["total"] > 0 else 0
            st.progress(progress, text=f"{job.get('saved', 0)}/{job['total']} saved to database")
            
            # Extended metrics grid
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                st.metric("📋 Discovered", job.get("discovered", job["total"]))
            with col2:
                st.metric("🧩 Parsed", job.get("parsed", 0))
            with col3:
                st.metric("✅ Validated", job.get("validated", 0))
            with col4:
                st.metric("💾 Saved", job.get("saved", 0))
            with col5:
                st.metric("⚙️ Processed", job["processed"])
            with col6:
                st.metric("❌ Failures", job["failed"])
            
            # Time estimate
            if status == "processing":
                elapsed = (datetime.now() - job["started_at"]).total_seconds()
                avg_time = elapsed / job["processed"] if job["processed"] > 0 else 2
                remaining = (job["total"] - job["processed"]) * avg_time
                st.caption(f"⏱️ Estimated time remaining: ~{remaining:.0f}s")
                
                # Update every 1 second
                time.sleep(1)
                iteration += 1
            else:
                # Processing completed or cancelled
                break
    
    # Retornar status final
    return processor.get_job_status(job_id)


def create_progress_monitor(job_id: str):
    """
    Creates progress monitor that automatically updates.
    Returns when the job is complete.
    
    Args:
        job_id: Job ID to monitor
        
    Returns:
        dict with final job status
    """
    st.info("⏳ **Processing underway**. You can freely navigate to other tabs.", icon="ℹ️")
    
    # Create placeholder for updates
    progress_placeholder = st.empty()
    
    # Monitor progress
    final_status = render_live_progress(job_id, progress_placeholder)
    
    return final_status
