"""Database models and operations using SQLModel and SQLite."""

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import create_engine
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
        self._create_tables()
        logger.info(f"Database initialized: {database_url}")

    def _create_tables(self) -> None:
        """Create all tables if they don't exist."""
        SQLModel.metadata.create_all(self.engine)

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
            
            return invoice_db

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
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        days_back: Optional[int] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[InvoiceDB]:
        """
        Search invoices with filters.

        Args:
            document_type: Filter by document type (NFe, NFCe, etc.)
            invoice_type: Alias for document_type
            operation_type: Filter by operation type (purchase, sale, transfer, return)
            issuer_cnpj: Filter by issuer CNPJ (contains search)
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
