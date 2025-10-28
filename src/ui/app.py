"""Streamlit UI for Fiscal Document Agent."""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st

from src.agent.agent_core import create_agent
import src.database.db as database_db

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
COST_PER_LLM_CALL = 0.001  # USD per API call (used for savings estimation)

st.set_page_config(
    page_title="Fiscal Document Agent",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Minimal, elegant styling (Apple-inspired)
st.markdown(
    """
    <style>
      /* Reduce default padding and roundness for a cleaner look */
      .block-container {padding-top: 2rem; padding-bottom: 2rem;}
      section[data-testid="stSidebar"] .stMarkdown h2 {margin-top: 0.5rem;}
      h1, h2, h3, h4 { color: #1D1D1F; }
      .metric-label { color: #6e6e73; font-size: 0.9rem; }
      .metric-value { color: #1D1D1F; font-weight: 600; }
      /* Subtle divider */
      hr {border: none; border-top: 1px solid #e5e5e7; margin: 0.75rem 0;}
      /* Buttons */
      .stButton>button { border-radius: 10px; padding: 0.5rem 1rem; }
      /* Reduce upload section spacing */
      .uploadedFile { padding: 0.5rem; }
      /* Fix scroll jumping */
      html { scroll-behavior: smooth; }
    </style>
    """,
    unsafe_allow_html=True,
)


def init_agent(api_key: str) -> None:
    """
    Initialize the agent with the given API key.

    Args:
        api_key: Google Gemini API key

    Raises:
        ValueError: If API key is invalid or agent initialization fails
    """
    if "agent" not in st.session_state or st.session_state.get("api_key") != api_key:
        try:
            logger.info("Initializing agent...")
            st.session_state.agent = create_agent(api_key=api_key, model_name="gemini-2.5-flash-lite")
            st.session_state.api_key = api_key
            logger.info("Agent initialized successfully")
        except (ValueError, KeyError, RuntimeError) as e:
            logger.error(f"Failed to initialize agent: {e}", exc_info=True)
            st.error(f"❌ Erro ao inicializar agente: {e}")
            st.session_state.agent = None


def get_cached_db(db_path: str) -> database_db.DatabaseManager:
    """
    Get or create cached database manager in session state.

    Args:
        db_path: Path to database file

    Returns:
        DatabaseManager instance cached in session state

    This avoids creating new connections on every rerun.

    Raises:
        OSError: If database path is invalid or inaccessible
        ValueError: If database initialization fails
    """
    db_key = f"db_manager_{db_path}"
    if db_key not in st.session_state:
        try:
            st.session_state[db_key] = database_db.DatabaseManager(
                database_url=f"sqlite:///{db_path}"
            )
        except (OSError, ValueError, RuntimeError) as e:
            logger.error(f"Failed to initialize database: {e}")
            st.error(f"❌ Erro ao conectar ao banco de dados: {e}")
            return None
    return st.session_state[db_key]


def main() -> None:
    """Main Streamlit application."""
    st.title("📄 Fiscal Document Agent")
    st.caption("Elegant, focused workspace for Brazilian fiscal documents")

    # Show connection status in header if needed
    if st.session_state.get("agent"):
        st.success("✅ Agent Ready", icon="🤖")

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Settings")

        # API Key input
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            help="Enter your Google Gemini API key for LLM-powered classification",
        )

        # Initialize agent when API key is provided
        if api_key:
            init_agent(api_key)

        # Storage settings
        st.subheader("📁 Storage")
        db_path = st.text_input("Database Path", value="./fiscal_documents.db")

        st.divider()

        # System status
        st.subheader("🔌 Status")
        if api_key and st.session_state.get("agent"):
            st.success("✅ Agent connected to Gemini")
        elif api_key:
            st.warning("⏳ Initializing agent...")
        else:
            st.warning("⚠️ No API Key (limited mode)")

        st.caption(f"💾 Database: {db_path}")

    # Native Streamlit tabs - no CSS complexity
    tab_home, tab_documents, tab_reports, tab_statistics = st.tabs(
        ["🏠 Home", "📄 Documents", "📈 Reports", "📊 Statistics"]
    )

    # ============= HOME TAB =============
    with tab_home:
        # Chat interface as primary interaction
        st.header("💬 Chat with Your Documents")
        st.caption("Ask in natural language. Portuguese or English. Minimal answers, clear actions.")

        # Initialize chat messages
        if "messages" not in st.session_state:
            st.session_state.messages = []

            # Add greeting if agent is available
            if st.session_state.get("agent"):
                greeting = st.session_state.agent.get_greeting()
                st.session_state.messages.append({"role": "assistant", "content": greeting})

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask about your fiscal documents..."):
            # Check if agent is available
            if not st.session_state.get("agent"):
                st.warning(
                    "⚠️ Por favor, configure sua chave API do Gemini na barra lateral "
                    "para usar o chat."
                )
            else:
                # Add user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                with st.chat_message("user"):
                    st.markdown(prompt)

                # Get agent response
                with st.chat_message("assistant"):
                    with st.spinner("🤔 Pensando..."):
                        try:
                            response = st.session_state.agent.chat(prompt)
                            st.markdown(response)
                            st.session_state.messages.append({"role": "assistant", "content": response})
                        except (ValueError, KeyError, RuntimeError, TimeoutError) as e:
                            error_msg = f"❌ Erro ao processar mensagem: {str(e)}"
                            st.error(error_msg)
                            logger.error(f"Chat error: {e}", exc_info=True)

        # Quick Actions below chat
        st.markdown("---")
        st.markdown("#### Quick Actions")
        st.caption("Navigate to key features")

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            if st.button("⬆️ Upload XMLs", use_container_width=True, type="secondary"):
                st.switch_page("page_documents")
        with c2:
            if st.button("🔍 Search Documents", use_container_width=True, type="secondary"):
                st.switch_page("page_documents")
        with c3:
            if st.button("📊 View Statistics", use_container_width=True, type="secondary"):
                st.switch_page("page_statistics")
        with c4:
            if st.button("📈 Generate Report", use_container_width=True, type="secondary"):
                st.switch_page("page_reports")

    # ============= DOCUMENTS TAB =============
    with tab_documents:
        st.header("📄 Documents")

        # Upload Section - compact and collapsed by default
        with st.expander("⬆️ Upload Fiscal Documents", expanded=False):
            st.caption("Upload single XMLs, multiple files, or ZIP archives (NFe, NFCe, CTe, MDFe)")
            from src.ui.components.async_upload import render_async_upload_tab
            render_async_upload_tab()

        # Explorer section - main focus
        st.subheader("🔍 Browse & Search")
        from src.ui.components.documents_explorer import render_documents_explorer
        
        db_docs = get_cached_db(db_path)
        if db_docs:
            render_documents_explorer(db_docs)

    # ============= REPORTS TAB =============
    with tab_reports:
        # Reports Tab with full reporting functionality
        from src.ui.components.reports_tab import render_reports_tab

        db_reports = get_cached_db(db_path)
        if db_reports:
            render_reports_tab(db_reports)

    # ============= STATISTICS TAB =============
    with tab_statistics:
        st.header("📊 Statistics & Overview")

        # Database statistics
        try:
            db_stats_mgr = get_cached_db(db_path)
            if not db_stats_mgr:
                st.error("Cannot connect to database")
                return

            db_stats = db_stats_mgr.get_statistics()

            # Key metrics
            st.subheader("Overview")
            c1, c2, c3, c4 = st.columns(4)
            with c1:
                st.metric("📄 Documents", db_stats.get("total_invoices", 0))
            with c2:
                st.metric("🛒 Items", db_stats.get("total_items", 0))
            with c3:
                st.metric("⚠️ Issues", db_stats.get("total_issues", 0))
            with c4:
                st.metric("💵 Total Value", f"R$ {db_stats.get('total_value', 0):,.2f}")

            st.divider()

            # Documents by type
            if db_stats.get("by_type"):
                st.subheader("📊 Documents by Type")
                type_df = {
                    "Type": list(db_stats["by_type"].keys()),
                    "Count": list(db_stats["by_type"].values()),
                }
                st.bar_chart(type_df, x="Type", y="Count", use_container_width=True)
            else:
                st.info("No documents in database yet.")

            st.divider()

            # Cache statistics
            st.subheader("🎯 Classification Cache")
            st.caption("Intelligent system that reduces LLM costs by reusing classifications")

            cache_stats = db_stats_mgr.get_cache_statistics()

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("🗄️ Cache Entries", cache_stats["total_entries"])
            with col2:
                st.metric("🎯 Cache Hits", cache_stats["total_hits"])
            with col3:
                st.metric("📈 Effectiveness", f"{cache_stats['cache_effectiveness']:.1f}%")
            with col4:
                avg_hits = cache_stats["avg_hits_per_entry"]
                cost_saved = cache_stats["total_hits"] * COST_PER_LLM_CALL
                st.metric("💰 Savings", f"${cost_saved:.2f}")

            if cache_stats["total_entries"] > 0:
                st.success(
                    f"✅ Cache working! {cache_stats['total_hits']} classifications "
                    f"reused from {cache_stats['total_entries']} saved patterns."
                )
            else:
                st.info("💡 No classifications in cache yet. Process documents to populate the cache.")

        except (ValueError, OSError, RuntimeError) as e:
            logger.error(f"Error loading statistics: {e}")
            st.error(f"Error loading statistics: {e}")


if __name__ == "__main__":
    main()
