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
        st.header("📋 Document History")
        st.markdown("Browse all documents stored in the database with advanced filters and pagination.")
        
        st.info(
            "💡 **Tip**: If you don't see your documents, try selecting **'All Time'** "
            "in the Date Range filter to include older documents."
        )

        # Initialize database
        from src.database.db import DatabaseManager
        
        # Convert file path to SQLite URL
        database_url = f"sqlite:///{db_path}"
        db = DatabaseManager(database_url=database_url)

        # Filters section
        st.subheader("🔍 Filters")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            filter_type = st.selectbox(
                "Document Type",
                options=["All", "NFe", "NFCe", "CTe", "MDFe"],
                key="history_filter_type"
            )

        with col2:
            filter_operation = st.selectbox(
                "Operation Type",
                options=["All", "Purchase", "Sale", "Transfer", "Return"],
                key="history_filter_operation"
            )

        with col3:
            filter_cnpj = st.text_input(
                "Issuer CNPJ (contains)",
                placeholder="00.000.000/0000-00",
                key="history_filter_cnpj"
            )

        with col4:
            # Date filter with presets
            date_preset = st.selectbox(
                "Date Range",
                options=["All Time", "Last 7 days", "Last 30 days", "Last 90 days", "Last Year", "Custom"],
                index=0,  # Default to "All Time"
                key="history_date_preset"
            )
        
        # Custom date range if selected
        if date_preset == "Custom":
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input(
                    "Start Date",
                    value=None,
                    key="history_start_date"
                )
            with col2:
                end_date = st.date_input(
                    "End Date", 
                    value=None,
                    key="history_end_date"
                )
        else:
            start_date = None
            end_date = None

        # Pagination settings
        st.subheader("📄 Pagination")
        col1, col2 = st.columns(2)
        
        with col1:
            page_size = st.selectbox(
                "Documents per page",
                options=[10, 25, 50, 100],
                index=1,  # Default to 25
                key="history_page_size"
            )
        
        # Initialize page number in session state
        if "history_page" not in st.session_state:
            st.session_state.history_page = 1

        # Build filters for database query
        db_filters = {}
        if filter_type != "All":
            db_filters["invoice_type"] = filter_type
        if filter_cnpj:
            db_filters["issuer_cnpj"] = filter_cnpj
        if filter_operation != "All":
            # Convert UI label to database value (lowercase)
            db_filters["operation_type"] = filter_operation.lower()
        
        # Handle date filtering based on preset
        if date_preset == "All Time":
            # No date filter - show all documents
            pass
        elif date_preset == "Last 7 days":
            db_filters["days_back"] = 7
        elif date_preset == "Last 30 days":
            db_filters["days_back"] = 30
        elif date_preset == "Last 90 days":
            db_filters["days_back"] = 90
        elif date_preset == "Last Year":
            db_filters["days_back"] = 365
        elif date_preset == "Custom":
            # Use custom date range
            if start_date:
                db_filters["start_date"] = datetime.combine(start_date, datetime.min.time())
            if end_date:
                db_filters["end_date"] = datetime.combine(end_date, datetime.max.time())

        # Query database with pagination
        offset = (st.session_state.history_page - 1) * page_size
        invoices = db.search_invoices(limit=page_size, offset=offset, **db_filters)

        # Get total count for pagination
        all_invoices = db.search_invoices(**db_filters)  # Without limit/offset
        total_documents = len(all_invoices)
        total_pages = (total_documents + page_size - 1) // page_size  # Ceiling division

        # Display statistics
        st.divider()
        st.subheader("📊 Statistics")
        
        # Get aggregate stats first
        stats = db.get_statistics()
        all_time_total = stats.get("total_invoices", 0)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Filtered Results", total_documents)
        with col2:
            st.metric("Current Page", f"{st.session_state.history_page}/{total_pages if total_pages > 0 else 1}")
        with col3:
            st.metric("Showing", f"{len(invoices)}")
        with col4:
            st.metric("All-time Total", all_time_total)
        
        # Help message if no results but database has documents
        if total_documents == 0 and all_time_total > 0:
            st.info(
                f"ℹ️ No documents found with current filters, but there are **{all_time_total}** "
                f"documents in the database. Try selecting **'All Time'** in the Date Range filter "
                f"to see older documents."
            )

        # Display documents
        st.divider()
        st.subheader(f"📄 Documents (Page {st.session_state.history_page}/{total_pages if total_pages > 0 else 1})")

        if not invoices:
            st.info("ℹ️ No documents found matching the current filters.")
        else:
            # Create DataFrame for tabular view
            import pandas as pd
            
            df_data = []
            for inv in invoices:
                total_invoice = float(inv.total_invoice) if inv.total_invoice else 0.0
                
                # Operation type emoji
                operation_emoji = {
                    "purchase": "📥",
                    "sale": "📤",
                    "transfer": "🔄",
                    "return": "↩️",
                }.get(inv.operation_type, "📄") if inv.operation_type else "❓"
                
                operation_display = f"{operation_emoji} {inv.operation_type.title()}" if inv.operation_type else "Not classified"
                
                df_data.append({
                    "Date": inv.issue_date.strftime("%Y-%m-%d %H:%M") if inv.issue_date else "N/A",
                    "Type": inv.document_type,
                    "Operation": operation_display,
                    "Number": inv.document_number,
                    "Issuer": inv.issuer_name[:25] + "..." if len(inv.issuer_name) > 25 else inv.issuer_name,
                    "CNPJ": inv.issuer_cnpj,
                    "Total": f"R$ {total_invoice:,.2f}",
                    "Items": len(inv.items) if inv.items else 0,
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # Detailed view in expanders
            st.subheader("📝 Detailed View")
            for inv in invoices:
                # Get validation issues for this invoice
                issues = db.get_validation_issues(inv.id) if hasattr(db, 'get_validation_issues') else []
                
                with st.expander(
                    f"📄 {inv.document_type} {inv.document_number} - {inv.issuer_name[:40]}"
                ):
                    # Summary
                    # Format values safely
                    total_products = float(inv.total_products) if inv.total_products else 0.0
                    total_taxes = float(inv.total_taxes) if inv.total_taxes else 0.0
                    total_invoice = float(inv.total_invoice) if inv.total_invoice else 0.0
                    
                    summary_md = f"""
**Número:** {inv.document_number}  
**Tipo:** {inv.document_type}  
**Data de Emissão:** {inv.issue_date.strftime('%d/%m/%Y %H:%M') if inv.issue_date else 'N/A'}  
**Chave de Acesso:** `{inv.document_key}`  

**Emitente:**  
- **Nome:** {inv.issuer_name}  
- **CNPJ:** {inv.issuer_cnpj}  

**Destinatário:**  
- **Nome:** {inv.recipient_name or 'N/A'}  
- **CNPJ/CPF:** {inv.recipient_cnpj_cpf or 'N/A'}  

**Valores:**  
- **Produtos:** R$ {total_products:,.2f}  
- **Impostos:** R$ {total_taxes:,.2f}  
- **Total:** R$ {total_invoice:,.2f}  
"""
                    st.markdown(summary_md)

                    # Classification (if available)
                    if inv.operation_type or inv.cost_center:
                        st.markdown("#### 🏷️ Classificação")
                        classification_dict = {
                            "operation_type": inv.operation_type,
                            "cost_center": inv.cost_center,
                            "confidence": inv.classification_confidence,
                            "reasoning": inv.classification_reasoning,
                            "used_llm_fallback": inv.used_llm_fallback,
                        }
                        st.markdown(format_classification(classification_dict))

                    # Items
                    if inv.items:
                        st.markdown("#### 🛒 Itens")
                        items_data = []
                        for item in inv.items:
                            unit_price = float(item.unit_price) if item.unit_price else 0.0
                            total_price = float(item.total_price) if item.total_price else 0.0
                            items_data.append({
                                "Code": item.product_code,
                                "Description": item.description[:40] + "..." if len(item.description) > 40 else item.description,
                                "NCM": item.ncm or "N/A",
                                "Qty": float(item.quantity) if item.quantity else 0,
                                "Unit Price": f"R$ {unit_price:,.2f}",
                                "Total": f"R$ {total_price:,.2f}",
                            })
                        items_df = pd.DataFrame(items_data)
                        st.dataframe(items_df, use_container_width=True, hide_index=True)

                    # Validation issues
                    if issues:
                        st.markdown("#### ⚠️ Validation Issues")
                        for issue in issues:
                            severity_emoji = "🔴" if issue.severity == "error" else "🟡"
                            st.markdown(f"{severity_emoji} **{issue.code}**: {issue.message}")
                    
                    # Action buttons
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button(f"🗑️ Delete", key=f"delete_{inv.id}"):
                            try:
                                db.delete_invoice(inv.id)
                                st.success("✅ Document deleted successfully!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error deleting document: {str(e)}")
                    with col2:
                        if st.button(f"📥 Export JSON", key=f"export_{inv.id}"):
                            import json
                            # Export as JSON
                            export_data = {
                                "document_number": inv.document_number,
                                "document_type": inv.document_type,
                                "document_key": inv.document_key,
                                "issue_date": inv.issue_date.isoformat() if inv.issue_date else None,
                                "issuer": {
                                    "name": inv.issuer_name,
                                    "cnpj": inv.issuer_cnpj,
                                },
                                "recipient": {
                                    "name": inv.recipient_name or "N/A",
                                    "cnpj": inv.recipient_cnpj_cpf or "N/A",
                                },
                                "totals": {
                                    "products": float(inv.total_products) if inv.total_products else 0,
                                    "taxes": float(inv.total_taxes) if inv.total_taxes else 0,
                                    "total": float(inv.total_invoice) if inv.total_invoice else 0,
                                },
                                "items": [
                                    {
                                        "code": item.product_code,
                                        "description": item.description,
                                        "ncm": item.ncm,
                                        "quantity": float(item.quantity) if item.quantity else 0,
                                        "unit_price": float(item.unit_price) if item.unit_price else 0,
                                        "total_price": float(item.total_price) if item.total_price else 0,
                                    }
                                    for item in (inv.items or [])
                                ],
                            }
                            json_str = json.dumps(export_data, indent=2, ensure_ascii=False)
                            st.download_button(
                                label="Download JSON",
                                data=json_str,
                                file_name=f"{inv.document_number}.json",
                                mime="application/json",
                                key=f"download_{inv.id}"
                            )

        # Pagination controls
        st.divider()
        col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
        
        with col1:
            if st.button("⏮️ First", disabled=(st.session_state.history_page == 1)):
                st.session_state.history_page = 1
                st.rerun()
        
        with col2:
            if st.button("◀️ Previous", disabled=(st.session_state.history_page == 1)):
                st.session_state.history_page -= 1
                st.rerun()
        
        with col3:
            # Page jump
            new_page = st.number_input(
                "Go to page",
                min_value=1,
                max_value=max(1, total_pages),
                value=st.session_state.history_page,
                key="page_jump"
            )
            if new_page != st.session_state.history_page:
                st.session_state.history_page = new_page
                st.rerun()
        
        with col4:
            if st.button("▶️ Next", disabled=(st.session_state.history_page >= total_pages)):
                st.session_state.history_page += 1
                st.rerun()
        
        with col5:
            if st.button("⏭️ Last", disabled=(st.session_state.history_page >= total_pages)):
                st.session_state.history_page = total_pages
                st.rerun()

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


if __name__ == "__main__":
    main()
