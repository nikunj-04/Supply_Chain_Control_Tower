"""Database models for Real-Time Shipment Tracking."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class ShipmentLocation(Base):
    """Real-time and historical shipment location tracking."""
    __tablename__ = "shipment_locations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    shipment_id = Column(String(50), nullable=False, index=True)
    
    # Location data
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_name = Column(String(200))  # City, State or landmark
    
    # Progress tracking
    distance_traveled_miles = Column(Float, nullable=False, default=0.0)
    distance_remaining_miles = Column(Float, nullable=False)
    progress_percentage = Column(Float, nullable=False, default=0.0)
    
    # Status
    status = Column(String(30), nullable=False)  # scheduled, picked_up, in_transit, at_hub, out_for_delivery, delivered, delayed
    
    # Timing
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    estimated_arrival = Column(DateTime, nullable=False)
    
    # Additional context
    speed_mph = Column(Float)  # Current speed if moving
    heading = Column(String(20))  # N, NE, E, SE, S, SW, W, NW
    is_delayed = Column(Boolean, default=False)
    delay_reason = Column(String(200))


class TrackingEvent(Base):
    """Milestone events in shipment journey."""
    __tablename__ = "tracking_events"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    shipment_id = Column(String(50), nullable=False, index=True)
    
    # Event details
    event_type = Column(String(50), nullable=False)  # pickup, departure, arrival, scan, delivery_attempt, delivered, exception
    event_code = Column(String(20))  # Standard event codes
    
    # Location
    location = Column(String(200), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    facility_type = Column(String(50))  # warehouse, hub, distribution_center, customer
    
    # Description
    description = Column(Text, nullable=False)
    notes = Column(Text)
    
    # Timing
    occurred_at = Column(DateTime, nullable=False)
    recorded_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    
    # Scan details
    scanned_by = Column(String(100))
    device_id = Column(String(50))


class RouteSegment(Base):
    """Planned route segments for shipments."""
    __tablename__ = "route_segments"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    shipment_id = Column(String(50), nullable=False, index=True)
    
    # Segment info
    segment_number = Column(Integer, nullable=False)
    from_location = Column(String(200), nullable=False)
    to_location = Column(String(200), nullable=False)
    
    # Coordinates
    from_latitude = Column(Float, nullable=False)
    from_longitude = Column(Float, nullable=False)
    to_latitude = Column(Float, nullable=False)
    to_longitude = Column(Float, nullable=False)
    
    # Segment details
    distance_miles = Column(Float, nullable=False)
    estimated_duration_hours = Column(Float, nullable=False)
    mode = Column(String(30), nullable=False)  # truck, rail, air, ocean
    carrier = Column(String(100))
    
    # Status
    status = Column(String(30), nullable=False, default='planned')  # planned, in_progress, completed
    started_at = Column(DateTime)
    completed_at = Column(DateTime)


class ETAUpdate(Base):
    """Historical ETA updates for shipments."""
    __tablename__ = "eta_updates"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    shipment_id = Column(String(50), nullable=False, index=True)
    
    # ETA information
    previous_eta = Column(DateTime)
    new_eta = Column(DateTime, nullable=False)
    change_hours = Column(Float)  # Positive for delay, negative for early
    
    # Reason for change
    reason = Column(String(200))
    confidence_level = Column(String(20))  # high, medium, low
    
    # Context
    current_location = Column(String(200))
    distance_remaining_miles = Column(Float)
    
    # Timing
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_by = Column(String(100), default='system')


# Database setup
engine = create_engine('sqlite:///data/tracking.db', echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)


def get_tracking_session(db_path: str = 'data/tracking.db'):
    """Get tracking database session."""
    engine = create_engine(f"sqlite:///{db_path}", echo=False)
    Base.metadata.create_all(engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()
