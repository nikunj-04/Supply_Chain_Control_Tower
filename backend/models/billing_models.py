"""Database models for Billing System."""
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Invoice(Base):
    """Customer invoices."""
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(String(50), nullable=False, unique=True, index=True)
    customer_id = Column(String(50), nullable=False, index=True)
    customer_name = Column(String(200), nullable=False)
    order_id = Column(String(50), nullable=False)
    invoice_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    due_date = Column(DateTime, nullable=False)
    payment_date = Column(DateTime)
    status = Column(String(30), nullable=False)  # pending, paid, overdue, disputed
    subtotal = Column(Float, nullable=False)
    tax = Column(Float, nullable=False)
    total = Column(Float, nullable=False)
    amount_paid = Column(Float, nullable=False, default=0.0)
    balance = Column(Float, nullable=False)


class BillingLineItem(Base):
    """Invoice line items."""
    __tablename__ = "billing_line_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id = Column(String(50), nullable=False, index=True)
    service_type = Column(String(100), nullable=False)  # storage, picking, packing, shipping, handling
    description = Column(String(500), nullable=False)
    quantity = Column(Float, nullable=False)
    unit_price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)


class BillingMetrics(Base):
    """Billing and revenue metrics."""
    __tablename__ = "billing_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    total_invoices = Column(Integer, nullable=False, default=0)
    invoices_paid = Column(Integer, nullable=False, default=0)
    invoices_overdue = Column(Integer, nullable=False, default=0)
    total_revenue = Column(Float, nullable=False, default=0.0)
    revenue_collected = Column(Float, nullable=False, default=0.0)
    outstanding_balance = Column(Float, nullable=False, default=0.0)
    collection_rate_pct = Column(Float, nullable=False, default=96.0)


def get_billing_engine(db_path: str):
    """Create and return Billing database engine."""
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_billing_db(db_path: str):
    """Initialize Billing database schema."""
    engine = get_billing_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_billing_session(db_path: str):
    """Get Billing database session."""
    engine = get_billing_engine(db_path)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
