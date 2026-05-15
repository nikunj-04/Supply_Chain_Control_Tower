"""Service for end-to-end order journey visibility across all systems."""
from datetime import datetime
from typing import List, Dict, Optional
from models.oms_models import Order, get_oms_session
from models.wms_models import Inventory, PickingTask, get_wms_session
from models.tms_models import Shipment, get_tms_session
from models.billing_models import Invoice, get_billing_session
from models.returns_models import Return, get_returns_session
from models.tracking_models import ShipmentLocation, TrackingEvent, get_tracking_session
from config import settings


class JourneyService:
    """Service for tracking complete order-to-delivery journey."""
    
    def __init__(self):
        self.oms_session = get_oms_session(settings.oms_db_path)
        self.wms_session = get_wms_session(settings.wms_db_path)
        self.tms_session = get_tms_session(settings.tms_db_path)
        self.billing_session = get_billing_session(settings.billing_db_path)
        self.returns_session = get_returns_session(settings.returns_db_path)
        self.tracking_session = get_tracking_session()
    
    def get_order_journey(self, order_id: str) -> Optional[Dict]:
        """Get complete journey for an order across all systems."""
        # Get order from OMS
        order = self.oms_session.query(Order).filter(
            Order.order_id == order_id
        ).first()
        
        if not order:
            return None
        
        # Build journey timeline
        journey = {
            'order_id': order.order_id,
            'customer': order.customer_name,
            'status': order.status,
            'order_date': order.order_date.isoformat(),
            'total_amount': order.total_value,
            'stages': self._build_journey_stages(order),
            'timeline': self._build_timeline(order),
            'metrics': self._calculate_journey_metrics(order)
        }
        
        return journey
    
    def get_all_journeys(self, status_filter: Optional[str] = None) -> List[Dict]:
        """Get all order journeys with summary information."""
        query = self.oms_session.query(Order)
        
        if status_filter:
            query = query.filter(Order.status == status_filter)
        
        orders = query.order_by(Order.order_date.desc()).limit(50).all()
        
        journeys = []
        for order in orders:
            # Get associated data
            shipment = self.tms_session.query(Shipment).filter(
                Shipment.order_id == order.order_id
            ).first()
            
            # Get latest tracking if available
            latest_location = None
            if shipment:
                latest_location = self.tracking_session.query(ShipmentLocation).filter(
                    ShipmentLocation.shipment_id == shipment.shipment_id
                ).order_by(ShipmentLocation.recorded_at.desc()).first()
            
            # Calculate stage
            current_stage = self._determine_current_stage(order, shipment, latest_location)
            
            journeys.append({
                'order_id': order.order_id,
                'customer': order.customer_name,
                'status': order.status,
                'current_stage': current_stage,
                'order_date': order.order_date.isoformat(),
                'total_amount': order.total_value,
                'items_count': order.total_items,
                'shipment_id': shipment.shipment_id if shipment else None,
                'delivery_progress': latest_location.progress_percentage if latest_location else 0,
                'is_delayed': (shipment and shipment.status == 'delayed') if shipment else False
            })
        
        return journeys
    
    def _build_journey_stages(self, order: Order) -> List[Dict]:
        """Build stages of the journey."""
        stages = []
        
        # Stage 1: Order Placed
        stages.append({
            'stage': 'order_placed',
            'name': 'Order Placed',
            'status': 'completed',
            'timestamp': order.order_date.isoformat(),
            'details': {
                'order_id': order.order_id,
                'customer': order.customer_name,
                'items': order.total_items,
                'amount': order.total_value
            }
        })
        
        # Stage 2: Warehouse Processing
        picking_tasks = self.wms_session.query(PickingTask).filter(
            PickingTask.order_id == order.order_id
        ).all()
        
        if picking_tasks:
            stage_status = 'completed' if order.status not in ['pending', 'processing'] else 'in_progress'
            stages.append({
                'stage': 'warehouse_processing',
                'name': 'Warehouse Processing',
                'status': stage_status,
                'timestamp': picking_tasks[0].created_at.isoformat() if picking_tasks else None,
                'details': {
                    'tasks_count': len(picking_tasks),
                    'tasks': [{
                        'sku': task.sku,
                        'quantity': task.quantity,
                        'location': task.location,
                        'status': task.status,
                        'assigned_to': task.assigned_to,
                        'created_at': task.created_at.isoformat()
                    } for task in picking_tasks[:5]]  # Limit to 5 most recent
                }
            })
        else:
            stages.append({
                'stage': 'warehouse_processing',
                'name': 'Warehouse Processing',
                'status': 'pending' if order.status == 'pending' else 'in_progress',
                'timestamp': None,
                'details': {}
            })
        
        # Stage 3: Shipment
        shipment = self.tms_session.query(Shipment).filter(
            Shipment.order_id == order.order_id
        ).first()
        
        if shipment:
            shipment_status = 'completed' if shipment.actual_delivery else 'in_progress'
            stages.append({
                'stage': 'in_transit',
                'name': 'In Transit',
                'status': shipment_status,
                'timestamp': shipment.actual_pickup.isoformat() if shipment.actual_pickup else shipment.scheduled_pickup.isoformat(),
                'details': {
                    'shipment_id': shipment.shipment_id,
                    'carrier': shipment.carrier,
                    'tracking_number': shipment.tracking_number,
                    'origin': shipment.origin,
                    'destination': shipment.destination,
                    'estimated_delivery': shipment.estimated_delivery.isoformat(),
                    'actual_delivery': shipment.actual_delivery.isoformat() if shipment.actual_delivery else None
                }
            })
            
            # Get tracking details if available
            latest_location = self.tracking_session.query(ShipmentLocation).filter(
                ShipmentLocation.shipment_id == shipment.shipment_id
            ).order_by(ShipmentLocation.recorded_at.desc()).first()
            
            if latest_location:
                stages[-1]['details']['current_location'] = {
                    'name': latest_location.location_name,
                    'latitude': latest_location.latitude,
                    'longitude': latest_location.longitude,
                    'progress': latest_location.progress_percentage
                }
        else:
            stages.append({
                'stage': 'in_transit',
                'name': 'In Transit',
                'status': 'pending',
                'timestamp': None,
                'details': {}
            })
        
        # Stage 4: Delivery
        if shipment and shipment.actual_delivery:
            # Safe comparison handling for both real datetimes and mocks
            try:
                on_time = shipment.actual_delivery <= shipment.estimated_delivery
            except TypeError:
                # Handle mock objects or None values
                on_time = None
            
            stages.append({
                'stage': 'delivered',
                'name': 'Delivered',
                'status': 'completed',
                'timestamp': shipment.actual_delivery.isoformat(),
                'details': {
                    'delivery_date': shipment.actual_delivery.isoformat(),
                    'on_time': on_time
                }
            })
        else:
            stages.append({
                'stage': 'delivered',
                'name': 'Delivered',
                'status': 'pending',
                'timestamp': None,
                'details': {}
            })
        
        # Stage 5: Billing
        invoice = self.billing_session.query(Invoice).filter(
            Invoice.order_id == order.order_id
        ).first()
        
        if invoice:
            stages.append({
                'stage': 'billing',
                'name': 'Billing',
                'status': 'completed',
                'timestamp': invoice.invoice_date.isoformat(),
                'details': {
                    'invoice_id': invoice.invoice_id,
                    'amount': invoice.total,
                    'status': invoice.status,
                    'due_date': invoice.due_date.isoformat()
                }
            })
        else:
            stages.append({
                'stage': 'billing',
                'name': 'Billing',
                'status': 'pending',
                'timestamp': None,
                'details': {}
            })
        
        # Check for returns
        returns = self.returns_session.query(Return).filter(
            Return.order_id == order.order_id
        ).all()
        
        if returns:
            stages.append({
                'stage': 'returns',
                'name': 'Returns',
                'status': 'in_progress' if any(r.status != 'completed' for r in returns) else 'completed',
                'timestamp': returns[0].return_date.isoformat(),
                'details': {
                    'returns_count': len(returns),
                    'returns': [{
                        'return_id': r.return_id,
                        'reason': r.reason,
                        'status': r.status,
                        'quantity': r.quantity
                    } for r in returns]
                }
            })
        
        return stages
    
    def _build_timeline(self, order: Order) -> List[Dict]:
        """Build chronological timeline of all events."""
        events = []
        
        # Order event
        try:
            details = f'{order.total_items} items, ${order.total_value:.2f}'
        except (TypeError, AttributeError):
            # Handle mock objects or missing attributes
            details = f'{getattr(order, "total_items", "?")} items, ${getattr(order, "total_value", 0)}'
        
        events.append({
            'timestamp': order.order_date.isoformat(),
            'system': 'OMS',
            'event': 'Order Created',
            'description': f'Order {order.order_id} placed by {order.customer_name}',
            'details': details
        })
        
        # Warehouse events
        picking_tasks = self.wms_session.query(PickingTask).filter(
            PickingTask.order_id == order.order_id
        ).order_by(PickingTask.created_at).all()
        
        for task in picking_tasks:
            events.append({
                'timestamp': task.created_at.isoformat(),
                'system': 'WMS',
                'event': f'Picking Task {task.status.title()}',
                'description': f'{task.quantity}x {task.sku} from {task.location}',
                'details': f'Assigned to: {task.assigned_to or "Unassigned"}'
            })
        
        # Shipment events
        shipment = self.tms_session.query(Shipment).filter(
            Shipment.order_id == order.order_id
        ).first()
        
        if shipment:
            if shipment.actual_pickup:
                events.append({
                    'timestamp': shipment.actual_pickup.isoformat(),
                    'system': 'TMS',
                    'event': 'Shipment Picked Up',
                    'description': f'Shipment {shipment.shipment_id} picked up from {shipment.origin}',
                    'details': f'Carrier: {shipment.carrier}'
                })
            
            # Tracking events
            tracking_events = self.tracking_session.query(TrackingEvent).filter(
                TrackingEvent.shipment_id == shipment.shipment_id
            ).order_by(TrackingEvent.occurred_at).all()
            
            for te in tracking_events:
                events.append({
                    'timestamp': te.occurred_at.isoformat(),
                    'system': 'Tracking',
                    'event': te.event_type.replace('_', ' ').title(),
                    'description': te.description,
                    'details': f'Location: {te.location}'
                })
            
            if shipment.actual_delivery:
                events.append({
                    'timestamp': shipment.actual_delivery.isoformat(),
                    'system': 'TMS',
                    'event': 'Delivered',
                    'description': f'Delivered to {shipment.destination}',
                    'details': 'On time' if shipment.actual_delivery <= shipment.estimated_delivery else 'Delayed'
                })
        
        # Billing events
        invoice = self.billing_session.query(Invoice).filter(
            Invoice.order_id == order.order_id
        ).first()
        
        if invoice:
            events.append({
                'timestamp': invoice.invoice_date.isoformat(),
                'system': 'Billing',
                'event': 'Invoice Generated',
                'description': f'Invoice {invoice.invoice_id} for ${invoice.total:.2f}',
                'details': f'Status: {invoice.status}'
            })
        
        # Return events
        returns = self.returns_session.query(Return).filter(
            Return.order_id == order.order_id
        ).all()
        
        for ret in returns:
            events.append({
                'timestamp': ret.return_date.isoformat(),
                'system': 'Returns',
                'event': 'Return Initiated',
                'description': f'Return {ret.return_id} - {ret.reason}',
                'details': f'Quantity: {ret.quantity}, Status: {ret.status}'
            })
        
        # Sort by timestamp
        events.sort(key=lambda x: x['timestamp'])
        
        return events
    
    def _calculate_journey_metrics(self, order: Order) -> Dict:
        """Calculate key metrics for the journey."""
        now = datetime.utcnow()
        
        # Order age
        order_age_hours = (now - order.order_date).total_seconds() / 3600
        
        # Get shipment for transit time
        shipment = self.tms_session.query(Shipment).filter(
            Shipment.order_id == order.order_id
        ).first()
        
        transit_time_hours = None
        on_time_delivery = None
        
        if shipment:
            # Use the later of actual_pickup or order_date to ensure transit doesn't exceed order age
            transit_start = max(shipment.actual_pickup, order.order_date) if shipment.actual_pickup else order.order_date
            
            if shipment.actual_delivery:
                transit_time_hours = (shipment.actual_delivery - transit_start).total_seconds() / 3600
                on_time_delivery = shipment.actual_delivery <= shipment.estimated_delivery
            elif shipment.actual_pickup:
                transit_time_hours = (now - transit_start).total_seconds() / 3600
        
        # Count timeline events
        timeline_events = self._build_timeline(order)
        
        return {
            'order_age_hours': round(order_age_hours, 1),
            'transit_time_hours': round(transit_time_hours, 1) if transit_time_hours else None,
            'on_time_delivery': on_time_delivery,
            'total_events': len(timeline_events),
            'systems_touched': len(set(e['system'] for e in timeline_events))
        }
    
    def _determine_current_stage(self, order: Order, shipment: Optional[Shipment], 
                                   location: Optional[ShipmentLocation]) -> str:
        """Determine the current stage of the order journey."""
        if order.status == 'pending':
            return 'order_placed'
        elif order.status == 'processing':
            return 'warehouse_processing'
        elif shipment:
            if shipment.actual_delivery:
                return 'delivered'
            elif location and location.status == 'out_for_delivery':
                return 'out_for_delivery'
            elif shipment.actual_pickup:
                return 'in_transit'
            else:
                return 'warehouse_processing'
        else:
            return 'warehouse_processing'
    
    def get_journey_stats(self) -> Dict:
        """Get summary statistics for all journeys."""
        total_orders = self.oms_session.query(Order).count()
        
        # Orders by status
        pending = self.oms_session.query(Order).filter(Order.status == 'pending').count()
        processing = self.oms_session.query(Order).filter(Order.status == 'processing').count()
        shipped = self.oms_session.query(Order).filter(Order.status == 'shipped').count()
        delivered = self.oms_session.query(Order).filter(Order.status == 'delivered').count()
        
        # Active shipments
        active_shipments = self.tms_session.query(Shipment).filter(
            Shipment.status.in_(['scheduled', 'in_transit'])
        ).count()
        
        return {
            'total_orders': total_orders,
            'pending': pending,
            'processing': processing,
            'shipped': shipped,
            'delivered': delivered,
            'active_shipments': active_shipments
        }
    
    def close(self):
        """Close all database sessions."""
        self.oms_session.close()
        self.wms_session.close()
        self.tms_session.close()
        self.billing_session.close()
        self.returns_session.close()
        self.tracking_session.close()
