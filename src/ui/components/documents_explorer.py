"""Documents Explorer v2 component with fast filters, pagination and export."""

from __future__ import annotations

from datetime import datetime
import io
import csv
import logging
from typing import Dict, List, Optional

import pandas as pd
import streamlit as st

from src.database.db import DatabaseManager, InvoiceDB

logger = logging.getLogger(__name__)


DATE_PRESETS = [
    "All Time",
    "Last 7 days",
    "Last 30 days",
    "Last 90 days",
    "Last Year",
    "Custom",
]


def _filters_ui() -> Dict:
    """Render filters and return a dict for DB queries."""
    st.subheader("🔍 Filters")
    # Global text search (issuer/recipient names, item descriptions)
    q = st.text_input(
        "Full-text search (issuer/recipient/items)",
        placeholder="e.g., supplier name, item description, or keywords",
        key="explorer_q",
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        doc_type = st.selectbox(
            "Document Type",
            options=["All", "NFe", "NFCe", "CTe", "MDFe"],
            key="explorer_type",
        )

    with col2:
        operation = st.selectbox(
            "Operation Type",
            options=["All", "Purchase", "Sale", "Transfer", "Return"],
            key="explorer_operation",
        )

    with col3:
        issuer = st.text_input(
            "Issuer CNPJ (contains)",
            placeholder="00.000.000/0000-00",
            key="explorer_issuer",
        )

    with col4:
        recipient = st.text_input(
            "Recipient CNPJ/CPF (contains)",
            placeholder="000.000.000-00",
            key="explorer_recipient",
        )

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        modal = st.selectbox(
            "Modal",
            options=["All", "1", "2", "3", "4", "5", "Other"],
            help="CTe/MDFe modal (1=Rodoviário, 2=Aéreo, 3=Aquaviário, 4=Ferroviário, 5=Dutoviário)",
            key="explorer_modal",
        )
    with col2:
        cost_center = st.text_input(
            "Cost Center (exact)",
            placeholder="CC001",
            key="explorer_cost_center",
        )
    with col3:
        min_conf = st.slider(
            "Min Confidence",
            min_value=0.0,
            max_value=1.0,
            value=0.0,
            step=0.05,
            key="explorer_min_conf",
        )
    with col4:
        date_preset = st.selectbox(
            "Date Range",
            options=DATE_PRESETS,
            index=0,
            key="explorer_date_preset",
        )

    start_date = None
    end_date = None
    if date_preset == "Custom":
        c1, c2 = st.columns(2)
        with c1:
            start_date = st.date_input("Start Date", value=None, key="explorer_start")
        with c2:
            end_date = st.date_input("End Date", value=None, key="explorer_end")

    filters: Dict = {}
    if q:
        filters["q"] = q
    if doc_type != "All":
        filters["invoice_type"] = doc_type
    if operation != "All":
        filters["operation_type"] = operation.lower()
    if issuer:
        filters["issuer_cnpj"] = issuer
    if recipient:
        filters["recipient_cnpj"] = recipient
    if modal and modal != "All":
        filters["modal"] = modal
    if cost_center:
        filters["cost_center"] = cost_center
    if min_conf and min_conf > 0:
        filters["min_confidence"] = float(min_conf)

    if date_preset == "Last 7 days":
        filters["days_back"] = 7
    elif date_preset == "Last 30 days":
        filters["days_back"] = 30
    elif date_preset == "Last 90 days":
        filters["days_back"] = 90
    elif date_preset == "Last Year":
        filters["days_back"] = 365
    elif date_preset == "Custom":
        if start_date:
            filters["start_date"] = datetime.combine(start_date, datetime.min.time())
        if end_date:
            filters["end_date"] = datetime.combine(end_date, datetime.max.time())

    return filters


def _to_rows(invoices: List[InvoiceDB]) -> pd.DataFrame:
    rows = []
    for inv in invoices:
        total_invoice = float(inv.total_invoice) if inv.total_invoice else 0.0
        operation_display = (
            {
                "purchase": "📥 purchase",
                "sale": "📤 sale",
                "transfer": "🔄 transfer",
                "return": "↩️ return",
            }.get(inv.operation_type, "📄 not classified")
            if inv.operation_type
            else "❓ not classified"
        )
        rows.append(
            {
                "Select": False,
                "Date": inv.issue_date.strftime("%Y-%m-%d %H:%M") if inv.issue_date else "N/A",
                "Type": inv.document_type,
                "Operation": operation_display,
                "Number": inv.document_number,
                "Issuer": inv.issuer_name,
                "CNPJ": inv.issuer_cnpj,
                "Recipient": inv.recipient_name or "",
                "Recipient Doc": inv.recipient_cnpj_cpf or "",
                "Modal": inv.modal or "",
                "Cost Center": inv.cost_center or "",
                "Confidence": inv.classification_confidence if inv.classification_confidence is not None else "",
                "Items": len(inv.items) if inv.items else 0,
                "Total": total_invoice,
                "Key": inv.document_key,
            }
        )
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df[[
            "Select", "Date", "Type", "Operation", "Number", "Issuer", "CNPJ",
            "Recipient", "Recipient Doc", "Modal", "Cost Center", "Confidence",
            "Items", "Total", "Key",
        ]]
    return df


def render_documents_explorer(db: DatabaseManager) -> None:
    """Render the Documents explorer v2."""
    st.header("📋 Documents Explorer v2")
    st.caption("Fast filtering, server-side pagination, selection and export")

    # Filters
    filters = _filters_ui()

    # Pagination controls
    st.subheader("📄 Pagination")
    c1, c2, c3 = st.columns(3)
    with c1:
        page_size = st.selectbox("Per page", options=[10, 25, 50, 100], index=1, key="explorer_page_size")
    if "explorer_page" not in st.session_state:
        st.session_state.explorer_page = 1

    # Count total efficiently
    total_documents = db.count_invoices(**filters)
    total_pages = max(1, (total_documents + page_size - 1) // page_size)
    st.caption(f"Total: {total_documents} documents · Page {st.session_state.explorer_page}/{total_pages}")

    # Export all filtered (streaming to temp file)
    exp_c1, exp_c2 = st.columns([2, 3])
    with exp_c1:
        st.caption("Export")
        export_disabled = total_documents == 0
        fmt = st.selectbox(
            "Format",
            options=["CSV", "CSV (gzip)", "Parquet"],
            index=0,
            disabled=export_disabled,
            key="explorer_export_fmt",
        )
        if st.button(
            f"⬇️ Export all filtered ({total_documents} rows)",
            disabled=export_disabled,
            key="explorer_export_all_btn",
        ):
            import tempfile, gzip
            from io import TextIOWrapper
            with st.spinner(f"Building {fmt} for all filtered documents..."):
                # Common header
                header = [
                    "Date","Type","Operation","Number","Issuer","CNPJ","Recipient","Recipient Doc",
                    "Modal","Cost Center","Confidence","Items","Total","Key",
                ]
                batch_size = 1000
                if fmt == "CSV":
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv")
                    with open(tmp.name, "w", encoding="utf-8", newline="") as f:
                        w = csv.writer(f)
                        w.writerow(header)
                        for ofs in range(0, total_documents, batch_size):
                            batch = db.search_invoices(limit=batch_size, offset=ofs, **filters)
                            for inv in batch:
                                total_invoice = float(inv.total_invoice) if inv.total_invoice else 0.0
                                op = inv.operation_type or ""
                                w.writerow([
                                    inv.issue_date.isoformat() if inv.issue_date else "",
                                    inv.document_type or "",
                                    op,
                                    inv.document_number or "",
                                    inv.issuer_name or "",
                                    inv.issuer_cnpj or "",
                                    inv.recipient_name or "",
                                    inv.recipient_cnpj_cpf or "",
                                    inv.modal or "",
                                    inv.cost_center or "",
                                    f"{inv.classification_confidence:.2f}" if inv.classification_confidence is not None else "",
                                    len(inv.items) if inv.items else 0,
                                    f"{total_invoice:.2f}",
                                    inv.document_key or "",
                                ])
                    st.download_button(
                        "Download CSV",
                        data=open(tmp.name, "rb"),
                        file_name="documents_filtered_export.csv",
                        mime="text/csv",
                        key="explorer_export_all_dl",
                    )
                elif fmt == "CSV (gzip)":
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv.gz")
                    with gzip.open(tmp.name, mode="wt", encoding="utf-8", newline="") as gz:
                        w = csv.writer(gz)
                        w.writerow(header)
                        for ofs in range(0, total_documents, batch_size):
                            batch = db.search_invoices(limit=batch_size, offset=ofs, **filters)
                            for inv in batch:
                                total_invoice = float(inv.total_invoice) if inv.total_invoice else 0.0
                                op = inv.operation_type or ""
                                w.writerow([
                                    inv.issue_date.isoformat() if inv.issue_date else "",
                                    inv.document_type or "",
                                    op,
                                    inv.document_number or "",
                                    inv.issuer_name or "",
                                    inv.issuer_cnpj or "",
                                    inv.recipient_name or "",
                                    inv.recipient_cnpj_cpf or "",
                                    inv.modal or "",
                                    inv.cost_center or "",
                                    f"{inv.classification_confidence:.2f}" if inv.classification_confidence is not None else "",
                                    len(inv.items) if inv.items else 0,
                                    f"{total_invoice:.2f}",
                                    inv.document_key or "",
                                ])
                    st.download_button(
                        "Download CSV (gzip)",
                        data=open(tmp.name, "rb"),
                        file_name="documents_filtered_export.csv.gz",
                        mime="application/gzip",
                        key="explorer_export_all_gz_dl",
                    )
                elif fmt == "Parquet":
                    try:
                        import pyarrow as pa
                        import pyarrow.parquet as pq
                    except (ImportError, ModuleNotFoundError):
                        st.error("pyarrow is required for Parquet export. Please install pyarrow.")
                    else:
                        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".parquet")
                        writer = None
                        try:
                            for ofs in range(0, total_documents, batch_size):
                                batch = db.search_invoices(limit=batch_size, offset=ofs, **filters)
                                rows = []
                                for inv in batch:
                                    total_invoice = float(inv.total_invoice) if inv.total_invoice else 0.0
                                    rows.append({
                                        "Date": inv.issue_date.isoformat() if inv.issue_date else "",
                                        "Type": inv.document_type or "",
                                        "Operation": inv.operation_type or "",
                                        "Number": inv.document_number or "",
                                        "Issuer": inv.issuer_name or "",
                                        "CNPJ": inv.issuer_cnpj or "",
                                        "Recipient": inv.recipient_name or "",
                                        "Recipient Doc": inv.recipient_cnpj_cpf or "",
                                        "Modal": inv.modal or "",
                                        "Cost Center": inv.cost_center or "",
                                        "Confidence": inv.classification_confidence if inv.classification_confidence is not None else None,
                                        "Items": len(inv.items) if inv.items else 0,
                                        "Total": total_invoice,
                                        "Key": inv.document_key or "",
                                    })
                                df_chunk = pd.DataFrame(rows)
                                table = pa.Table.from_pandas(df_chunk, preserve_index=False)
                                if writer is None:
                                    writer = pq.ParquetWriter(tmp.name, table.schema)
                                writer.write_table(table)
                        finally:
                            if writer is not None:
                                writer.close()
                        st.download_button(
                            "Download Parquet",
                            data=open(tmp.name, "rb"),
                            file_name="documents_filtered_export.parquet",
                            mime="application/octet-stream",
                            key="explorer_export_all_parquet_dl",
                        )

    with exp_c2:
        st.caption("Export (Excel)")
        export_disabled = total_documents == 0
        if st.button(
            f"⬇️ Export all filtered (Excel)",
            disabled=export_disabled,
            key="explorer_export_all_xlsx_btn",
        ):
            with st.spinner("Building Excel workbook for all filtered documents..."):
                # Build datasets in chunks
                invoices_rows = []
                items_rows = []
                batch_size = 1000
                for ofs in range(0, total_documents, batch_size):
                    batch = db.search_invoices(limit=batch_size, offset=ofs, **filters)
                    for inv in batch:
                        total_invoice = float(inv.total_invoice) if inv.total_invoice else 0.0
                        invoices_rows.append(
                            {
                                "Date": inv.issue_date.isoformat() if inv.issue_date else "",
                                "Type": inv.document_type or "",
                                "Operation": inv.operation_type or "",
                                "Number": inv.document_number or "",
                                "Issuer": inv.issuer_name or "",
                                "CNPJ": inv.issuer_cnpj or "",
                                "Recipient": inv.recipient_name or "",
                                "Recipient Doc": inv.recipient_cnpj_cpf or "",
                                "Modal": inv.modal or "",
                                "Cost Center": inv.cost_center or "",
                                "Confidence": inv.classification_confidence if inv.classification_confidence is not None else "",
                                "Items": len(inv.items) if inv.items else 0,
                                "Total": total_invoice,
                                "Key": inv.document_key or "",
                            }
                        )
                        # Items for this invoice
                        if getattr(inv, "items", None):
                            for it in inv.items:
                                items_rows.append(
                                    {
                                        "Invoice Key": inv.document_key or "",
                                        "Item": it.item_number,
                                        "Code": it.product_code,
                                        "Description": it.description,
                                        "NCM": getattr(it, "ncm", None) or "",
                                        "CFOP": getattr(it, "cfop", None) or "",
                                        "Unit": getattr(it, "unit", None) or "",
                                        "Quantity": float(it.quantity) if getattr(it, "quantity", None) else 0.0,
                                        "Unit Price": float(it.unit_price) if getattr(it, "unit_price", None) else 0.0,
                                        "Total Price": float(it.total_price) if getattr(it, "total_price", None) else 0.0,
                                        "ICMS": float(it.taxes.icms) if getattr(it, "taxes", None) and getattr(it.taxes, "icms", None) is not None else 0.0,
                                        "IPI": float(it.taxes.ipi) if getattr(it, "taxes", None) and getattr(it.taxes, "ipi", None) is not None else 0.0,
                                        "PIS": float(it.taxes.pis) if getattr(it, "taxes", None) and getattr(it.taxes, "pis", None) is not None else 0.0,
                                        "COFINS": float(it.taxes.cofins) if getattr(it, "taxes", None) and getattr(it.taxes, "cofins", None) is not None else 0.0,
                                        "ISSQN": float(it.taxes.issqn) if getattr(it, "taxes", None) and getattr(it.taxes, "issqn", None) is not None else 0.0,
                                    }
                                )

                inv_df = pd.DataFrame(invoices_rows)
                items_df = pd.DataFrame(items_rows)

                # Write to Excel with formatting
                import io as _io
                buffer = _io.BytesIO()
                # Prefer xlsxwriter for richer formatting; pandas will import it if installed
                with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
                    inv_df.to_excel(writer, index=False, sheet_name="Invoices")
                    items_df.to_excel(writer, index=False, sheet_name="Items")

                    wb = writer.book
                    ws_inv = writer.sheets["Invoices"]
                    ws_items = writer.sheets["Items"]

                    # Formats
                    header_fmt = wb.add_format({"bold": True, "bg_color": "#F2F2F2", "bottom": 1})
                    money_fmt = wb.add_format({"num_format": "R$ #,##0.00"})
                    num2_fmt = wb.add_format({"num_format": "0.00"})

                    # Apply header format
                    for col, _name in enumerate(inv_df.columns):
                        ws_inv.write(0, col, inv_df.columns[col], header_fmt)
                    for col, _name in enumerate(items_df.columns):
                        ws_items.write(0, col, items_df.columns[col], header_fmt)

                    # Column widths & numeric formats for Invoices
                    inv_widths = {
                        "Date": 20,
                        "Type": 8,
                        "Operation": 12,
                        "Number": 10,
                        "Issuer": 28,
                        "CNPJ": 18,
                        "Recipient": 28,
                        "Recipient Doc": 18,
                        "Modal": 8,
                        "Cost Center": 12,
                        "Confidence": 12,
                        "Items": 8,
                        "Total": 14,
                        "Key": 40,
                    }
                    for i, col in enumerate(inv_df.columns):
                        ws_inv.set_column(i, i, inv_widths.get(col, 12))
                        if col == "Total":
                            ws_inv.set_column(i, i, inv_widths.get(col, 12), money_fmt)
                        if col == "Confidence":
                            ws_inv.set_column(i, i, inv_widths.get(col, 12), num2_fmt)

                    # Column widths & numeric formats for Items
                    items_widths = {
                        "Invoice Key": 40,
                        "Item": 6,
                        "Code": 14,
                        "Description": 40,
                        "NCM": 12,
                        "CFOP": 10,
                        "Unit": 8,
                        "Quantity": 10,
                        "Unit Price": 14,
                        "Total Price": 14,
                        "ICMS": 12,
                        "IPI": 12,
                        "PIS": 12,
                        "COFINS": 12,
                        "ISSQN": 12,
                    }
                    for i, col in enumerate(items_df.columns):
                        ws_items.set_column(i, i, items_widths.get(col, 12))
                        if col in ("Unit Price", "Total Price", "ICMS", "IPI", "PIS", "COFINS", "ISSQN"):
                            ws_items.set_column(i, i, items_widths.get(col, 12), money_fmt)
                        if col == "Quantity":
                            ws_items.set_column(i, i, items_widths.get(col, 12), num2_fmt)

                    # Freeze headers & add filters
                    ws_inv.freeze_panes(1, 0)
                    ws_items.freeze_panes(1, 0)
                    ws_inv.autofilter(0, 0, max(1, len(inv_df)), max(0, len(inv_df.columns) - 1))
                    ws_items.autofilter(0, 0, max(1, len(items_df)), max(0, len(items_df.columns) - 1))

                st.download_button(
                    "Download Excel (Invoices + Items)",
                    data=buffer.getvalue(),
                    file_name="documents_filtered_export.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    key="explorer_export_all_xlsx_dl",
                )
    # Fetch current page
    offset = (st.session_state.explorer_page - 1) * page_size
    invoices = db.search_invoices(limit=page_size, offset=offset, **filters)

    # Dataframe with selection
    df = _to_rows(invoices)
    if df.empty:
        st.info("No documents found for the current filters.")
        return

    # Selection controls
    st.checkbox("Select all on page", key="explorer_select_all")
    if st.session_state.explorer_select_all:
        df["Select"] = True

    edited_df = st.data_editor(
        df,
        use_container_width=True,
        hide_index=True,
        disabled=[
            "Date", "Type", "Operation", "Number", "Issuer", "CNPJ", "Recipient",
            "Recipient Doc", "Modal", "Cost Center", "Confidence", "Items", "Total", "Key",
        ],
        column_config={
            "Total": st.column_config.NumberColumn(format="R$ %.2f"),
            "Confidence": st.column_config.NumberColumn(format="%.2f"),
        },
        key="explorer_table",
    )

    # Determine selected keys
    selected_keys = edited_df.loc[edited_df["Select"] == True, "Key"].tolist()

    # Export and actions
    c1, c2, c3, c4 = st.columns([1.5, 1, 1, 3])
    with c1:
        st.write(f"Selected: {len(selected_keys)}")
    with c2:
        # Export selected as CSV
        if selected_keys:
            export_df = edited_df[edited_df["Select"] == True].drop(columns=["Select"])  # type: ignore
            csv_data = export_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Export selected (CSV)",
                data=csv_data,
                file_name="documents_export.csv",
                mime="text/csv",
                key="explorer_export_csv",
            )
    with c3:
        if st.button("🗑️ Delete selected", disabled=(len(selected_keys) == 0)):
            deleted = 0
            for key in selected_keys:
                try:
                    if db.delete_invoice(key):
                        deleted += 1
                except (ValueError, KeyError, RuntimeError) as e:
                    logger.warning(f"Failed to delete invoice {key}: {e}")
            st.success(f"Deleted {deleted} documents")
            st.session_state.explorer_select_all = False
            st.rerun()

    # Pagination nav
    st.divider()
    c1, c2, c3, c4, c5 = st.columns([1, 1, 2, 1, 1])
    with c1:
        if st.button("⏮️ First", disabled=(st.session_state.explorer_page == 1)):
            st.session_state.explorer_page = 1
            st.rerun()
    with c2:
        if st.button("◀️ Previous", disabled=(st.session_state.explorer_page == 1)):
            st.session_state.explorer_page -= 1
            st.rerun()
    with c3:
        new_page = st.number_input(
            "Go to page",
            min_value=1,
            max_value=total_pages,
            value=st.session_state.explorer_page,
            key="explorer_page_jump",
        )
        if new_page != st.session_state.explorer_page:
            st.session_state.explorer_page = new_page
            st.rerun()
    with c4:
        if st.button("▶️ Next", disabled=(st.session_state.explorer_page >= total_pages)):
            st.session_state.explorer_page += 1
            st.rerun()
    with c5:
        if st.button("⏭️ Last", disabled=(st.session_state.explorer_page >= total_pages)):
            st.session_state.explorer_page = total_pages
            st.rerun()
