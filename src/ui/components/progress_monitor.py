"""
Componente de progresso em tempo real que não bloqueia a UI.
Usa placeholders e auto-update em vez de st.rerun() completo.
"""

import logging
import time
from datetime import datetime

import streamlit as st

from src.ui.async_processor import AsyncProcessor

logger = logging.getLogger(__name__)


def render_live_progress(job_id: str, placeholder):
    """
    Renderiza progresso em tempo real usando placeholder.
    Não recarrega a página inteira, apenas atualiza o componente.
    
    Args:
        job_id: ID do job
        placeholder: st.empty() placeholder para atualizar
    """
    processor = AsyncProcessor()
    
    max_iterations = 180  # ~3 min com sleep de 1s
    iteration = 0
    
    while iteration < max_iterations:
        job = processor.get_job_status(job_id)
        
        if not job:
            with placeholder.container():
                st.error("❌ Job não encontrado")
            break
        
        status = job["status"]
        
        # Renderizar progresso no placeholder (sem recarregar página)
        with placeholder.container():
            # Use 'saved' as main progress to reflect DB persistence
            progress = job.get("saved", 0) / job["total"] if job["total"] > 0 else 0
            st.progress(progress, text=f"{job.get('saved', 0)}/{job['total']} salvos no banco")
            
            # Extended metrics grid
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                st.metric("� Descobertos", job.get("discovered", job["total"]))
            with col2:
                st.metric("🧩 Parseados", job.get("parsed", 0))
            with col3:
                st.metric("✅ Validados", job.get("validated", 0))
            with col4:
                st.metric("💾 Salvos", job.get("saved", 0))
            with col5:
                st.metric("⚙️ Processados", job["processed"])
            with col6:
                st.metric("❌ Falhas", job["failed"])
            
            # Time estimate
            if status == "processing":
                elapsed = (datetime.now() - job["started_at"]).total_seconds()
                avg_time = elapsed / job["processed"] if job["processed"] > 0 else 2
                remaining = (job["total"] - job["processed"]) * avg_time
                st.caption(f"⏱️ Tempo restante estimado: ~{remaining:.0f}s")
                
                # Atualizar a cada 1 segundo
                time.sleep(1)
                iteration += 1
            else:
                # Processamento concluído ou cancelado
                break
    
    # Retornar status final
    return processor.get_job_status(job_id)


def create_progress_monitor(job_id: str):
    """
    Cria monitor de progresso que atualiza automaticamente.
    Retorna quando o job estiver completo.
    
    Args:
        job_id: ID do job a monitorar
        
    Returns:
        dict com status final do job
    """
    st.info("⏳ **Processamento em andamento**. Você pode navegar para outras abas livremente.", icon="ℹ️")
    
    # Criar placeholder para updates
    progress_placeholder = st.empty()
    
    # Monitorar progresso
    final_status = render_live_progress(job_id, progress_placeholder)
    
    return final_status
