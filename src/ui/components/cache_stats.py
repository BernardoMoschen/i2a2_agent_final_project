"""Cache statistics component for Streamlit."""

import logging

import streamlit as st

logger = logging.getLogger(__name__)

# Constants
COST_PER_LLM_CALL = 0.001  # USD per API call (used for savings estimation)


def render_cache_stats(db):
    """Render cache statistics in expander."""
    
    with st.expander("📊 Cache de Classificações (Economia de LLM)", expanded=False):
        try:
            stats = db.get_cache_statistics()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "🗄️ Entradas em Cache",
                    stats["total_entries"],
                    help="Classificações únicas armazenadas"
                )
            
            with col2:
                st.metric(
                    "🎯 Cache Hits",
                    stats["total_hits"],
                    help="Vezes que o cache foi usado ao invés de chamar LLM"
                )
            
            with col3:
                st.metric(
                    "📈 Efetividade",
                    f"{stats['cache_effectiveness']:.1f}%",
                    help="Percentual de classificações que vieram do cache"
                )
            
            with col4:
                avg_hits = stats["avg_hits_per_entry"]
                cost_saved = stats["total_hits"] * COST_PER_LLM_CALL
                st.metric(
                    "💰 Economia Estimada",
                    f"${cost_saved:.2f}",
                    help=f"Economia em chamadas LLM (média {avg_hits:.1f} hits/entrada)"
                )
            
            if stats["total_entries"] > 0:
                st.success(
                    f"✅ Cache funcionando! {stats['total_hits']} classificações "
                    f"reutilizadas de {stats['total_entries']} padrões salvos."
                )
            else:
                st.info("💡 Nenhuma classificação em cache ainda. Processe alguns documentos para popular o cache.")
                
        except (ValueError, KeyError, RuntimeError, OSError) as e:
            logger.error(f"Error rendering cache stats: {e}", exc_info=True)
            st.error("Erro ao carregar estatísticas de cache")
