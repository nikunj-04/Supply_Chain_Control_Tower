"""Database models for TMS (Transportation Management System)."""
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Shipment(Base):
    """Shipment tracking."""
    __tablename__ = "shipments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    shipment_id = Column(String(50), nullable=False, unique=True, index=True)
    order_id = Column(String(50), nullable=False, index=True)
    carrier = Column(String(100), nullable=False)
    tracking_number = Column(String(100), nullable=False)
    status = Column(String(30), nullable=False)  # scheduled, in_transit, delivered, delayed, exception
    origin = Column(String(200), nullable=False)
    destination = Column(String(200), nullable=False)
    scheduled_pickup = Column(DateTime, nullable=False)
    actual_pickup = Column(DateTime)
    estimated_delivery = Column(DateTime, nullable=False)
    actual_delivery = Column(DateTime)
    weight_lbs = Column(Float, nullable=False)
    cost = Column(Float, nullable=False)


class Route(Base):
    """Delivery routes."""
    __tablename__ = "routes"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    route_id = Column(String(50), nullable=False, unique=True, index=True)
    driver = Column(String(100), nullable=False)
    vehicle = Column(String(50), nullable=False)
    status = Column(String(30), nullable=False)  # planned, active, completed
    scheduled_start = Column(DateTime, nullable=False)
    actual_start = Column(DateTime)
    scheduled_end = Column(DateTime, nullable=False)
    actual_end = Column(DateTime)
    total_stops = Column(Integer, nullable=False)
    completed_stops = Column(Integer, nullable=False, default=0)
    total_distance_miles = Column(Float, nullable=False)


class TransportMetrics(Base):
    """Transportation metrics."""
    __tablename__ = "transport_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    total_shipments = Column(Integer, nullable=False, default=0)
    on_time_deliveries = Column(Integer, nullable=False, default=0)
    delayed_shipments = Column(Integer, nullable=False, default=0)
    on_time_delivery_pct = Column(Float, nullable=False, default=92.0)
    avg_transit_time_hours = Column(Float, nullable=False, default=48.0)
    total_transport_cost = Column(Float, nullable=False, default=0.0)
    cost_per_shipment = Column(Float, nullable=False, default=0.0)


def get_tms_engine(db_path: str):
    """Create and return TMS database engine."""
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_tms_db(db_path: str):
    """Initialize TMS database schema."""
    engine = get_tms_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_tms_session(db_path: str):
    """Get TMS database session."""
    engine = get_tms_engine(db_path)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
