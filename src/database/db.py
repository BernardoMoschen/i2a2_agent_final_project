"""Database models and operations using SQLModel and SQLite."""

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple

from sqlalchemy import Index, create_engine, event, func, case, extract
from sqlalchemy import text
from sqlalchemy.orm import selectinload
from sqlmodel import Field, Relationship, Session, SQLModel, select

logger = logging.getLogger(__name__)


class InvoiceDB(SQLModel, table=True):
    """Invoice table for storing fiscal documents."""

    __tablename__ = "invoices"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Document metadata
    document_type: str = Field(index=True)
    document_key: str = Field(unique=True, index=True)
    document_number: str = Field(index=True)
    series: str
    issue_date: datetime = Field(index=True)
    
    # Parties
    issuer_cnpj: str = Field(index=True)
    issuer_name: str
    recipient_cnpj_cpf: Optional[str] = Field(default=None, index=True)
    recipient_name: Optional[str] = Field(default=None)
    
    # Financial totals
    total_products: Decimal = Field(default=Decimal("0"))
    total_taxes: Decimal = Field(default=Decimal("0"))
    total_invoice: Decimal = Field(default=Decimal("0"))
    
    # Tax breakdown
    tax_icms: Decimal = Field(default=Decimal("0"))
    tax_ipi: Decimal = Field(default=Decimal("0"))
    tax_pis: Decimal = Field(default=Decimal("0"))
    tax_cofins: Decimal = Field(default=Decimal("0"))
    tax_issqn: Decimal = Field(default=Decimal("0"))
    
    # Classification fields
    operation_type: Optional[str] = Field(default=None, index=True)
    cost_center: Optional[str] = Field(default=None, index=True)
    classification_confidence: Optional[float] = Field(default=None)
    classification_reasoning: Optional[str] = Field(default=None)
    used_llm_fallback: bool = Field(default=False)
    
    # Transport-specific fields (CTe/MDFe)
    modal: Optional[str] = Field(default=None, index=True)
    rntrc: Optional[str] = Field(default=None)
    vehicle_plate: Optional[str] = Field(default=None)
    vehicle_uf: Optional[str] = Field(default=None)
    route_ufs: Optional[str] = Field(default=None)  # JSON array as string
    cargo_weight: Optional[Decimal] = Field(default=None)
    cargo_weight_net: Optional[Decimal] = Field(default=None)
    cargo_volume: Optional[Decimal] = Field(default=None)
    service_taker_type: Optional[str] = Field(default=None)
    freight_value: Optional[Decimal] = Field(default=None)
    freight_type: Optional[str] = Field(default=None)
    dangerous_cargo: bool = Field(default=False)
    insurance_value: Optional[Decimal] = Field(default=None)
    emission_type: Optional[str] = Field(default=None)
    
    # Metadata
    raw_xml: Optional[str] = Field(default=None)
    parsed_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    # Relationships
    items: List["InvoiceItemDB"] = Relationship(back_populates="invoice", cascade_delete=True)
    issues: List["ValidationIssueDB"] = Relationship(back_populates="invoice", cascade_delete=True)
    
    # Composite indexes for common queries
    __table_args__ = (
        # Search by period + type
        Index('ix_invoices_date_type', 'issue_date', 'document_type'),
        # Search by issuer + period
        Index('ix_invoices_issuer_date', 'issuer_cnpj', 'issue_date'),
        # Search by recipient + period
        Index('ix_invoices_recipient_date', 'recipient_cnpj_cpf', 'issue_date'),
        # Search by cost center + operation type
        Index('ix_invoices_cost_center_op', 'cost_center', 'operation_type'),
        # Transport: modal + period
        Index('ix_invoices_modal_date', 'modal', 'issue_date'),
    )


class InvoiceItemDB(SQLModel, table=True):
    """Invoice item table."""

    __tablename__ = "invoice_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoices.id", index=True)
    
    item_number: int
    product_code: str
    description: str
    ncm: Optional[str] = Field(default=None, index=True)
    cfop: str = Field(index=True)
    unit: str
    quantity: Decimal
    unit_price: Decimal
    total_price: Decimal
    
    # Tax breakdown for item
    tax_icms: Decimal = Field(default=Decimal("0"))
    tax_ipi: Decimal = Field(default=Decimal("0"))
    tax_pis: Decimal = Field(default=Decimal("0"))
    tax_cofins: Decimal = Field(default=Decimal("0"))
    tax_issqn: Decimal = Field(default=Decimal("0"))
    
    # Relationship
    invoice: InvoiceDB = Relationship(back_populates="items")


class ValidationIssueDB(SQLModel, table=True):
    """Validation issue table."""

    __tablename__ = "validation_issues"

    id: Optional[int] = Field(default=None, primary_key=True)
    invoice_id: int = Field(foreign_key="invoices.id", index=True)
    
    code: str = Field(index=True)
    severity: str = Field(index=True)
    message: str
    field: Optional[str] = Field(default=None)
    suggestion: Optional[str] = Field(default=None)
    resolved: bool = Field(default=False, index=True)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    
    # Relationship
    invoice: InvoiceDB = Relationship(back_populates="issues")


