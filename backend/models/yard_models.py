"""Database models for Yard/Dock Management System."""
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class DockAppointment(Base):
    """Dock door appointments."""
    __tablename__ = "dock_appointments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(String(50), nullable=False, unique=True, index=True)
    dock_door = Column(String(20), nullable=False)
    appointment_type = Column(String(30), nullable=False)  # inbound, outbound
    carrier = Column(String(100), nullable=False)
    trailer_number = Column(String(50))
    status = Column(String(30), nullable=False)  # scheduled, checked_in, loading, unloading, completed, missed
    scheduled_time = Column(DateTime, nullable=False)
    actual_arrival = Column(DateTime)
    actual_start = Column(DateTime)
    actual_completion = Column(DateTime)
    expected_duration_minutes = Column(Integer, nullable=False)
    actual_duration_minutes = Column(Integer)


class YardLocation(Base):
    """Trailer yard locations."""
    __tablename__ = "yard_locations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    location_id = Column(String(20), nullable=False, unique=True, index=True)
    zone = Column(String(20), nullable=False)  # A, B, C, D
    status = Column(String(30), nullable=False)  # occupied, available, reserved, maintenance
    trailer_number = Column(String(50))
    carrier = Column(String(100))
    check_in_time = Column(DateTime)
    expected_departure = Column(DateTime)
    contents = Column(String(200))  # inbound_freight, outbound_freight, empty, maintenance


class YardMetrics(Base):
    """Yard and dock operational metrics."""
    __tablename__ = "yard_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, nullable=False, index=True)
    total_appointments = Column(Integer, nullable=False, default=0)
    appointments_completed = Column(Integer, nullable=False, default=0)
    appointments_missed = Column(Integer, nullable=False, default=0)
    on_time_arrival_pct = Column(Float, nullable=False, default=88.0)
    avg_dock_time_minutes = Column(Float, nullable=False, default=45.0)
    yard_capacity = Column(Integer, nullable=False, default=50)
    yard_occupied = Column(Integer, nullable=False, default=35)
    yard_utilization_pct = Column(Float, nullable=False, default=70.0)


def get_yard_engine(db_path: str):
    """Create and return Yard database engine."""
    return create_engine(f"sqlite:///{db_path}", echo=False)


def init_yard_db(db_path: str):
    """Initialize Yard database schema."""
    engine = get_yard_engine(db_path)
    Base.metadata.create_all(engine)
    return engine


def get_yard_session(db_path: str):
    """Get Yard database session."""
    engine = get_yard_engine(db_path)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
