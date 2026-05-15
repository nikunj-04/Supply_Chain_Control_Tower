"""Service for managing supply chain exceptions."""
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from models.exception_models import Exception, ExceptionAction, ExceptionRule, SessionLocal
from models.tms_models import Shipment, get_tms_session
from models.wms_models import Inventory, get_wms_session
from models.oms_models import Order, get_oms_session
from models.returns_models import Return, get_returns_session
from config import settings
import random


class ExceptionService:
    """Service for exception detection, management, and resolution."""
    
    def __init__(self):
        self.session = SessionLocal()
    
    def detect_exceptions(self) -> List[Dict]:
        """Scan all systems and detect exceptions based on rules."""
        exceptions_detected = []
        
        # Detect TMS exceptions (delayed shipments)
        tms_exceptions = self._detect_tms_exceptions()
        exceptions_detected.extend(tms_exceptions)
        
        # Detect WMS exceptions (low inventory)
        wms_exceptions = self._detect_wms_exceptions()
        exceptions_detected.extend(wms_exceptions)
        
        # Detect OMS exceptions (order issues)
        oms_exceptions = self._detect_oms_exceptions()
        exceptions_detected.extend(oms_exceptions)
        
        # Detect Returns exceptions (high return rates)
        returns_exceptions = self._detect_returns_exceptions()
        exceptions_detected.extend(returns_exceptions)
        
        return exceptions_detected
    
    def _detect_tms_exceptions(self) -> List[Dict]:
        """Detect transportation exceptions."""
        exceptions = []
        tms_session = get_tms_session(settings.tms_db_path)
        
        try:
            now = datetime.utcnow()
            
            # Find delayed shipments
            delayed_shipments = tms_session.query(Shipment).filter(
                Shipment.status.in_(['in_transit', 'scheduled']),
                Shipment.estimated_delivery < now,
                Shipment.actual_delivery.is_(None)
            ).all()
            
            for shipment in delayed_shipments:
                days_delayed = (now - shipment.estimated_delivery).days
                
                exception_id = f"EXC-TMS-{shipment.shipment_id}"
                
                # Check if exception already exists by exception_id OR entity_id with open/in_progress status
                # Use no_autoflush to prevent premature flush of pending objects
                with self.session.no_autoflush:
                    existing = self.session.query(Exception).filter(
                        ((Exception.exception_id == exception_id) |
                         (Exception.entity_id == shipment.shipment_id)),
                        Exception.status.in_(['open', 'in_progress'])
                    ).first()
                
                if not existing:
                    severity = 'critical' if days_delayed >= 1 else 'warning'
                    
                    # Calculate cost impact safely (handle mocks in tests)
                    try:
                        cost_impact = float(shipment.cost) * 0.1 * days_delayed
                    except (TypeError, ValueError, AttributeError):
                        cost_impact = 0.0
                    
                    exception = Exception(
                        exception_id=exception_id,
                        exception_type='delay',
                        severity=severity,
                        status='open',
                        source_system='TMS',
                        entity_type='shipment',
                        entity_id=shipment.shipment_id,
                        title=f"Shipment {shipment.shipment_id} delayed by {days_delayed} day(s)",
                        description=f"Shipment from {shipment.origin} to {shipment.destination} is {days_delayed} day(s) past estimated delivery date.",
                        impact=f"Customer delivery delay, potential SLA breach",
                        customer=f"Customer-{shipment.order_id[:3]}",
                        location=shipment.destination,
                        carrier=shipment.carrier,
                        days_delayed=days_delayed,
                        cost_impact=cost_impact,  # 10% cost per day delayed
                        detected_at=now,
                        expected_resolution=now + timedelta(days=1),
                        requires_escalation=(days_delayed >= 2)
                    )
                    
                    self.session.add(exception)
                    exceptions.append({
                        'exception_id': exception.exception_id,
                        'type': 'delay',
                        'severity': severity,
                        'entity': shipment.shipment_id
                    })
            
            try:
                self.session.commit()
            except BaseException as e:
                self.session.rollback()
                print(f"Error committing TMS exceptions: {e}")
            
        finally:
            tms_session.close()
        
        return exceptions
    
    def _detect_wms_exceptions(self) -> List[Dict]:
        """Detect warehouse/inventory exceptions."""
        exceptions = []
        wms_session = get_wms_session(settings.wms_db_path)
        
        try:
            now = datetime.utcnow()
            
            # Find low inventory items
            low_inventory = wms_session.query(Inventory).filter(
                Inventory.quantity_on_hand < Inventory.reorder_point
            ).all()
            
            for item in low_inventory:
                # Check if exception already exists
                exception_id = f"EXC-WMS-{item.sku}"
                
                # Use no_autoflush to prevent premature flush of pending objects
                with self.session.no_autoflush:
                    existing = self.session.query(Exception).filter(
                        ((Exception.exception_id == exception_id) |
                         (Exception.entity_id == item.sku)),
                        Exception.exception_type == 'inventory',
                        Exception.status.in_(['open', 'in_progress'])
                    ).first()
                
                if not existing:
                    days_until_stockout = max(1, int(item.quantity_on_hand / 10))  # Assuming 10 units/day usage
                    severity = 'critical' if days_until_stockout <= 2 else 'warning'
                    
                    exception = Exception(
                        exception_id=exception_id,
                        exception_type='inventory',
                        severity=severity,
                        status='open',
                        source_system='WMS',
                        entity_type='inventory',
                        entity_id=item.sku,
                        title=f"Low inventory: {item.sku}",
                        description=f"Current stock ({item.quantity_on_hand}) below reorder point ({item.reorder_point}). Estimated {days_until_stockout} days until stockout.",
                        impact=f"Risk of stockout, potential order delays",
                        location=item.warehouse_location,
                        quantity_affected=int(item.reorder_point - item.quantity_on_hand),
                        cost_impact=50.0 * (item.reorder_point - item.quantity_on_hand),  # Assuming $50/unit average cost
                        detected_at=now,
                        expected_resolution=now + timedelta(days=3),
                        requires_escalation=(days_until_stockout <= 1)
                    )
                    
                    try:
                        self.session.add(exception)
                        self.session.flush()  # Flush immediately to catch constraint errors
                        exceptions.append({
                            'exception_id': exception.exception_id,
                            'type': 'inventory',
                            'severity': severity,
                            'entity': item.sku
                        })
                    except BaseException as e:
                        self.session.rollback()
                        print(f"Skipping duplicate WMS exception {exception_id}: {e}")
            
            try:
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                print(f"Error committing WMS exceptions: {e}")
            
        finally:
            wms_session.close()
        
        return exceptions
    
    def _detect_oms_exceptions(self) -> List[Dict]:
        """Detect order management exceptions."""
        exceptions = []
        oms_session = get_oms_session(settings.oms_db_path)
        
        try:
            now = datetime.utcnow()
            
            # Find orders stuck in processing for too long
            stuck_orders = oms_session.query(Order).filter(
                Order.status == 'processing',
                Order.order_date < (now - timedelta(hours=24))
            ).all()
            
            for order in stuck_orders:
                exception_id = f"EXC-OMS-{order.order_id}"
                
                # Use no_autoflush to prevent premature flush of pending objects
                with self.session.no_autoflush:
                    existing = self.session.query(Exception).filter(
                        ((Exception.exception_id == exception_id) |
                         (Exception.entity_id == order.order_id)),
                        Exception.status.in_(['open', 'in_progress'])
                    ).first()
                
                if not existing:
                    hours_delayed = int((now - order.order_date).total_seconds() / 3600)
                    severity = 'critical' if hours_delayed >= 48 else 'warning'
                    
                    exception = Exception(
                        exception_id=exception_id,
                        exception_type='processing_delay',
                        severity=severity,
                        status='open',
                        source_system='OMS',
                        entity_type='order',
                        entity_id=order.order_id,
                        title=f"Order {order.order_id} stuck in processing",
                        description=f"Order has been in processing status for {hours_delayed} hours without progression.",
                        impact=f"Customer order delay, potential cancellation risk",
                        customer=order.customer_name,
                        cost_impact=order.total_value * 0.05,  # 5% risk cost
                        detected_at=now,
                        expected_resolution=now + timedelta(hours=4),
                        requires_escalation=(hours_delayed >= 48)
                    )
                    
                    try:
                        self.session.add(exception)
                        self.session.flush()  # Flush immediately to catch constraint errors
                        exceptions.append({
                            'exception_id': exception.exception_id,
                            'type': 'processing_delay',
                            'severity': severity,
                            'entity': order.order_id
                        })
                    except BaseException as e:
                        self.session.rollback()
                        print(f"Skipping duplicate OMS exception {exception_id}: {e}")
            
            try:
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                print(f"Error committing OMS exceptions: {e}")
            
        finally:
            oms_session.close()
        
        return exceptions
    
    def _detect_returns_exceptions(self) -> List[Dict]:
        """Detect returns-related exceptions."""
        exceptions = []
        returns_session = get_returns_session(settings.returns_db_path)
        
        try:
            now = datetime.utcnow()
            
            # Find returns pending inspection for too long
            pending_returns = returns_session.query(Return).filter(
                Return.status == 'received',
                Return.received_date < (now - timedelta(days=3))
            ).all()
            
            for ret in pending_returns:
                exception_id = f"EXC-RET-{ret.return_id}"
                
                # Use no_autoflush to prevent premature flush of pending objects
                with self.session.no_autoflush:
                    existing = self.session.query(Exception).filter(
                        ((Exception.exception_id == exception_id) |
                         (Exception.entity_id == ret.return_id)),
                        Exception.status.in_(['open', 'in_progress'])
                    ).first()
                
                if not existing:
                    days_pending = (now - ret.received_date).days
                    severity = 'critical' if days_pending >= 5 else 'warning'
                    
                    exception = Exception(
                        exception_id=exception_id,
                        exception_type='returns_delay',
                        severity=severity,
                        status='open',
                        source_system='Returns',
                        entity_type='return',
                        entity_id=ret.return_id,
                        title=f"Return {ret.return_id} pending inspection",
                        description=f"Return has been awaiting inspection for {days_pending} days.",
                        impact=f"Customer refund delay, restocking delay",
                        customer=f"Customer-{ret.order_id[:3]}",
                        quantity_affected=1,  # Default quantity
                        cost_impact=ret.refund_amount,
                        detected_at=now,
                        expected_resolution=now + timedelta(days=1),
                        requires_escalation=(days_pending >= 7)
                    )
                    
                    try:
                        self.session.add(exception)
                        self.session.flush()  # Flush immediately to catch constraint errors
                        exceptions.append({
                            'exception_id': exception.exception_id,
                            'type': 'returns_delay',
                            'severity': severity,
                            'entity': ret.return_id
                        })
                    except BaseException as e:
                        self.session.rollback()
                        print(f"Skipping duplicate Returns exception {exception_id}: {e}")
            
            try:
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                print(f"Error committing Returns exceptions: {e}")
            
        finally:
            returns_session.close()
        
        return exceptions
    
    def get_all_exceptions(self, status: Optional[str] = None, 
                           severity: Optional[str] = None,
                           exception_type: Optional[str] = None) -> List[Dict]:
        """Get all exceptions with optional filters."""
        query = self.session.query(Exception)
        
        if status:
            query = query.filter(Exception.status == status)
        if severity:
            query = query.filter(Exception.severity == severity)
        if exception_type:
            query = query.filter(Exception.exception_type == exception_type)
        
        exceptions = query.order_by(
            Exception.severity.desc(),
            Exception.detected_at.desc()
        ).all()
        
        return [self._exception_to_dict(exc) for exc in exceptions]
    
    def get_exception_by_id(self, exception_id: str) -> Optional[Dict]:
        """Get a specific exception by ID."""
        exception = self.session.query(Exception).filter(
            Exception.exception_id == exception_id
        ).first()
        
        if exception:
            return self._exception_to_dict(exception)
        return None
    
    def update_exception_status(self, exception_id: str, new_status: str, 
                                 user: str, notes: Optional[str] = None) -> Dict:
        """Update exception status."""
        exception = self.session.query(Exception).filter(
            Exception.exception_id == exception_id
        ).first()
        
        if not exception:
            raise ValueError(f"Exception {exception_id} not found")
        
        old_status = exception.status
        exception.status = new_status
        
        if new_status == 'resolved':
            exception.resolved_at = datetime.utcnow()
            if notes:
                exception.resolution_notes = notes
        
        # Log action
        action = ExceptionAction(
            exception_id=exception_id,
            action_type='status_change',
            performed_by=user,
            notes=notes,
            previous_value=old_status,
            new_value=new_status
        )
        
        self.session.add(action)
        self.session.commit()
        
        return self._exception_to_dict(exception)
    
    def assign_exception(self, exception_id: str, assigned_to: str, 
                         assigned_by: str) -> Dict:
        """Assign exception to a user."""
        exception = self.session.query(Exception).filter(
            Exception.exception_id == exception_id
        ).first()
        
        if not exception:
            raise ValueError(f"Exception {exception_id} not found")
        
        old_assignee = exception.assigned_to
        exception.assigned_to = assigned_to
        exception.assigned_at = datetime.utcnow()
        exception.status = 'in_progress'
        
        # Log action
        action = ExceptionAction(
            exception_id=exception_id,
            action_type='reassign',
            performed_by=assigned_by,
            notes=f"Assigned to {assigned_to}",
            previous_value=old_assignee or 'unassigned',
            new_value=assigned_to
        )
        
        self.session.add(action)
        self.session.commit()
        
        return self._exception_to_dict(exception)
    
    def add_exception_note(self, exception_id: str, user: str, note: str) -> Dict:
        """Add a note/comment to an exception."""
        action = ExceptionAction(
            exception_id=exception_id,
            action_type='comment',
            performed_by=user,
            notes=note
        )
        
        self.session.add(action)
        self.session.commit()
        
        return {'success': True, 'action_id': action.id}
    
    def get_exception_actions(self, exception_id: str) -> List[Dict]:
        """Get all actions/history for an exception."""
        actions = self.session.query(ExceptionAction).filter(
            ExceptionAction.exception_id == exception_id
        ).order_by(ExceptionAction.performed_at.desc()).all()
        
        return [{
            'id': action.id,
            'action_type': action.action_type,
            'performed_by': action.performed_by,
            'performed_at': action.performed_at.isoformat(),
            'notes': action.notes,
            'previous_value': action.previous_value,
            'new_value': action.new_value
        } for action in actions]
    
    def get_exception_stats(self) -> Dict:
        """Get summary statistics for exceptions."""
        total = self.session.query(Exception).count()
        open_count = self.session.query(Exception).filter(Exception.status == 'open').count()
        in_progress = self.session.query(Exception).filter(Exception.status == 'in_progress').count()
        resolved = self.session.query(Exception).filter(Exception.status == 'resolved').count()
        
        critical = self.session.query(Exception).filter(
            Exception.severity == 'critical',
            Exception.status.in_(['open', 'in_progress'])
        ).count()
        
        warning = self.session.query(Exception).filter(
            Exception.severity == 'warning',
            Exception.status.in_(['open', 'in_progress'])
        ).count()
        
        # Count by type
        by_type = {}
        for exc_type in ['delay', 'inventory', 'processing_delay', 'returns_delay', 'quality']:
            count = self.session.query(Exception).filter(
                Exception.exception_type == exc_type,
                Exception.status.in_(['open', 'in_progress'])
            ).count()
            if count > 0:
                by_type[exc_type] = count
        
        return {
            'total': total,
            'open': open_count,
            'in_progress': in_progress,
            'resolved': resolved,
            'critical': critical,
            'warning': warning,
            'by_type': by_type
        }
    
    def _exception_to_dict(self, exception: Exception) -> Dict:
        """Convert exception model to dictionary."""
        return {
            'exception_id': exception.exception_id,
            'exception_type': exception.exception_type,
            'severity': exception.severity,
            'status': exception.status,
            'source_system': exception.source_system,
            'entity_type': exception.entity_type,
            'entity_id': exception.entity_id,
            'title': exception.title,
            'description': exception.description,
            'impact': exception.impact,
            'customer': exception.customer,
            'location': exception.location,
            'carrier': exception.carrier,
            'days_delayed': exception.days_delayed,
            'cost_impact': exception.cost_impact,
            'quantity_affected': exception.quantity_affected,
            'detected_at': exception.detected_at.isoformat() if exception.detected_at else None,
            'expected_resolution': exception.expected_resolution.isoformat() if exception.expected_resolution else None,
            'resolved_at': exception.resolved_at.isoformat() if exception.resolved_at else None,
            'assigned_to': exception.assigned_to,
            'assigned_at': exception.assigned_at.isoformat() if exception.assigned_at else None,
            'resolution_notes': exception.resolution_notes,
            'resolution_action': exception.resolution_action,
            'is_customer_notified': exception.is_customer_notified,
            'requires_escalation': exception.requires_escalation,
            'is_recurring': exception.is_recurring
        }
    
    def close(self):
        """Close database session."""
        self.session.close()
