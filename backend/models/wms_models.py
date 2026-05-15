"""Database models for WMS (Warehouse Management System)."""
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Inventory(Base):
    """Inventory levels and locations."""
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sku = Column(String(50), nullable=False, index=True)
    product_name = Column(String(200), nullable=False)
    warehouse_location = Column(String(50), nullable=False)
    quantity_on_hand = Column(Integer, nullable=False)
    quantity_reserved = Column(Integer, nullable=False, default=0)
    quantity_available = Column(Integer, nullable=False)
    reorder_point = Column(Integer, nullable=False, default=100)
    last_updated = Column(DateTime, nullable=False, default=datetime.utcnow)


class PickingTask(Base):
    """Warehouse picking tasks."""
    __tablename__ = "picking_tasks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(String(50), nullable=False, index=True)
    sku = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    location = Column(String(50), nullable=False)
    status = Column(String(20), nullable=False)  # pending, in_progress, completed, delayed
    assigned_to = Column(String(100))
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime)
    priority = Column(String(20), nullable=False, default="normal")  # low, normal, high, urgent


class WarehouseMetrics(Base):
    """Warehouse operational metrics."""
    __tablename__ = "warehouse_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    total_picks = Column(Integer, nullable=False, default=0)
    picks_completed = Column(Integer, nullable=False, default=0)
    picks_delayed = Column(Integer, nullable=False, default=0)
    avg_pick_time_minutes = Column(Float, nullable=False, default=0.0)
    inventory_accuracy_pct = Column(Float, nullable=False, default=99.0)
    capacity_utilization_pct = Column(Float, nullable=False, default=75.0)


def get_wms_engine(db_path: str):
    """Create and return WMS database engine."""
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_wms_db(db_path: str):
    """Initialize WMS database schema."""
    engine = get_wms_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_wms_session(db_path: str):
    """Get WMS database session."""
    engine = get_wms_engine(db_path)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
