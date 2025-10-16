"""Database models and operations using SQLModel and SQLite."""

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import create_engine
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

    def save_invoice(self, invoice_model, validation_issues: List) -> InvoiceDB:
        """
        Save invoice and related data to database.

        Args:
            invoice_model: InvoiceModel from Pydantic
            validation_issues: List of ValidationIssue objects

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
                raw_xml=invoice_model.raw_xml,
                parsed_at=invoice_model.parsed_at,
            )
            
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
            
            return invoice_db

    def get_invoice_by_key(self, document_key: str) -> Optional[InvoiceDB]:
        """Get invoice by document key."""
        with Session(self.engine) as session:
            statement = select(InvoiceDB).where(InvoiceDB.document_key == document_key)
            return session.exec(statement).first()

    def get_all_invoices(self, limit: int = 100, offset: int = 0) -> List[InvoiceDB]:
        """Get all invoices with pagination."""
        with Session(self.engine) as session:
            statement = select(InvoiceDB).order_by(InvoiceDB.issue_date.desc()).limit(limit).offset(offset)
            return list(session.exec(statement).all())

    def search_invoices(
        self,
        document_type: Optional[str] = None,
        issuer_cnpj: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100,
    ) -> List[InvoiceDB]:
        """
        Search invoices with filters.

        Args:
            document_type: Filter by document type (NFe, NFCe, etc.)
            issuer_cnpj: Filter by issuer CNPJ
            start_date: Filter by issue date >= start_date
            end_date: Filter by issue date <= end_date
            limit: Maximum results

        Returns:
            List of matching invoices
        """
        with Session(self.engine) as session:
            statement = select(InvoiceDB)
            
            if document_type:
                statement = statement.where(InvoiceDB.document_type == document_type)
            if issuer_cnpj:
                statement = statement.where(InvoiceDB.issuer_cnpj == issuer_cnpj)
            if start_date:
                statement = statement.where(InvoiceDB.issue_date >= start_date)
            if end_date:
                statement = statement.where(InvoiceDB.issue_date <= end_date)
            
            statement = statement.order_by(InvoiceDB.issue_date.desc()).limit(limit)
            return list(session.exec(statement).all())

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
