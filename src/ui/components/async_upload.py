"""
Async upload component for Streamlit.
Provides non-blocking upload with real-time progress tracking.
"""

import logging
import time
from datetime import datetime

import streamlit as st

from src.ui.async_processor import AsyncProcessor
from src.utils.file_processing import format_classification, format_validation_issues

logger = logging.getLogger(__name__)


def render_async_upload_tab():
    """Render async upload tab with real-time progress and auto-tuned parallelism."""

    st.header("⚡ Upload Fiscal Documents")
    
    # Warning about background job
    if "current_job_id" in st.session_state:
        processor = AsyncProcessor()
        job = processor.get_job_status(st.session_state.current_job_id)
        if job and job["status"] == "processing":
            st.info("⏳ **Processing Active**. You can freely navigate between tabs. Processing continues in the background.", icon="📋")
    
    # File uploader

import logging
import time
from datetime import datetime

import streamlit as st

from src.ui.async_processor import AsyncProcessor
from src.utils.file_processing import format_classification, format_validation_issues

logger = logging.getLogger(__name__)


def render_async_upload_tab():
    """Render async upload tab with real-time progress and auto-tuned parallelism."""

    st.header("⚡ Upload de Documentos Fiscais")
    
    # Info banner with document support
    st.info(
        "📄 **Supported Documents:** NFe, NFCe, CTe (transport), MDFe (manifest) | "
        "📦 Accepts individual XMLs or ZIPs with multiple documents",
        icon="ℹ️"
    )
    
    # Container fixo para evitar scroll jump durante updates
    progress_container = st.empty()


    # File uploader
    uploaded_files = st.file_uploader(
        "Select XMLs or ZIP files",
        type=["xml", "zip"],
        accept_multiple_files=True,
        key="async_uploader",
        help="Supports NFe, NFCe, CTe, MDFe - individual files or ZIPs",
    )

    if not uploaded_files:
        st.info("👆 Select one or more files to start")
        
        # Show active jobs if any (mesmo sem upload novo)
        _show_active_jobs()
        
        # Check if there is active job in processing
        if "current_job_id" in st.session_state:
            processor = AsyncProcessor()
            job = processor.get_job_status(st.session_state.current_job_id)
            if job and job["status"] == "processing":
                st.divider()
                st.warning("⚠️ **There is processing underway**. You can navigate to other tabs while you wait.")
                with st.container():
                    render_job_progress(st.session_state.current_job_id)
        
        return

    # Count XMLs (including those inside ZIPs)
    import zipfile
    from io import BytesIO
    
    xml_count = 0
    zip_count = 0
    total_xml_count = 0
    
    for file in uploaded_files:
        if file.name.lower().endswith('.xml'):
            xml_count += 1
            total_xml_count += 1
        elif file.name.lower().endswith('.zip'):
            zip_count += 1
            # Count XMLs inside ZIP
            try:
                file.seek(0)  # Reset file pointer
                content = file.read()
                file.seek(0)  # Reset again for later processing
                
                with zipfile.ZipFile(BytesIO(content)) as zf:
                    xml_in_zip = sum(1 for f in zf.filelist if f.filename.lower().endswith('.xml'))
                    total_xml_count += xml_in_zip
            except:
                # If ZIP is invalid, count as 1 to avoid confusion
                total_xml_count += 1
    
    st.success(f"✅ **{total_xml_count} XMLs** detected ({xml_count} loose + {zip_count} ZIP(s))")

    # Auto-configure optimal thread count (max performance)
    max_workers = 5  # Optimal for Streamlit Cloud (1 GB RAM)
    
    # Show metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("📋 XMLs", total_xml_count)
    
    with col2:
        estimated_time = total_xml_count * 2 / max_workers  # ~2s per XML
        st.metric("⏱️ Estimated Time", f"~{estimated_time:.0f}s")
    
    with col3:
        st.metric("⚡ Processing", f"{max_workers} threads")

    # Process button
    if st.button(
        "🚀 Process Documents",
        type="primary",
        use_container_width=True,
    ):
        # Auto-tuned processor (no manual configuration needed)
        processor = AsyncProcessor()

        # Start async processing
        job_id = processor.process_files_async(
            files=uploaded_files,
            company_id=st.session_state.get("company_id", "default"),
            user_id=st.session_state.get("user_id", "anonymous"),
        )

        st.session_state.current_job_id = job_id
        st.success(f"✅ Processing **{total_xml_count} XMLs** started!")

        # Force rerun to show progress
        time.sleep(0.5)
        st.rerun()

    # Show current job progress usando progress monitor (sem st.rerun)
    if "current_job_id" in st.session_state:
        st.divider()
        
        from src.ui.components.progress_monitor import create_progress_monitor
        
        # Este monitor atualiza automaticamente usando placeholders (não bloqueia UI)
        final_status = create_progress_monitor(st.session_state.current_job_id)
        
        # Mostrar resultados finais
        if final_status and final_status["status"] == "completed":
            _show_job_results(final_status)
            
            # Limpar job ID após visualização
            if st.button("🗑️ Limpar resultados"):
                del st.session_state.current_job_id
                st.rerun()




