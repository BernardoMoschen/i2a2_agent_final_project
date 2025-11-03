"""Cache statistics component for Streamlit."""

import logging

import streamlit as st

logger = logging.getLogger(__name__)

# Constants
COST_PER_LLM_CALL = 0.001  # USD per API call (used for savings estimation)


def render_cache_stats(db):
    """Render cache statistics in expander."""
    
    with st.expander("📊 Classification Cache (LLM Savings)", expanded=False):
        try:
            stats = db.get_cache_statistics()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "🗄️ Cache Entries",
                    stats["total_entries"],
                    help="Unique classifications stored"
                )
            
            with col2:
                st.metric(
                    "🎯 Cache Hits",
                    stats["total_hits"],
                    help="Times cache was used instead of calling LLM"
                )
            
            with col3:
                st.metric(
                    "📈 Effectiveness",
                    f"{stats['cache_effectiveness']:.1f}%",
                    help="Percentage of classifications from cache"
                )
            
            with col4:
                avg_hits = stats["avg_hits_per_entry"]
                cost_saved = stats["total_hits"] * COST_PER_LLM_CALL
                st.metric(
                    "💰 Estimated Savings",
                    f"${cost_saved:.2f}",
                    help=f"Savings on LLM calls (avg {avg_hits:.1f} hits/entry)"
                )
            
            if stats["total_entries"] > 0:
                st.success(
                    f"✅ Cache working! {stats['total_hits']} classifications "
                    f"reused from {stats['total_entries']} saved patterns."
                )
            else:
                st.info("💡 No classifications in cache yet. Process some documents to populate the cache.")
                
        except (ValueError, KeyError, RuntimeError, OSError) as e:
            logger.error(f"Error rendering cache stats: {e}", exc_info=True)
            st.error("Error loading cache statistics")
