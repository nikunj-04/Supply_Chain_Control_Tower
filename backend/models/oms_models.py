"""Database models for OMS (Order Management System)."""
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Order(Base):
    """Customer orders."""
    __tablename__ = "orders"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), nullable=False, unique=True, index=True)
    customer_id = Column(String(50), nullable=False)
    customer_name = Column(String(200), nullable=False)
    status = Column(String(30), nullable=False)  # pending, processing, shipped, delivered, cancelled
    order_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    promised_delivery_date = Column(DateTime, nullable=False)
    actual_delivery_date = Column(DateTime)
    total_items = Column(Integer, nullable=False)
    total_value = Column(Float, nullable=False)
    priority = Column(String(20), nullable=False, default="normal")
    shipping_address = Column(String(500), nullable=False)


class OrderLine(Base):
    """Order line items."""
    __tablename__ = "order_lines"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), nullable=False, index=True)
    sku = Column(String(50), nullable=False)
    product_name = Column(String(200), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    line_total = Column(Float, nullable=False)


class OrderMetrics(Base):
    """Order processing metrics."""
    __tablename__ = "order_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    total_orders = Column(Integer, nullable=False, default=0)
    orders_shipped = Column(Integer, nullable=False, default=0)
    orders_delivered = Column(Integer, nullable=False, default=0)
    orders_delayed = Column(Integer, nullable=False, default=0)
    on_time_delivery_pct = Column(Float, nullable=False, default=95.0)
    avg_processing_time_hours = Column(Float, nullable=False, default=24.0)
    order_accuracy_pct = Column(Float, nullable=False, default=98.5)


def get_oms_engine(db_path: str):
    """Create and return OMS database engine."""
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_oms_db(db_path: str):
    """Initialize OMS database schema."""
    engine = get_oms_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_oms_session(db_path: str):
    """Get OMS database session."""
    engine = get_oms_engine(db_path)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