class ClassificationCacheDB(SQLModel, table=True):
    """Cache table for document classifications to reduce LLM calls."""

    __tablename__ = "classification_cache"

    id: Optional[int] = Field(default=None, primary_key=True)
    
    # Cache key (hash of issuer_cnpj + ncm + cfop)
    cache_key: str = Field(unique=True, index=True)
    
    # Classification result
    operation_type: str
    cost_center: str
    confidence: float
    reasoning: Optional[str] = Field(default=None)
    used_llm: bool = Field(default=False)
    
    # Metadata
    issuer_cnpj: str = Field(index=True)
    ncm: Optional[str] = Field(default=None, index=True)
    cfop: str = Field(index=True)
    
    # Usage stats
    hit_count: int = Field(default=0)
    last_used_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class DatabaseManager:
    """Manage SQLite database operations."""

    def __init__(self, database_url: str = "sqlite:///fiscal_documents.db"):
        """
        Initialize database manager.

        Args:
            database_url: SQLAlchemy database URL
        """
        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.fts_enabled: bool = False
        
        # Configure SQLite for better performance
        self._configure_sqlite_pragmas()
        
        self._create_tables()
        logger.info(f"Database initialized: {database_url}")
    
    def _configure_sqlite_pragmas(self) -> None:
        """Configure SQLite PRAGMAs for optimal performance."""
        if "sqlite" in self.database_url:
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                # WAL mode allows concurrent reads
                cursor.execute("PRAGMA journal_mode=WAL")
                # Optimized synchronization (NORMAL is safe and faster)
                cursor.execute("PRAGMA synchronous=NORMAL")
                # Larger page cache (10MB)
                cursor.execute("PRAGMA cache_size=-10000")
                # Enable foreign keys
                cursor.execute("PRAGMA foreign_keys=ON")
                # Temp store in memory
                cursor.execute("PRAGMA temp_store=MEMORY")
                # Memory-mapped I/O for faster reads (256MB)
                cursor.execute("PRAGMA mmap_size=268435456")
                cursor.close()
            logger.info("SQLite performance PRAGMAs configured")

    def _create_tables(self) -> None:
        """Create all tables if they don't exist."""
        SQLModel.metadata.create_all(self.engine)
        # Ensure schema is up-to-date for existing databases
        try:
            self._migrate_schema()
        except (ValueError, KeyError, RuntimeError, OSError) as e:
            logger.error(f"Schema migration check failed: {e}")

    def _migrate_schema(self) -> None:
        """
        Lightweight schema migrator for SQLite to add newly introduced columns and indexes.

        This is safe to run repeatedly and will only apply changes if missing.
        """
        if "sqlite" not in self.database_url:
            return

        transport_columns = {
            "modal": "TEXT",
            "rntrc": "TEXT",
            "vehicle_plate": "TEXT",
            "vehicle_uf": "TEXT",
            "route_ufs": "TEXT",
            "cargo_weight": "NUMERIC",
            "cargo_weight_net": "NUMERIC",
            "cargo_volume": "NUMERIC",
            "service_taker_type": "TEXT",
            "freight_value": "NUMERIC",
            "freight_type": "TEXT",
            "dangerous_cargo": "INTEGER DEFAULT 0",
            "insurance_value": "NUMERIC",
            "emission_type": "TEXT",
        }

        composite_indexes = [
            ("ix_invoices_date_type", "invoices", "issue_date, document_type"),
            ("ix_invoices_issuer_date", "invoices", "issuer_cnpj, issue_date"),
            ("ix_invoices_recipient_date", "invoices", "recipient_cnpj_cpf, issue_date"),
            ("ix_invoices_cost_center_op", "invoices", "cost_center, operation_type"),
            ("ix_invoices_modal_date", "invoices", "modal, issue_date"),
        ]

        with self.engine.begin() as conn:
            # Discover existing columns
            existing_cols = set()
            for row in conn.exec_driver_sql("PRAGMA table_info(invoices)").fetchall():
                # PRAGMA table_info columns: cid, name, type, notnull, dflt_value, pk
                existing_cols.add(row[1])

            # Add missing transport columns
            for col, col_type in transport_columns.items():
                if col not in existing_cols:
                    logger.info(f"Applying migration: add column invoices.{col} {col_type}")
                    conn.exec_driver_sql(f"ALTER TABLE invoices ADD COLUMN {col} {col_type}")

            # Ensure composite indexes exist
            for idx_name, table, cols in composite_indexes:
                conn.exec_driver_sql(
                    f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table} ({cols})"
                )

        # Try to ensure FTS after columns exist
        self._ensure_fts()

    def _ensure_fts(self) -> None:
        """Create and populate FTS5 table if available. Sets self.fts_enabled."""
        if "sqlite" not in self.database_url:
            self.fts_enabled = False
            return
        try:
            with self.engine.begin() as conn:
                # Attempt to create FTS5 table
                conn.exec_driver_sql(
                    """
                    CREATE VIRTUAL TABLE IF NOT EXISTS invoices_fts USING fts5(
                        invoice_id UNINDEXED,
                        issuer_name,
                        recipient_name,
                        items_text
                    )
                    """
                )
            self.fts_enabled = True
        except (RuntimeError, OSError, ValueError) as e:
            logger.warning(f"FTS5 not available: {e}")
            self.fts_enabled = False
            return

        # Populate if empty
        try:
            with self.engine.begin() as conn:
                cnt = conn.exec_driver_sql("SELECT count(*) FROM invoices_fts").scalar()
                if cnt == 0:
                    logger.info("Populating FTS index from existing data (this may take a while)...")
                    # Build in chunks
                    offset = 0
                    batch = 1000
                    while True:
                        # Fetch a page of invoices and joined items' descriptions
                        res = conn.exec_driver_sql(
                            """
                            SELECT i.id, i.issuer_name, i.recipient_name
                            FROM invoices i
                            ORDER BY i.id
                            LIMIT :lim OFFSET :off
                            """,
                            {"lim": batch, "off": offset},
                        ).fetchall()
                        if not res:
                            break
                        # For each invoice, collect items_text
                        inv_ids = [row[0] for row in res]
                        items_map = {}
                        if inv_ids:
                            placeholders = ",".join([str(int(x)) for x in inv_ids])
                            items_rows = conn.exec_driver_sql(
                                f"SELECT invoice_id, description FROM invoice_items WHERE invoice_id IN ({placeholders})"
                            ).fetchall()
                            for iid, desc in items_rows:
                                items_map.setdefault(iid, []).append(desc or "")
                        # Insert into FTS
                        for iid, issuer_name, recipient_name in res:
                            items_text = " ".join(items_map.get(iid, []))[:20000]
                            conn.exec_driver_sql(
                                "INSERT INTO invoices_fts (invoice_id, issuer_name, recipient_name, items_text) VALUES (:iid, :inm, :rnm, :it)",
                                {"iid": iid, "inm": issuer_name or "", "rnm": recipient_name or "", "it": items_text},
                            )
                        offset += batch
                    logger.info("FTS index populated")
        except (RuntimeError, OSError, ValueError) as e:
            logger.warning(f"Could not populate FTS index: {e}")

    def save_invoice(self, invoice_model, validation_issues: List, classification: Optional[dict] = None) -> InvoiceDB:
        """
        Save invoice and related data to database.

        Args:
            invoice_model: InvoiceModel from Pydantic
            validation_issues: List of ValidationIssue objects
            classification: Optional dict with classification results
                {operation_type, cost_center, confidence, reasoning, used_llm_fallback}

        Returns:
            Saved InvoiceDB instance
        """
        with Session(self.engine) as session:
            # Check if invoice already exists
            statement = select(InvoiceDB).where(
                InvoiceDB.document_key == invoice_model.document_key
            )
            existing = session.exec(statement).first()
            
            if existing:
                logger.warning(f"Invoice {invoice_model.document_key} already exists")
                # Eagerly load relationships before returning
                session.refresh(existing, ["items", "issues"])
                return existing

            # Create invoice
            invoice_db = InvoiceDB(
                document_type=invoice_model.document_type,
                document_key=invoice_model.document_key,
                document_number=invoice_model.document_number,
                series=invoice_model.series,
                issue_date=invoice_model.issue_date,
                issuer_cnpj=invoice_model.issuer_cnpj,
                issuer_name=invoice_model.issuer_name,
                recipient_cnpj_cpf=invoice_model.recipient_cnpj_cpf,
                recipient_name=invoice_model.recipient_name,
                total_products=invoice_model.total_products,
                total_taxes=invoice_model.total_taxes,
                total_invoice=invoice_model.total_invoice,
                tax_icms=invoice_model.taxes.icms,
                tax_ipi=invoice_model.taxes.ipi,
                tax_pis=invoice_model.taxes.pis,
                tax_cofins=invoice_model.taxes.cofins,
                tax_issqn=invoice_model.taxes.issqn,
                # Transport-specific fields
                modal=invoice_model.modal,
                rntrc=invoice_model.rntrc,
                vehicle_plate=invoice_model.vehicle_plate,
                vehicle_uf=invoice_model.vehicle_uf,
                route_ufs=",".join(invoice_model.route_ufs) if invoice_model.route_ufs else None,
                cargo_weight=invoice_model.cargo_weight,
                cargo_weight_net=invoice_model.cargo_weight_net,
                cargo_volume=invoice_model.cargo_volume,
                service_taker_type=invoice_model.service_taker_type,
                freight_value=invoice_model.freight_value,
                freight_type=invoice_model.freight_type,
                dangerous_cargo=invoice_model.dangerous_cargo,
                insurance_value=invoice_model.insurance_value,
                emission_type=invoice_model.emission_type,
                raw_xml=invoice_model.raw_xml,
                parsed_at=invoice_model.parsed_at,
            )
            
            # Add classification if provided
            if classification:
                invoice_db.operation_type = classification.get("operation_type")
                invoice_db.cost_center = classification.get("cost_center")
                invoice_db.classification_confidence = classification.get("confidence")
                invoice_db.classification_reasoning = classification.get("reasoning")
                invoice_db.used_llm_fallback = classification.get("used_llm_fallback", False)
            
            session.add(invoice_db)
            session.commit()
            session.refresh(invoice_db)
            
            # Save items
            for item in invoice_model.items:
                item_db = InvoiceItemDB(
                    invoice_id=invoice_db.id,
                    item_number=item.item_number,
                    product_code=item.product_code,
                    description=item.description,
                    ncm=item.ncm,
                    cfop=item.cfop,
                    unit=item.unit,
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    total_price=item.total_price,
                    tax_icms=item.taxes.icms,
                    tax_ipi=item.taxes.ipi,
                    tax_pis=item.taxes.pis,
                    tax_cofins=item.taxes.cofins,
                    tax_issqn=item.taxes.issqn,
                )
                session.add(item_db)
            
            # Save validation issues
            for issue in validation_issues:
                issue_db = ValidationIssueDB(
                    invoice_id=invoice_db.id,
                    code=issue.code,
                    severity=issue.severity,
                    message=issue.message,
                    field=issue.field,
                    suggestion=issue.suggestion,
                )
                session.add(issue_db)
            
            session.commit()
            logger.info(f"Saved invoice {invoice_db.document_key} with {len(invoice_model.items)} items")
            
            # Eagerly load relationships before session closes
            session.refresh(invoice_db, ["items", "issues"])
            
            # Update FTS index
            try:
                if self.fts_enabled:
                    items_text = " ".join([it.description or "" for it in invoice_db.items])[:20000]
                    session.exec(
                        text(
                            "INSERT INTO invoices_fts (invoice_id, issuer_name, recipient_name, items_text) VALUES (:iid, :inm, :rnm, :it)"
                        ),
                        {"iid": invoice_db.id, "inm": invoice_db.issuer_name or "", "rnm": invoice_db.recipient_name or "", "it": items_text},
                    )
                    session.commit()
            except Exception as e:
                logger.debug(f"FTS update skipped: {e}")
            
            return invoice_db

    def _create_invoice_db(self, invoice_model, classification: Optional[dict] = None) -> InvoiceDB:
        """
        Helper: Create InvoiceDB instance from InvoiceModel.
        
        Args:
            invoice_model: InvoiceModel from Pydantic
            classification: Optional classification results
            
        Returns:
            InvoiceDB instance (not yet added to session)
        """
        invoice_db = InvoiceDB(
            document_type=invoice_model.document_type,
            document_key=invoice_model.document_key,
            document_number=invoice_model.document_number,
            series=invoice_model.series,
            issue_date=invoice_model.issue_date,
            issuer_cnpj=invoice_model.issuer_cnpj,
            issuer_name=invoice_model.issuer_name,
            recipient_cnpj_cpf=invoice_model.recipient_cnpj_cpf,
            recipient_name=invoice_model.recipient_name,
            total_products=invoice_model.total_products,
            total_taxes=invoice_model.total_taxes,
            total_invoice=invoice_model.total_invoice,
            tax_icms=invoice_model.taxes.icms,
            tax_ipi=invoice_model.taxes.ipi,
            tax_pis=invoice_model.taxes.pis,
            tax_cofins=invoice_model.taxes.cofins,
            tax_issqn=invoice_model.taxes.issqn,
            # Transport-specific fields
            modal=invoice_model.modal,
            rntrc=invoice_model.rntrc,
            vehicle_plate=invoice_model.vehicle_plate,
            vehicle_uf=invoice_model.vehicle_uf,
            route_ufs=",".join(invoice_model.route_ufs) if invoice_model.route_ufs else None,
            cargo_weight=invoice_model.cargo_weight,
            cargo_weight_net=invoice_model.cargo_weight_net,
            cargo_volume=invoice_model.cargo_volume,
            service_taker_type=invoice_model.service_taker_type,
            freight_value=invoice_model.freight_value,
            freight_type=invoice_model.freight_type,
            dangerous_cargo=invoice_model.dangerous_cargo,
            insurance_value=invoice_model.insurance_value,
            emission_type=invoice_model.emission_type,
            raw_xml=invoice_model.raw_xml,
            parsed_at=invoice_model.parsed_at,
        )
        
        # Add classification if provided
        if classification:
            invoice_db.operation_type = classification.get("operation_type")
            invoice_db.cost_center = classification.get("cost_center")
            invoice_db.classification_confidence = classification.get("confidence")
            invoice_db.classification_reasoning = classification.get("reasoning")
            invoice_db.used_llm_fallback = classification.get("used_llm_fallback", False)
        
        return invoice_db

    def _create_item_dbs(self, invoice_db: InvoiceDB, items) -> List[InvoiceItemDB]:
        """
        Helper: Create InvoiceItemDB instances from invoice items.
        
        Args:
            invoice_db: Parent invoice (must have id set)
            items: List of InvoiceItem from InvoiceModel
            
        Returns:
            List of InvoiceItemDB instances
        """
        item_dbs = []
        for item in items:
            item_db = InvoiceItemDB(
                invoice_id=invoice_db.id,
                item_number=item.item_number,
                product_code=item.product_code,
                description=item.description,
                ncm=item.ncm,
                cfop=item.cfop,
                unit=item.unit,
                quantity=item.quantity,
                unit_price=item.unit_price,
                total_price=item.total_price,
                tax_icms=item.taxes.icms,
                tax_ipi=item.taxes.ipi,
                tax_pis=item.taxes.pis,
                tax_cofins=item.taxes.cofins,
                tax_issqn=item.taxes.issqn,
            )
            item_dbs.append(item_db)
        return item_dbs

    def _create_issue_dbs(self, invoice_db: InvoiceDB, validation_issues: List) -> List[ValidationIssueDB]:
        """
        Helper: Create ValidationIssueDB instances from validation issues.
        
        Args:
            invoice_db: Parent invoice (must have id set)
            validation_issues: List of ValidationIssue objects
            
        Returns:
            List of ValidationIssueDB instances
        """
        issue_dbs = []
        for issue in validation_issues:
            issue_db = ValidationIssueDB(
                invoice_id=invoice_db.id,
                code=issue.code,
                severity=issue.severity,
                message=issue.message,
                field=issue.field,
                suggestion=issue.suggestion,
            )
            issue_dbs.append(issue_db)
        return issue_dbs

    def save_invoices_batch(
        self, 
        invoices_data: List[Tuple]
    ) -> List[InvoiceDB]:
        """
        Bulk insert multiple invoices in a single transaction.
        
        10-50x faster than individual save_invoice() calls for large batches.
        Use this when processing ZIP archives with many documents.
        
        Args:
            invoices_data: List of tuples, each containing:
                (invoice_model, validation_issues, classification_dict_or_None)
        
        Returns:
            List of saved InvoiceDB instances with relationships loaded
            
        Example:
            >>> batch = [
            ...     (invoice1, issues1, classification1),
            ...     (invoice2, issues2, None),
            ...     (invoice3, issues3, classification3),
            ... ]
            >>> saved = db.save_invoices_batch(batch)
            >>> print(f"Saved {len(saved)} invoices")
        """
        if not invoices_data:
            return []
        
        saved_invoices = []
        
        with Session(self.engine) as session:
            # Single transaction for all inserts
            for invoice_model, validation_issues, classification in invoices_data:
                # Check if already exists (skip duplicates)
                statement = select(InvoiceDB).where(
                    InvoiceDB.document_key == invoice_model.document_key
                )
                existing = session.exec(statement).first()
                
                if existing:
                    logger.warning(f"Skipping duplicate: {invoice_model.document_key}")
                    saved_invoices.append(existing)
                    continue
                
                # Create invoice
                invoice_db = self._create_invoice_db(invoice_model, classification)
                session.add(invoice_db)
                session.flush()  # Get invoice.id without committing
                
                # Create items
                item_dbs = self._create_item_dbs(invoice_db, invoice_model.items)
                for item_db in item_dbs:
                    session.add(item_db)
                
                # Create issues
                issue_dbs = self._create_issue_dbs(invoice_db, validation_issues)
                for issue_db in issue_dbs:
                    session.add(issue_db)
                
                saved_invoices.append(invoice_db)
            
            # Single commit for entire batch
            session.commit()
            
            logger.info(f"Bulk inserted {len(saved_invoices)} invoices "
                       f"({sum(len(inv.items) for inv in saved_invoices)} items total)")
            
            # Refresh all to load relationships
            for invoice_db in saved_invoices:
                session.refresh(invoice_db, ["items", "issues"])
            
            # Batch update FTS
            try:
                if self.fts_enabled and saved_invoices:
                    for inv in saved_invoices:
                        items_text = " ".join([it.description or "" for it in inv.items])[:20000]
                        session.exec(
                            text(
                                "INSERT INTO invoices_fts (invoice_id, issuer_name, recipient_name, items_text) VALUES (:iid, :inm, :rnm, :it)"
                            ),
                            {"iid": inv.id, "inm": inv.issuer_name or "", "rnm": inv.recipient_name or "", "it": items_text},
                        )
                    session.commit()
            except Exception as e:
                logger.debug(f"FTS batch update skipped: {e}")
        
        return saved_invoices

    def get_invoice_by_key(self, document_key: str) -> Optional[InvoiceDB]:
        """Get invoice by document key with relationships loaded."""
        from sqlalchemy.orm import selectinload
        
        with Session(self.engine) as session:
            statement = select(InvoiceDB).options(
                selectinload(InvoiceDB.items),
                selectinload(InvoiceDB.issues)
            ).where(InvoiceDB.document_key == document_key)
            
            invoice = session.exec(statement).first()
            if invoice:
                # Ensure relationships are loaded
                _ = invoice.items
                _ = invoice.issues
            return invoice

    def get_all_invoices(self, limit: int = 100, offset: int = 0) -> List[InvoiceDB]:
        """Get all invoices with pagination and relationships loaded."""
        from sqlalchemy.orm import selectinload
        
        with Session(self.engine) as session:
            statement = select(InvoiceDB).options(
                selectinload(InvoiceDB.items),
                selectinload(InvoiceDB.issues)
            ).order_by(InvoiceDB.issue_date.desc()).limit(limit).offset(offset)
            
            invoices = list(session.exec(statement).all())
            # Ensure relationships are loaded
            for inv in invoices:
                _ = inv.items
                _ = inv.issues
            return invoices

    def search_invoices(
        self,
        document_type: Optional[str] = None,
        invoice_type: Optional[str] = None,  # Alias for document_type
        operation_type: Optional[str] = None,  # Filter by classification
        issuer_cnpj: Optional[str] = None,
        recipient_cnpj: Optional[str] = None,
        modal: Optional[str] = None,
        cost_center: Optional[str] = None,
        min_confidence: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days_back: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
        q: Optional[str] = None,
    ) -> List[InvoiceDB]:
        """
        Search invoices with filters.

        Args:
            document_type: Filter by document type (NFe, NFCe, etc.)
            invoice_type: Alias for document_type
            operation_type: Filter by operation type (purchase, sale, transfer, return)
            issuer_cnpj: Filter by issuer CNPJ (contains search)
            recipient_cnpj: Filter by recipient CNPJ/CPF (contains search)
            modal: Filter by transport modal (CTe/MDFe)
            cost_center: Filter by cost center (classification)
            min_confidence: Minimum classification confidence
            start_date: Filter by issue date >= start_date
            end_date: Filter by issue date <= end_date
            days_back: Filter by documents from last N days
            limit: Maximum results
            offset: Skip first N results (for pagination)

        Returns:
            List of matching invoices with eagerly loaded relationships
        """
        from sqlalchemy.orm import selectinload
        
        with Session(self.engine) as session:
            statement = select(InvoiceDB).options(
                selectinload(InvoiceDB.items),
                selectinload(InvoiceDB.issues)
            )
            
            # Full-text search
            if q:
                if self.fts_enabled:
                    try:
                        # Fetch matching IDs via FTS
                        id_rows = session.exec(
                            text("SELECT invoice_id FROM invoices_fts WHERE invoices_fts MATCH :q"),
                            {"q": q},
                        ).all()
                        ids = [row[0] for row in id_rows]
                        if not ids:
                            return []
                        statement = statement.where(InvoiceDB.id.in_(ids))
                    except Exception as e:
                        logger.debug(f"FTS query failed, fallback to LIKE: {e}")
                        statement = statement.where(
                            (InvoiceDB.issuer_name.contains(q)) | (InvoiceDB.recipient_name.contains(q))
                        )
                else:
                    statement = statement.where(
                        (InvoiceDB.issuer_name.contains(q)) | (InvoiceDB.recipient_name.contains(q))
                    )

            # Handle both document_type and invoice_type (alias)
            doc_type = document_type or invoice_type
            if doc_type:
                statement = statement.where(InvoiceDB.document_type == doc_type)
            
            # Operation type filter
            if operation_type:
                statement = statement.where(InvoiceDB.operation_type == operation_type)
            
            # CNPJ contains search
            if issuer_cnpj:
                statement = statement.where(InvoiceDB.issuer_cnpj.contains(issuer_cnpj))
            if recipient_cnpj:
                statement = statement.where(InvoiceDB.recipient_cnpj_cpf.contains(recipient_cnpj))

            # Transport modal filter (exact match)
            if modal:
                statement = statement.where(InvoiceDB.modal == modal)

            # Cost center and confidence filters
            if cost_center:
                statement = statement.where(InvoiceDB.cost_center == cost_center)
            if min_confidence is not None:
                statement = statement.where(InvoiceDB.classification_confidence >= min_confidence)
            
            # Date filters
            if days_back:
                cutoff_date = datetime.now(UTC) - timedelta(days=days_back)
                statement = statement.where(InvoiceDB.issue_date >= cutoff_date)
            if start_date:
                statement = statement.where(InvoiceDB.issue_date >= start_date)
            if end_date:
                statement = statement.where(InvoiceDB.issue_date <= end_date)
            
            # Order by date descending and apply pagination
            statement = (
                statement
                .order_by(InvoiceDB.issue_date.desc())
                .offset(offset)
                .limit(limit)
            )
            
            # Execute query and get all results
            invoices = list(session.exec(statement).all())
            
            # Ensure relationships are loaded before session closes
            for inv in invoices:
                # Access relationships to ensure they're loaded
                _ = inv.items
                _ = inv.issues
            
            return invoices

    def count_invoices(
        self,
        document_type: Optional[str] = None,
        invoice_type: Optional[str] = None,
        operation_type: Optional[str] = None,
        issuer_cnpj: Optional[str] = None,
        recipient_cnpj: Optional[str] = None,
        modal: Optional[str] = None,
        cost_center: Optional[str] = None,
        min_confidence: Optional[float] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days_back: Optional[int] = None,
        q: Optional[str] = None,
    ) -> int:
        """Return total count for given filters (used for pagination)."""
        with Session(self.engine) as session:
            statement = select(func.count()).select_from(InvoiceDB)

            # Handle both document_type and invoice_type (alias)
            doc_type = document_type or invoice_type
            if doc_type:
                statement = statement.where(InvoiceDB.document_type == doc_type)

            if operation_type:
                statement = statement.where(InvoiceDB.operation_type == operation_type)

            if issuer_cnpj:
                statement = statement.where(InvoiceDB.issuer_cnpj.contains(issuer_cnpj))
            if recipient_cnpj:
                statement = statement.where(InvoiceDB.recipient_cnpj_cpf.contains(recipient_cnpj))

            if modal:
                statement = statement.where(InvoiceDB.modal == modal)

            if cost_center:
                statement = statement.where(InvoiceDB.cost_center == cost_center)
            if min_confidence is not None:
                statement = statement.where(InvoiceDB.classification_confidence >= min_confidence)

            if days_back:
                cutoff_date = datetime.now(UTC) - timedelta(days=days_back)
                statement = statement.where(InvoiceDB.issue_date >= cutoff_date)
            if start_date:
                statement = statement.where(InvoiceDB.issue_date >= start_date)
            if end_date:
                statement = statement.where(InvoiceDB.issue_date <= end_date)

            # FTS or LIKE for text search
            if q:
                if self.fts_enabled:
                    try:
                        id_rows = session.exec(
                            text("SELECT invoice_id FROM invoices_fts WHERE invoices_fts MATCH :q"),
                            {"q": q},
                        ).all()
                        ids = [row[0] for row in id_rows]
                        if not ids:
                            return 0
                        statement = statement.where(InvoiceDB.id.in_(ids))
                    except Exception as e:
                        logger.debug(f"FTS count failed, fallback to LIKE: {e}")
                        statement = statement.where(
                            (InvoiceDB.issuer_name.contains(q)) | (InvoiceDB.recipient_name.contains(q))
                        )
                else:
                    statement = statement.where(
                        (InvoiceDB.issuer_name.contains(q)) | (InvoiceDB.recipient_name.contains(q))
                    )

            return session.exec(statement).one()

    def get_statistics(self) -> dict:
        """Get database statistics."""
        with Session(self.engine) as session:
            total_invoices = len(session.exec(select(InvoiceDB)).all())
            total_items = len(session.exec(select(InvoiceItemDB)).all())
            total_issues = len(session.exec(select(ValidationIssueDB)).all())
            
            # Get totals by document type
            invoices = session.exec(select(InvoiceDB)).all()
            by_type = {}
            total_value = Decimal("0")
            
            for inv in invoices:
                by_type[inv.document_type] = by_type.get(inv.document_type, 0) + 1
                total_value += inv.total_invoice
            
            return {
                "total_invoices": total_invoices,
                "total_items": total_items,
                "total_issues": total_issues,
                "by_type": by_type,
                "total_value": float(total_value),
            }

    def delete_invoice(self, document_key: str) -> bool:
        """Delete invoice by document key."""
        with Session(self.engine) as session:
            statement = select(InvoiceDB).where(InvoiceDB.document_key == document_key)
            invoice = session.exec(statement).first()
            
            if invoice:
                session.delete(invoice)
                session.commit()
                logger.info(f"Deleted invoice {document_key}")
                return True
            
            return False

    def get_validation_issues(self, invoice_id: int) -> list[ValidationIssueDB]:
        """Get validation issues for a specific invoice."""
        with Session(self.engine) as session:
            statement = select(ValidationIssueDB).where(
                ValidationIssueDB.invoice_id == invoice_id
            )
            return list(session.exec(statement).all())

    def get_classification_from_cache(self, cache_key: str) -> Optional[dict]:
        """Get classification from cache."""
        with Session(self.engine) as session:
            statement = select(ClassificationCacheDB).where(
                ClassificationCacheDB.cache_key == cache_key
            )
            cache_entry = session.exec(statement).first()
            
            if cache_entry:
                # Update usage stats
                cache_entry.hit_count += 1
                cache_entry.last_used_at = datetime.now(UTC)
                session.add(cache_entry)
                session.commit()
                
                logger.info(f"Cache HIT for key {cache_key[:16]}... (hits: {cache_entry.hit_count})")
                
                return {
                    "operation_type": cache_entry.operation_type,
                    "cost_center": cache_entry.cost_center,
                    "confidence": cache_entry.confidence,
                    "reasoning": cache_entry.reasoning,
                    "used_llm_fallback": cache_entry.used_llm,
                    "from_cache": True,
                }
            
            return None

    def save_classification_to_cache(
        self,
        cache_key: str,
        issuer_cnpj: str,
        ncm: Optional[str],
        cfop: str,
        classification: dict,
    ) -> None:
        """Save classification to cache."""
        with Session(self.engine) as session:
            # Check if already exists
            statement = select(ClassificationCacheDB).where(
                ClassificationCacheDB.cache_key == cache_key
            )
            existing = session.exec(statement).first()
            
            if existing:
                # Update existing entry
                existing.operation_type = classification["operation_type"]
                existing.cost_center = classification["cost_center"]
                existing.confidence = classification["confidence"]
                existing.reasoning = classification.get("reasoning")
                existing.used_llm = classification.get("used_llm_fallback", False)
                existing.last_used_at = datetime.now(UTC)
                session.add(existing)
            else:
                # Create new entry
                cache_entry = ClassificationCacheDB(
                    cache_key=cache_key,
                    issuer_cnpj=issuer_cnpj,
                    ncm=ncm,
                    cfop=cfop,
                    operation_type=classification["operation_type"],
                    cost_center=classification["cost_center"],
                    confidence=classification["confidence"],
                    reasoning=classification.get("reasoning"),
                    used_llm=classification.get("used_llm_fallback", False),
                )
                session.add(cache_entry)
            
            session.commit()
            logger.info(f"Saved classification to cache: {cache_key[:16]}...")

    def get_cache_statistics(self) -> dict:
        """Get cache statistics."""
        with Session(self.engine) as session:
            total_entries = len(session.exec(select(ClassificationCacheDB)).all())
            
            if total_entries == 0:
                return {
                    "total_entries": 0,
                    "total_hits": 0,
                    "avg_hits_per_entry": 0,
                    "cache_effectiveness": 0,
                }
            
            cache_entries = session.exec(select(ClassificationCacheDB)).all()
            total_hits = sum(entry.hit_count for entry in cache_entries)
            
            return {
                "total_entries": total_entries,
                "total_hits": total_hits,
                "avg_hits_per_entry": total_hits / total_entries if total_entries > 0 else 0,
                "cache_effectiveness": (total_hits / (total_entries + total_hits)) * 100 if (total_entries + total_hits) > 0 else 0,
            }

    def update_invoice_classification(
        self,
        document_key: str,
        classification: dict,
    ) -> bool:
        """Update invoice classification fields."""
        with Session(self.engine) as session:
            statement = select(InvoiceDB).where(InvoiceDB.document_key == document_key)
            invoice = session.exec(statement).first()
            
            if invoice:
                invoice.operation_type = classification.get("operation_type")
                invoice.cost_center = classification.get("cost_center")
                invoice.classification_confidence = classification.get("confidence")
                invoice.classification_reasoning = classification.get("reasoning")
                invoice.used_llm_fallback = classification.get("used_llm_fallback", False)
                
                session.add(invoice)
                session.commit()
                logger.info(f"Updated classification for invoice {document_key}")
                return True
            
            return False

    def get_validation_issue_analysis(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        limit: int = 10,
    ) -> dict:
        """
        Analyze validation issues to find the most common problems.
        
        Args:
            year: Filter by year (e.g., 2024)
            month: Filter by month (1-12), requires year to be set
            limit: Maximum number of top issues to return
            
        Returns:
            Dictionary with analysis of common validation issues
        """
        with Session(self.engine) as session:
            # Build query for validation issues
            query = select(
                ValidationIssueDB.code,
                ValidationIssueDB.severity,
            ).join(InvoiceDB)
            
            # Filter by date range if year/month provided
            if year is not None:
                start_date = datetime(year, month or 1, 1, tzinfo=UTC)
                if month is not None:
                    # Last day of the month
                    next_month = datetime(
                        year,
                        month + 1 if month < 12 else 1,
                        1,
                        tzinfo=UTC
                    ) - timedelta(days=1)
                    end_date = next_month.replace(hour=23, minute=59, second=59)
                else:
                    # Entire year
                    end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=UTC)
                
                query = query.where(
                    InvoiceDB.issue_date >= start_date,
                    InvoiceDB.issue_date <= end_date,
                )
            
            issues = session.exec(query).all()
            
            if not issues:
                return {
                    "period": f"{year}/{month}" if month else str(year) if year else "all time",
                    "total_issues": 0,
                    "common_issues": [],
                    "by_severity": {},
                }
            
            # Count issues by code and severity
            issue_counts: dict[str, dict] = {}
            severity_counts: dict[str, int] = {}
            
            for code, severity in issues:
                # Count by issue code
                if code not in issue_counts:
                    issue_counts[code] = {
                        "count": 0,
                        "severity": severity,
                        "severities": {}
                    }
                issue_counts[code]["count"] += 1
                
                # Track severity distribution for this code
                if severity not in issue_counts[code]["severities"]:
                    issue_counts[code]["severities"][severity] = 0
                issue_counts[code]["severities"][severity] += 1
                
                # Count by severity
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            # Sort by frequency
            sorted_issues = sorted(
                issue_counts.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )[:limit]
            
            # Get descriptions for issue codes (from database if available)
            common_issues = []
            for code, data in sorted_issues:
                # Try to get a sample message
                sample_query = (
                    select(ValidationIssueDB.message, ValidationIssueDB.field)
                    .where(ValidationIssueDB.code == code)
                    .limit(1)
                )
                sample = session.exec(sample_query).first()
                
                common_issues.append({
                    "code": code,
                    "count": data["count"],
                    "severity": data["severity"],
                    "severity_breakdown": data["severities"],
                    "sample_message": sample[0] if sample else None,
                    "field": sample[1] if sample else None,
                })
            
            period_str = f"{year}/{month:02d}" if month else str(year) if year else "all time"
            
            return {
                "period": period_str,
                "total_issues": len(issues),
                "common_issues": common_issues,
                "by_severity": severity_counts,
            }

    def get_validation_issues_by_issuer(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        limit: int = 20,
    ) -> dict:
        """
        Analyze validation issues grouped by issuer/emitente.
        
        Args:
            year: Filter by year (e.g., 2024)
            month: Filter by month (1-12), requires year
            limit: Maximum number of issuers to return
            
        Returns:
            Dictionary with analysis per issuer
        """
        with Session(self.engine) as session:
            # Build base query
            query = (
                select(
                    InvoiceDB.issuer_cnpj,
                    InvoiceDB.issuer_name,
                    InvoiceDB.id.label("invoice_id"),
                    ValidationIssueDB.code,
                    ValidationIssueDB.severity,
                )
                .outerjoin(ValidationIssueDB)
            )
            
            # Filter by date range if specified
            if year is not None:
                start_date = datetime(year, month or 1, 1, tzinfo=UTC)
                if month is not None:
                    next_month = datetime(
                        year,
                        month + 1 if month < 12 else 1,
                        1,
                        tzinfo=UTC
                    )
                    end_date = next_month - timedelta(days=1)
                else:
                    end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=UTC)
                
                query = query.where(
                    InvoiceDB.issue_date >= start_date,
                    InvoiceDB.issue_date <= end_date,
                )
            
            results = session.exec(query).all()
            
            if not results:
                return {}
            
            # Aggregate by issuer
            issuer_data = {}
            
            for cnpj, name, invoice_id, code, severity in results:
                if cnpj not in issuer_data:
                    issuer_data[cnpj] = {
                        "name": name,
                        "invoices": set(),
                        "errors": 0,
                        "warnings": 0,
                        "issues": {}
                    }
                
                if invoice_id:
                    issuer_data[cnpj]["invoices"].add(invoice_id)
                
                if code:
                    if severity == "error":
                        issuer_data[cnpj]["errors"] += 1
                    elif severity == "warning":
                        issuer_data[cnpj]["warnings"] += 1
                    
                    if code not in issuer_data[cnpj]["issues"]:
                        issuer_data[cnpj]["issues"][code] = 0
                    issuer_data[cnpj]["issues"][code] += 1
            
            # Convert to list and sort by error rate
            issuer_list = []
            for cnpj, data in issuer_data.items():
                invoice_count = len(data["invoices"])
                total_issues = data["errors"] + data["warnings"]
                error_rate = (data["errors"] / invoice_count * 100) if invoice_count > 0 else 0
                
                top_issues = sorted(
                    data["issues"].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                
                issuer_list.append({
                    "cnpj": cnpj,
                    "name": data["name"],
                    "document_count": invoice_count,
                    "error_count": data["errors"],
                    "warning_count": data["warnings"],
                    "total_issues": total_issues,
                    "error_rate": round(error_rate, 2),
                    "top_issues": [{"code": code, "count": cnt} for code, cnt in top_issues],
                })
            
            # Sort by error rate descending
            issuer_list.sort(key=lambda x: x["error_rate"], reverse=True)
            
            return {
                "period": f"{year}/{month:02d}" if month else str(year) if year else "all time",
                "total_issuers": len(issuer_list),
                "issuers": issuer_list[:limit]
            }

    def get_validation_issues_by_operation(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
    ) -> dict:
        """
        Compare validation issues across different operation types.
        
        Args:
            year: Filter by year
            month: Filter by month
            
        Returns:
            Dictionary with analysis by operation type
        """
        with Session(self.engine) as session:
            query = select(
                InvoiceDB.operation_type,
                InvoiceDB.id.label("invoice_id"),
                ValidationIssueDB.code,
                ValidationIssueDB.severity,
            ).outerjoin(ValidationIssueDB)
            
            # Filter by date
            if year is not None:
                start_date = datetime(year, month or 1, 1, tzinfo=UTC)
                if month is not None:
                    next_month = datetime(year, month + 1 if month < 12 else 1, 1, tzinfo=UTC)
                    end_date = next_month - timedelta(days=1)
                else:
                    end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=UTC)
                
                query = query.where(
                    InvoiceDB.issue_date >= start_date,
                    InvoiceDB.issue_date <= end_date,
                )
            
            results = session.exec(query).all()
            
            # Aggregate by operation
            op_data = {}
            
            for operation, invoice_id, code, severity in results:
                op_type = operation or "unclassified"
                
                if op_type not in op_data:
                    op_data[op_type] = {
                        "invoices": set(),
                        "errors": 0,
                        "warnings": 0,
                    }
                
                if invoice_id:
                    op_data[op_type]["invoices"].add(invoice_id)
                
                if code:
                    if severity == "error":
                        op_data[op_type]["errors"] += 1
                    elif severity == "warning":
                        op_data[op_type]["warnings"] += 1
            
            # Format response
            result = {}
            for op_type, data in op_data.items():
                count = len(data["invoices"])
                total_issues = data["errors"] + data["warnings"]
                result[op_type] = {
                    "document_count": count,
                    "error_count": data["errors"],
                    "warning_count": data["warnings"],
                    "total_issues": total_issues,
                    "avg_issues_per_doc": round(total_issues / count, 2) if count > 0 else 0,
                    "error_rate": round((data["errors"] / count * 100), 2) if count > 0 else 0,
                }
            
            return {
                "period": f"{year}/{month:02d}" if month else str(year) if year else "all time",
                "by_operation": result
            }

    def calculate_data_quality_score(
        self,
        year: Optional[int] = None,
    ) -> dict:
        """
        Calculate overall data quality metrics (0-100 scale).
        
        Args:
            year: Filter by year, if None uses all data
            
        Returns:
            Dictionary with quality metrics
        """
        with Session(self.engine) as session:
            # Base query
            query = select(
                InvoiceDB.id,
                InvoiceDB.issue_date,
            )
            
            if year:
                start_date = datetime(year, 1, 1, tzinfo=UTC)
                end_date = datetime(year, 12, 31, 23, 59, 59, tzinfo=UTC)
                query = query.where(
                    InvoiceDB.issue_date >= start_date,
                    InvoiceDB.issue_date <= end_date,
                )
            
            invoices = session.exec(query).all()
            
            if not invoices:
                return {
                    "overall_score": 0,
                    "documents_analyzed": 0,
                    "metrics": {}
                }
            
            invoice_ids = [inv[0] for inv in invoices]
            
            # Count issues
            issues_query = select(
                func.count().label("total"),
                func.sum(case((ValidationIssueDB.severity == "error", 1), else_=0)).label("errors"),
                func.sum(case((ValidationIssueDB.severity == "warning", 1), else_=0)).label("warnings"),
            ).where(ValidationIssueDB.invoice_id.in_(invoice_ids))
            
            total_issues, error_count, warning_count = session.exec(issues_query).one()
            
            total_issues = total_issues or 0
            error_count = error_count or 0
            warning_count = warning_count or 0
            
            doc_count = len(invoice_ids)
            
            # Calculate metrics
            docs_with_errors = min(doc_count, len(set(
                session.exec(
                    select(ValidationIssueDB.invoice_id).where(
                        (ValidationIssueDB.invoice_id.in_(invoice_ids)) &
                        (ValidationIssueDB.severity == "error")
                    ).distinct()
                ).all()
            )))
            
            docs_with_warnings = min(doc_count, len(set(
                session.exec(
                    select(ValidationIssueDB.invoice_id).where(
                        (ValidationIssueDB.invoice_id.in_(invoice_ids)) &
                        (ValidationIssueDB.severity == "warning")
                    ).distinct()
                ).all()
            )))
            
            # Score calculation
            completeness = 100  # All docs present
            accuracy = max(0, 100 - (error_count / max(1, doc_count) * 50))
            consistency = max(0, 100 - (warning_count / max(1, doc_count) * 30))
            
            overall_score = (completeness + accuracy + consistency) / 3
            
            return {
                "overall_score": round(overall_score, 1),
                "documents_analyzed": doc_count,
                "documents_with_errors": docs_with_errors,
                "documents_with_warnings": docs_with_warnings,
                "documents_clean": doc_count - docs_with_errors - docs_with_warnings,
                "total_issues": total_issues,
                "error_count": error_count,
                "warning_count": warning_count,
                "metrics": {
                    "completeness": round(completeness, 1),
                    "accuracy": round(accuracy, 1),
                    "consistency": round(consistency, 1),
                },
                "error_rate": round((error_count / doc_count * 100), 2) if doc_count > 0 else 0,
                "warning_rate": round((warning_count / doc_count * 100), 2) if doc_count > 0 else 0,
            }

    def get_remediation_suggestions(self, year: Optional[int] = None, month: Optional[int] = None, limit: int = 10) -> dict:  # pragma: no cover
        """
        Get remediation suggestions for most common validation issues.
        
        Maps error codes to recommended actions and provides a prioritized list
        of fixes based on frequency and impact.
        
        Args:
            year: Optional filter by year
            month: Optional filter by month
            limit: Max number of suggestions to return (default 10)
            
        Returns:
            Dictionary with suggestions sorted by impact (frequency * severity weight)
        """
        try:
            with Session(self.engine) as session:
                # Get all validation issues with filters
                query = select(ValidationIssueDB).join(InvoiceDB)
                
                if year is not None:
                    start_date = datetime(year, month or 1, 1)
                    if month is not None:
                        next_month = datetime(
                            year,
                            month + 1 if month < 12 else 1,
                            1,
                        ) - timedelta(days=1)
                        end_date = next_month.replace(hour=23, minute=59, second=59)
                    else:
                        end_date = datetime(year, 12, 31, 23, 59, 59)
                    
                    query = query.where(
                        (InvoiceDB.issue_date >= start_date) & (InvoiceDB.issue_date <= end_date)
                    )
                
                issues_db = session.exec(query).all()
                
                # Aggregate by code/severity/message
                issue_counts: dict = {}
                for issue in issues_db:
                    key = (issue.code, issue.severity, issue.message)
                    issue_counts[key] = issue_counts.get(key, 0) + 1
                
                # Sort by frequency
                sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
                issues = [(code, severity, msg, count) for (code, severity, msg), count in sorted_issues]
            
            # Map error codes to remediation actions
            REMEDIATION_MAP = {
                # Tax issues
                "INVALID_TAX_RATE": {
                    "action": "Verify tax calculation",
                    "steps": ["Check ICMS/IPI/PIS rates", "Validate against state and federal rules", "Review CST code"],
                    "priority": "high"
                },
                "TAX_MISMATCH": {
                    "action": "Reconcile declared vs calculated taxes",
                    "steps": ["Recalculate taxes from items", "Check rounding rules", "Verify tax base"],
                    "priority": "high"
                },
                "TOTAL_MISMATCH": {
                    "action": "Reconcile invoice totals",
                    "steps": ["Sum all item values", "Add taxes correctly", "Check for deductions"],
                    "priority": "critical"
                },
                # Classification issues
                "INVALID_CFOP": {
                    "action": "Correct CFOP code",
                    "steps": ["Verify operation type", "Check CFOP validity for state", "Review fiscal situation"],
                    "priority": "high"
                },
                "INVALID_OPERATION_TYPE": {
                    "action": "Set correct operation type",
                    "steps": ["Identify if purchase/sale/transfer", "Classify correctly in system"],
                    "priority": "high"
                },
                # Item/product issues
                "INVALID_NCM": {
                    "action": "Validate NCM code",
                    "steps": ["Check NCM format (8 digits)", "Verify product classification", "Update product catalog"],
                    "priority": "medium"
                },
                "MISSING_ITEM_DATA": {
                    "action": "Complete item information",
                    "steps": ["Add product code", "Include quantity/unit", "Provide unit price"],
                    "priority": "high"
                },
                # CNPJ/document issues
                "INVALID_CNPJ": {
                    "action": "Fix CNPJ format",
                    "steps": ["Validate CNPJ syntax", "Check digit verification", "Update company data"],
                    "priority": "critical"
                },
                "INVALID_IE": {
                    "action": "Fix State Registration",
                    "steps": ["Verify IE format", "Check state rules", "Update company data"],
                    "priority": "medium"
                },
                # Quantity/value issues
                "QUANTITY_UNIT_MISMATCH": {
                    "action": "Fix quantity and unit",
                    "steps": ["Verify item quantity", "Check unit of measure", "Recalculate total"],
                    "priority": "medium"
                },
                "VALUE_PRECISION_ERROR": {
                    "action": "Fix value precision",
                    "steps": ["Use correct decimal places", "Apply rounding rules", "Recalculate totals"],
                    "priority": "medium"
                },
            }
            
            suggestions = []
            for code, severity, message, frequency in issues:
                # Calculate impact score (frequency * severity weight)
                severity_weight = {"error": 3, "warning": 1}.get(severity, 1)
                impact = frequency * severity_weight
                
                # Get remediation or use generic
                remedy = REMEDIATION_MAP.get(code, {
                    "action": f"Investigate {code}",
                    "steps": ["Review error message", "Consult documentation", "Contact support if needed"],
                    "priority": "low"
                })
                
                suggestions.append({
                    "code": code,
                    "frequency": frequency,
                    "severity": severity,
                    "impact_score": impact,
                    "sample_message": message,
                    "remediation": {
                        "action": remedy["action"],
                        "steps": remedy["steps"],
                        "priority": remedy["priority"]
                    }
                })
            
            # Sort by impact
            suggestions.sort(key=lambda x: x["impact_score"], reverse=True)
            
            period = f"{year}-{month:02d}" if year and month else f"{year}" if year else "all time"
            
            return {
                "period": period,
                "total_suggestions": len(suggestions),
                "suggestions": suggestions
            }
            
        except Exception as e:
            logger.error(f"Error generating remediation suggestions: {e}")
            return {"period": "unknown", "total_suggestions": 0, "suggestions": [], "error": str(e)}

    def analyze_trends(self, months_back: int = 12) -> dict:  # pragma: no cover
        """
        Analyze validation issue trends over time.
        
        Shows monthly aggregation of errors/warnings and trend direction
        (increasing/decreasing/stable).
        
        Args:
            months_back: Number of months to analyze (default 12)
            
        Returns:
            Dictionary with monthly trends and aggregate statistics
        """
        try:
            # Calculate start date (no timezone issues)
            end_date = datetime.now()
            start_date = end_date - timedelta(days=30 * months_back)
            
            with Session(self.engine) as session:
                # Get invoices in the period with their validation issues
                query = select(InvoiceDB).where(InvoiceDB.issue_date >= start_date)
                invoices = session.exec(query).all()
                
                # Aggregate by month
                monthly_data: dict = {}
                
                for invoice in invoices:
                    year = invoice.issue_date.year
                    month = invoice.issue_date.month
                    period_key = f"{year}-{month:02d}"
                    
                    if period_key not in monthly_data:
                        monthly_data[period_key] = {
                            "year": year,
                            "month": month,
                            "document_count": 0,
                            "error_count": 0,
                            "warning_count": 0,
                        }
                    
                    monthly_data[period_key]["document_count"] += 1
                    
                    # Count issues for this invoice
                    issue_query = select(ValidationIssueDB).where(
                        ValidationIssueDB.invoice_id == invoice.id
                    )
                    issues = session.exec(issue_query).all()
                    
                    for issue in issues:
                        if issue.severity == "error":
                            monthly_data[period_key]["error_count"] += 1
                        elif issue.severity == "warning":
                            monthly_data[period_key]["warning_count"] += 1
                
                # Convert to list and sort
                trends = []
                for period_key in sorted(monthly_data.keys()):
                    data = monthly_data[period_key]
                    doc_count = data["document_count"]
                    if doc_count == 0:
                        continue
                    
                    error_rate = (data["error_count"] / doc_count * 100) if doc_count > 0 else 0
                    warning_rate = (data["warning_count"] / doc_count * 100) if doc_count > 0 else 0
                    
                    trends.append({
                        "period": period_key,
                        "documents": doc_count,
                        "errors": data["error_count"],
                        "warnings": data["warning_count"],
                        "error_rate": round(error_rate, 2),
                        "warning_rate": round(warning_rate, 2),
                        "total_issues": data["error_count"] + data["warning_count"]
                    })
            
            # Analyze trend direction
            if len(trends) >= 2:
                # Compare first and last
                first_error_rate = trends[0]["error_rate"]
                last_error_rate = trends[-1]["error_rate"]
                
                if last_error_rate > first_error_rate * 1.1:  # 10% increase
                    trend_direction = "📈 INCREASING (Quality Degrading)"
                elif last_error_rate < first_error_rate * 0.9:  # 10% decrease
                    trend_direction = "📉 DECREASING (Quality Improving)"
                else:
                    trend_direction = "➡️ STABLE"
                
                # Calculate average rate for the period
                avg_error_rate = sum(t["error_rate"] for t in trends) / len(trends)
            else:
                trend_direction = "📊 INSUFFICIENT DATA"
                avg_error_rate = trends[0]["error_rate"] if trends else 0
            
            return {
                "months_analyzed": months_back,
                "data_points": len(trends),
                "trend_direction": trend_direction,
                "average_error_rate": round(avg_error_rate, 2),
                "first_period": trends[0]["period"] if trends else None,
                "last_period": trends[-1]["period"] if trends else None,
                "monthly_data": trends
            }
            
        except Exception as e:
            logger.error(f"Error analyzing trends: {e}")
            return {"months_analyzed": months_back, "data_points": 0, "monthly_data": [], "error": str(e)}

