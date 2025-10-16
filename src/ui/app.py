"""Streamlit UI for Fiscal Document Agent."""

import streamlit as st

st.set_page_config(
    page_title="Fiscal Document Agent",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded",
)


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

        # Upload directory
        st.subheader("📁 Storage Settings")
        archive_dir = st.text_input("Archive Directory", value="./archives")
        db_path = st.text_input("Database Path", value="./fiscal_documents.db")

        st.divider()

        # System status
        st.subheader("🔌 System Status")
        if api_key:
            st.success("✅ API Key configured")
        else:
            st.warning("⚠️ No API Key (fallback mode)")

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

            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("🔍 Parse", type="primary", use_container_width=True):
                    st.info("Parser integration coming soon...")
            with col2:
                if st.button("✔️ Validate", use_container_width=True):
                    st.info("Validator integration coming soon...")
            with col3:
                if st.button("🏷️ Classify", use_container_width=True):
                    st.info("Classifier integration coming soon...")

            # Display uploaded files
            st.subheader("Uploaded Files")
            for file in uploaded_files:
                with st.expander(f"📄 {file.name}"):
                    st.text(f"Size: {file.size / 1024:.2f} KB")
                    st.text(f"Type: {file.type}")

    with tab2:
        st.header("Chat with Your Documents")
        st.markdown("Ask questions about your fiscal documents using natural language.")

        # Chat messages container
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Chat input
        if prompt := st.chat_input("Ask about your fiscal documents..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            # Placeholder response
            with st.chat_message("assistant"):
                response = (
                    "🔧 Agent integration coming soon. I'll be able to answer "
                    "questions about your documents once the LangChain agent "
                    "is wired up!"
                )
                st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})

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
