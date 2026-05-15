"""Database models for Exception Management."""
from sqlalchemy import Column, Integer, String, Float, DateTime, Text, Boolean, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Exception(Base):
    """Supply chain exceptions and alerts."""
    __tablename__ = "exceptions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    exception_id = Column(String(50), nullable=False, unique=True, index=True)
    exception_type = Column(String(50), nullable=False, index=True)  # delay, inventory, quality, billing, capacity
    severity = Column(String(20), nullable=False, index=True)  # critical, warning, info
    status = Column(String(30), nullable=False, default='open')  # open, in_progress, resolved, dismissed
    
    # Reference to source system and entity
    source_system = Column(String(30), nullable=False)  # TMS, WMS, OMS, Billing, Returns
    entity_type = Column(String(50), nullable=False)  # shipment, order, inventory, invoice
    entity_id = Column(String(50), nullable=False, index=True)
    
    # Exception details
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    impact = Column(String(100))  # business impact description
    
    # Associated data
    customer = Column(String(100))
    location = Column(String(100))
    carrier = Column(String(100))
    
    # Metrics
    days_delayed = Column(Integer)
    cost_impact = Column(Float)
    quantity_affected = Column(Integer)
    
    # Timestamps
    detected_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    expected_resolution = Column(DateTime)
    resolved_at = Column(DateTime)
    
    # Assignment and resolution
    assigned_to = Column(String(100))
    assigned_at = Column(DateTime)
    resolution_notes = Column(Text)
    resolution_action = Column(String(100))  # reassigned, expedited, refunded, etc.
    
    # Flags
    is_customer_notified = Column(Boolean, default=False)
    requires_escalation = Column(Boolean, default=False)
    is_recurring = Column(Boolean, default=False)


class ExceptionAction(Base):
    """Actions taken on exceptions."""
    __tablename__ = "exception_actions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    exception_id = Column(String(50), nullable=False, index=True)
    action_type = Column(String(50), nullable=False)  # status_change, reassign, comment, escalate, notify
    performed_by = Column(String(100), nullable=False)
    performed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    notes = Column(Text)
    previous_value = Column(String(200))
    new_value = Column(String(200))


class ExceptionRule(Base):
    """Rules for automatic exception detection."""
    __tablename__ = "exception_rules"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    rule_id = Column(String(50), nullable=False, unique=True, index=True)
    rule_name = Column(String(200), nullable=False)
    exception_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    
    # Conditions
    source_system = Column(String(30), nullable=False)
    condition_field = Column(String(100), nullable=False)  # e.g., 'days_delayed', 'quantity_on_hand'
    condition_operator = Column(String(20), nullable=False)  # gt, lt, eq, gte, lte
    condition_value = Column(String(100), nullable=False)
    
    # Actions
    auto_assign_to = Column(String(100))
    auto_notify = Column(Boolean, default=True)
    auto_escalate_after_hours = Column(Integer)
    
    # Status
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)


# Database setup
engine = create_engine('sqlite:///data/exceptions.db', echo=False)
Base.metadata.create_all(engine)
SessionLocal = sessionmaker(bind=engine)
