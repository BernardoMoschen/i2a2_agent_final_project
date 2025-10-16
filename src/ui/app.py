"""Streamlit UI for Fiscal Document Agent."""

import logging
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import streamlit as st

from src.agent.agent_core import create_agent
from src.utils.file_processing import (
    FileProcessor,
    format_invoice_summary,
    format_items_table,
    format_validation_issues,
)

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
    tab1, tab2, tab3, tab4 = st.tabs(["📤 Upload", "💬 Chat", "📊 Validation", "📈 Reports"])

    with tab1:
        st.header("Upload Fiscal Documents")
        st.markdown("Upload single XML files or ZIP archives containing multiple documents.")

        uploaded_files = st.file_uploader(
            "Choose XML or ZIP files",
            type=["xml", "zip"],
            accept_multiple_files=True,
        )

        if uploaded_files:
            st.success(f"✅ {len(uploaded_files)} file(s) uploaded")

            # Process button
            if st.button("🔍 Process All Files", type="primary", use_container_width=True):
                processor = FileProcessor()

                # Initialize progress
                progress_bar = st.progress(0)
                status_text = st.empty()

                all_results = []

                # Process each file
                for idx, uploaded_file in enumerate(uploaded_files):
                    status_text.text(f"Processing {uploaded_file.name}...")

                    # Read file content
                    file_content = uploaded_file.read()

                    # Process file
                    results = processor.process_file(file_content, uploaded_file.name)
                    all_results.extend(results)

                    # Update progress
                    progress_bar.progress((idx + 1) / len(uploaded_files))

                status_text.text(f"✅ Processed {len(all_results)} document(s)")
                progress_bar.empty()

                # Store results in session state
                st.session_state.processed_documents = all_results

                # Display results
                st.divider()
                st.subheader("📋 Processing Results")

                for filename, invoice, issues in all_results:
                    with st.expander(f"📄 {filename} - {invoice.document_type} {invoice.document_number}", expanded=True):
                        # Summary
                        st.markdown(format_invoice_summary(invoice))

                        # Validation
                        st.markdown("#### ✅ Validação")
                        st.markdown(format_validation_issues(issues))

                        # Items table
                        st.markdown("#### 🛒 Itens do Documento")
                        st.markdown(format_items_table(invoice))

            # Display previously processed documents
            elif "processed_documents" in st.session_state and st.session_state.processed_documents:
                st.divider()
                st.subheader("📋 Previously Processed Documents")

                for filename, invoice, issues in st.session_state.processed_documents:
                    with st.expander(f"📄 {filename} - {invoice.document_type} {invoice.document_number}"):
                        st.markdown(format_invoice_summary(invoice))
                        st.markdown("#### ✅ Validação")
                        st.markdown(format_validation_issues(issues))
                        st.markdown("#### 🛒 Itens")
                        st.markdown(format_items_table(invoice))

    with tab2:
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

    with tab3:
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

    with tab4:
        st.header("Reports & Visualizations")
        st.markdown("Generate reports and visualize your fiscal data.")

        col1, col2 = st.columns(2)

        with col1:
            st.subheader("📊 Report Generation")
            st.selectbox("Report Type", ["Summary", "Detailed", "Tax Analysis"])
            st.date_input("Date Range", value=[])

            if st.button("📥 Generate Report", type="primary"):
                st.info("Report generation coming soon...")

        with col2:
            st.subheader("📈 Quick Stats")
            st.metric("Documents Processed", "0")
            st.metric("Total Value", "R$ 0,00")
            st.metric("Validation Pass Rate", "-%")

        st.divider()

        st.subheader("📉 Placeholder Visualization")
        st.info("Charts and graphs will appear here once documents are processed.")


if __name__ == "__main__":
    main()
