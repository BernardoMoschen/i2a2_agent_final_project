"""Streamlit UI for Fiscal Document Agent."""

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st

from src.agent.agent_core import create_agent
from src.utils.file_processing import format_classification

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(
    page_title="Fiscal Document Agent",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


def init_agent(api_key: str) -> None:
    """
    Initialize the agent with the given API key.

    Args:
        api_key: Google Gemini API key
    """
    if "agent" not in st.session_state or st.session_state.get("api_key") != api_key:
        try:
            logger.info("Initializing agent...")
            st.session_state.agent = create_agent(api_key=api_key, model_name="gemini-2.5-flash-lite")
            st.session_state.api_key = api_key
            logger.info("Agent initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}", exc_info=True)
            st.error(f"❌ Erro ao inicializar agente: {e}")
            st.session_state.agent = None


def main() -> None:
    """Main Streamlit application."""
    st.title("📄 Fiscal Document Agent")
    st.markdown(
        """
        Automated processing, validation, classification, and archiving of
        Brazilian fiscal documents.
        """
    )

    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # API Key input
        api_key = st.text_input(
            "Gemini API Key",
            type="password",
            help="Enter your Google Gemini API key for LLM-powered classification",
        )

        # Initialize agent when API key is provided
        if api_key:
            init_agent(api_key)

        # Upload directory
        st.subheader("📁 Storage Settings")
        archive_dir = st.text_input("Archive Directory", value="./archives")
        db_path = st.text_input("Database Path", value="./fiscal_documents.db")

        st.divider()

        # System status
        st.subheader("🔌 System Status")
        if api_key and st.session_state.get("agent"):
            st.success("✅ Agent connected to Gemini")
        elif api_key:
            st.warning("⏳ Initializing agent...")
        else:
            st.warning("⚠️ No API Key (limited mode)")

        st.info(f"📦 Archive: {archive_dir}")
        st.info(f"💾 Database: {db_path}")

    # Main content area
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
        ["⚡ Upload", "📋 History", "💬 Chat", "📊 Validation", "📈 Reports", "📊 Statistics"]
    )

    with tab1:
        # Async Upload Tab
        from src.ui.components.async_upload import render_async_upload_tab
        render_async_upload_tab()

    with tab2:
        # Initialize database
        from src.database.db import DatabaseManager
        from src.ui.components.documents_explorer import render_documents_explorer

        database_url = f"sqlite:///{db_path}"
        db = DatabaseManager(database_url=database_url)

        render_documents_explorer(db)

    with tab3:
        st.header("Chat with Your Documents")
        st.markdown("Ask questions about your fiscal documents using natural language.")

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
                return

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
                    except Exception as e:
                        error_msg = f"❌ Erro ao processar mensagem: {str(e)}"
                        st.error(error_msg)
                        logger.error(f"Chat error: {e}", exc_info=True)

    with tab4:
        st.header("Validation Results")
        st.markdown("View detailed validation issues for processed documents.")

        # Placeholder validation table
        st.info("No documents processed yet. Upload and validate documents in the Upload tab.")

        # Example structure
        with st.expander("📋 Example Validation Report"):
            st.markdown(
                """
            **Document**: NFe 35240112345678000190550010000000011234567890

            **Validation Summary**:
            - ✅ 8 checks passed
            - ⚠️ 2 warnings
            - ❌ 0 errors

            **Issues**:
            1. **VAL003** (Warning): Sum of item totals does not match
               total_products (tolerance: 0.02)
               - Field: `total_products`
               - Suggestion: Check for rounding errors or missing items

            2. **VAL007** (Info): One or more items missing NCM code
               - Field: `items[].ncm`
               - Suggestion: NCM codes help with classification and tax reporting
            """
            )

    with tab5:
        # Reports Tab with full reporting functionality
        from src.ui.components.reports_tab import render_reports_tab
        
        # Convert file path to SQLite URL
        database_url = f"sqlite:///{db_path}"
        db_reports = DatabaseManager(database_url=database_url)
        
        render_reports_tab(db_reports)

    with tab6:
        st.header("📊 System Statistics")
        
        # Cache statistics
        from src.database.db import DatabaseManager
        from src.ui.components.cache_stats import render_cache_stats
        
        try:
            db = DatabaseManager()
            
            st.subheader("🎯 Classification Cache")
            st.markdown("Intelligent system that reduces LLM costs by reusing classifications from similar documents.")
            
            # Render cache stats (expanded by default in this tab)
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
                    help="Percentage of classifications that came from cache"
                )
            
            with col4:
                avg_hits = stats["avg_hits_per_entry"]
                cost_saved = stats["total_hits"] * 0.001  # Assuming $0.001 per LLM call
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
            
            st.divider()
            
            # Database statistics
            st.subheader("💾 Database Statistics")
            db_stats = db.get_statistics()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📄 Total Documents", db_stats["total_invoices"])
            
            with col2:
                st.metric("🛒 Total Items", db_stats["total_items"])
            
            with col3:
                st.metric("⚠️ Validation Issues", db_stats["total_issues"])
            
            # Documents by type
            if db_stats["by_type"]:
                st.markdown("#### 📊 Documents by Type")
                type_df = {
                    "Type": list(db_stats["by_type"].keys()),
                    "Count": list(db_stats["by_type"].values())
                }
                st.bar_chart(type_df, x="Type", y="Count")
            
            st.metric("💵 Total Value Processed", f"R$ {db_stats['total_value']:,.2f}")
                
        except Exception as e:
            logger.error(f"Error loading statistics: {e}")
            st.error("Error loading statistics")

    with tab6:
        st.header("📊 System Statistics")
        
        # Cache statistics
        from src.database.db import DatabaseManager
        from src.ui.components.cache_stats import render_cache_stats
        
        try:
            db = DatabaseManager()
            
            st.subheader("🎯 Classification Cache")
            st.markdown("Intelligent system that reduces LLM costs by reusing classifications from similar documents.")
            
            # Render cache stats (expanded by default in this tab)
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
                    help="Percentage of classifications that came from cache"
                )
            
            with col4:
                avg_hits = stats["avg_hits_per_entry"]
                cost_saved = stats["total_hits"] * 0.001  # Assuming $0.001 per LLM call
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
            
            st.divider()
            
            # Database statistics
            st.subheader("💾 Database Statistics")
            db_stats = db.get_statistics()
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("📄 Total Documents", db_stats["total_invoices"])
            
            with col2:
                st.metric("🛒 Total Items", db_stats["total_items"])
            
            with col3:
                st.metric("⚠️ Validation Issues", db_stats["total_issues"])
            
            # Documents by type
            if db_stats["by_type"]:
                st.markdown("#### 📊 Documents by Type")
                type_df = {
                    "Type": list(db_stats["by_type"].keys()),
                    "Count": list(db_stats["by_type"].values())
                }
                st.bar_chart(type_df, x="Type", y="Count")
            
            st.metric("💵 Total Value Processed", f"R$ {db_stats['total_value']:,.2f}")
                
        except Exception as e:
            logger.error(f"Error loading statistics: {e}")
            st.error("Error loading statistics")


if __name__ == "__main__":
    main()