def _show_job_results(job: dict):
    """Show completed job results with tabs for success vs errors."""
    
    st.divider()
    st.success(f"✅ Processing completed: {job['successful']} successes, {job['failed']} failures")
    
    # Time summary
    if job.get("completed_at"):
        total_time = (job["completed_at"] - job["started_at"]).total_seconds()
        st.caption(f"⏱️ Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
    
    # Tabs for success vs errors
    tab1, tab2 = st.tabs(
        [
            f"✅ Processed Documents ({job['successful']})",
            f"❌ Errors ({job['failed']})",
        ]
    )

    with tab1:
        if job.get("results"):
            for result in job["results"]:
                _render_success_result(result)
        else:
            st.info("No document was successfully processed")

    with tab2:
        if job.get("errors"):
            for error in job["errors"]:
                st.error(
                    f"**{error['file']}** (index {error['index']}): {error['error']}"
                )
            # Download CSV of errors
            import io, csv
            csv_buffer = io.StringIO()
            writer = csv.writer(csv_buffer)
            writer.writerow(["file", "index", "error"]) 
            for e in job["errors"]:
                writer.writerow([e.get("file"), e.get("index"), e.get("error")])
            st.download_button(
                label="⬇️ Download error list (CSV)",
                data=csv_buffer.getvalue(),
                file_name=f"upload_errors_{job['started_at'].strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )
        else:
            st.success("No errors found! 🎉")


def render_job_progress(job_id: str):
    """Render real-time progress for a job."""

    processor = AsyncProcessor()
    job = processor.get_job_status(job_id)

    if not job:
        st.error("❌ Job not found")
        if st.button("🗑️ Clear"):
            if "current_job_id" in st.session_state:
                del st.session_state.current_job_id
            st.rerun()
        return

    # Header with job ID
    st.subheader(f"📊 Processing: `{job_id[:8]}...`")

    # Status badge
    status = job["status"]
    status_container = st.empty()
    
    with status_container.container():
        if status == "processing":
            st.info("⏳ Processing in the background... (interface remains usable)", icon="ℹ️")
        elif status == "completed":
            st.success("✅ Processing completed!")
        elif status == "cancelled":
            st.warning("⚠️ Processing cancelled")
        else:
            st.error(f"❌ Status: {status}")

    # Progress bar (use saved/total to reflect persistence)
    progress = job.get("saved", 0) / job["total"] if job["total"] > 0 else 0
    st.progress(progress, text=f"{job.get('saved', 0)}/{job['total']} saved to database")

    # Extended Metrics
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

    # Time tracking
    elapsed = (datetime.now() - job["started_at"]).total_seconds()
    
    if status == "completed" and job["completed_at"]:
        total_time = (job["completed_at"] - job["started_at"]).total_seconds()
        st.caption(f"⏱️ Total time: {total_time:.1f}s ({total_time/60:.1f} min)")
    elif status == "processing":
        avg_time = elapsed / job["processed"] if job["processed"] > 0 else 2
        remaining = (job["total"] - job["processed"]) * avg_time
        st.caption(
            f"⏱️ Elapsed: {elapsed:.1f}s | Remaining: ~{remaining:.0f}s"
        )

    # Auto-refresh while processing (1s polling)
    if status == "processing":
        time.sleep(1)
        st.rerun()

    # Results section (only when completed)
    if status == "completed":
        st.divider()

        # Tabs for success vs errors
        tab1, tab2 = st.tabs(
            [
                f"✅ Processed Documents ({job['successful']})",
                f"❌ Errors ({job['failed']})",
            ]
        )

        with tab1:
            if job["results"]:
                for result in job["results"]:
                    _render_success_result(result)
            else:
                st.info("No documents were successfully processed")

        with tab2:
            if job["errors"]:
                for error in job["errors"]:
                    st.error(
                        f"**{error['file']}** (index {error['index']}): {error['error']}"
                    )
                # Provide CSV download of errors
                import io, csv
                csv_buffer = io.StringIO()
                writer = csv.writer(csv_buffer)
                writer.writerow(["file", "index", "error"])
                for e in job["errors"]:
                    writer.writerow([e.get("file"), e.get("index"), e.get("error")])
                st.download_button(
                    label="⬇️ Download errors (CSV)",
                    data=csv_buffer.getvalue(),
                    file_name=f"upload_errors_{job_id[:8]}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )
            else:
                st.success("No errors found! 🎉")

        # Action buttons
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🗑️ Clear Job", type="secondary", use_container_width=True):
                processor.clear_job(job_id)
                if "current_job_id" in st.session_state:
                    del st.session_state.current_job_id
                st.rerun()
        
        with col2:
            if st.button("🔄 New Processing", type="primary", use_container_width=True):
                if "current_job_id" in st.session_state:
                    del st.session_state.current_job_id
                st.rerun()


def _render_success_result(result: dict):
    """Render a successful processing result with visual document type badges."""
    
    invoice = result["invoice"]
    issues = result.get("issues", [])
    classification = result.get("classification")
    
    # Document type emoji and color
    doc_type_info = {
        "NFe": {"emoji": "🧾", "color": "blue"},
        "NFCe": {"emoji": "🧾", "color": "green"},
        "CTe": {"emoji": "🚚", "color": "orange"},
        "MDFe": {"emoji": "📋", "color": "purple"},
    }
    
    info = doc_type_info.get(invoice.document_type, {"emoji": "📄", "color": "gray"})
    
    # Build expander title with document type badge
    title = f"{info['emoji']} **{invoice.document_type}** {invoice.document_number}"
    if invoice.document_type in ["CTe", "MDFe"]:
        title += f" - {result['file']}"
    else:
        title += f" - {invoice.issuer_name[:30]}..."

    with st.expander(title, expanded=False):
        # Invoice summary
        col1, col2 = st.columns(2)
        
        with col1:
            doc_label = {
                "NFe": "Electronic Invoice",
                "NFCe": "Consumer Invoice",
                "CTe": "Transport Knowledge",
                "MDFe": "Manifest of Documents"
            }.get(invoice.document_type, invoice.document_type)
            
            st.markdown(f"""
            **Type:** {doc_label}  
            **Number:** {invoice.document_number}/{invoice.series}  
            **Key:** `{invoice.document_key}`  
            **Date:** {invoice.issue_date.strftime("%d/%m/%Y %H:%M")}
            """)
        
        with col2:
            # Show different info based on document type
            if invoice.document_type in ["CTe", "MDFe"]:
                st.markdown(f"""
                **Carrier:** {invoice.issuer_name}  
                **CNPJ:** {invoice.issuer_cnpj}  
                **Origin:** {invoice.issuer_uf or "N/A"}  
                **Destination:** {invoice.recipient_uf or "N/A"}
                """)
            else:
                st.markdown(f"""
                **Issuer:** {invoice.issuer_name}  
                **CNPJ:** {invoice.issuer_cnpj}  
                **Recipient:** {invoice.recipient_name or "N/A"}  
                """)

        # Financial info (skip for MDFe which has no values)
        if invoice.document_type != "MDFe":
            st.markdown("### 💰 Values")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                label = "Service" if invoice.document_type == "CTe" else "Products"
                st.metric(label, f"R$ {invoice.total_products:,.2f}")
            with col2:
                st.metric("Taxes", f"R$ {invoice.total_taxes:,.2f}")
            with col3:
                st.metric("Total", f"R$ {invoice.total_invoice:,.2f}")
        else:
            st.info("📋 **Manifest:** Control document (no monetary values)", icon="ℹ️")

        # Classification
        if classification:
            st.markdown("### 🏷️ Automatic Classification")
            st.success(format_classification(classification))

        # Validation issues
        if issues:
            st.markdown("### ⚠️ Validation Issues")
            st.warning(format_validation_issues(issues))
        else:
            st.success("✅ No validation issues found!")


def _show_active_jobs():
    """Show list of all active jobs in session."""
    
    processor = AsyncProcessor()
    all_jobs = processor.get_all_jobs()
    
    if not all_jobs:
        return
    
    st.divider()
    st.subheader("📋 Active Jobs")
    
    for job_id, job in all_jobs.items():
        with st.expander(
            f"Job {job_id[:8]}... - {job['status'].upper()} "
            f"({job['processed']}/{job['total']})",
            expanded=False
        ):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Status", job['status'])
            with col2:
                st.metric("Progress", f"{job['processed']}/{job['total']}")
            with col3:
                if st.button("📊 View Details", key=f"view_{job_id}"):
                    st.session_state.current_job_id = job_id
                    st.rerun()
