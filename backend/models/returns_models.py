"""Database models for Returns Management System."""
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Return(Base):
    """Product returns."""
    __tablename__ = "returns"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    return_id = Column(String(50), nullable=False, unique=True, index=True)
    order_id = Column(String(50), nullable=False, index=True)
    customer_id = Column(String(50), nullable=False)
    customer_name = Column(String(200), nullable=False)
    status = Column(String(30), nullable=False)  # initiated, in_transit, received, inspected, processed, refunded
    reason = Column(String(100), nullable=False)  # damaged, wrong_item, defective, not_needed, size_issue
    return_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    received_date = Column(DateTime)
    processed_date = Column(DateTime)
    total_value = Column(Float, nullable=False)
    refund_amount = Column(Float, nullable=False)
    refund_status = Column(String(30), nullable=False)  # pending, approved, refunded


class ReturnLineItem(Base):
    """Return line items."""
    __tablename__ = "return_line_items"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    return_id = Column(String(50), nullable=False, index=True)
    sku = Column(String(50), nullable=False)
    product_name = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False)
    condition = Column(String(50), nullable=False)  # resaleable, damaged, defective
    restocking_fee = Column(Float, nullable=False, default=0.0)


class ReturnMetrics(Base):
    """Returns processing metrics."""
    __tablename__ = "return_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    total_returns = Column(Integer, nullable=False, default=0)
    returns_processed = Column(Integer, nullable=False, default=0)
    returns_pending = Column(Integer, nullable=False, default=0)
    return_rate_pct = Column(Float, nullable=False, default=5.0)
    avg_processing_time_days = Column(Float, nullable=False, default=3.5)
    total_refund_amount = Column(Float, nullable=False, default=0.0)
    resaleable_rate_pct = Column(Float, nullable=False, default=70.0)


def get_returns_engine(db_path: str):
    """Create and return Returns database engine."""
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_returns_db(db_path: str):
    """Initialize Returns database schema."""
    engine = get_returns_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_returns_session(db_path: str):
    """Get Returns database session."""
    engine = get_returns_engine(db_path)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
