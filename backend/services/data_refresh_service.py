"""Service for refreshing and updating dashboard data to reflect current time."""
from datetime import datetime, timedelta
from typing import Dict, Any
import random
from sqlalchemy import func

from models.tms_models import Shipment, get_tms_session
from models.tracking_models import ShipmentLocation, TrackingEvent, get_tracking_session
from models.oms_models import Order, get_oms_session
from models.wms_models import PickingTask, get_wms_session
from config import settings
from logger import setup_logger

logger = setup_logger(__name__)


class DataRefreshService:
    """Service for refreshing time-sensitive data across all systems."""
    
    def __init__(self):
        """Initialize refresh service."""
        pass
    
    def refresh_all_data(self) -> Dict[str, Any]:
        """Refresh all time-sensitive data."""
        logger.info("Starting comprehensive data refresh")
        
        results = {
            'shipment_tracking': self.refresh_shipment_tracking(),
            'shipment_statuses': self.refresh_shipment_statuses(),
            'order_statuses': self.refresh_order_statuses(),
            'picking_tasks': self.refresh_picking_tasks(),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        logger.info(f"Data refresh completed: {results}")
        return results
    
    def refresh_shipment_tracking(self) -> Dict[str, int]:
        """Update shipment tracking data with current timestamps and realistic positions."""
        logger.info("Refreshing shipment tracking data")
        
        # Use default paths like other services do
        from services.tracking_service import TrackingService
        tracking_service = TrackingService()
        tracking_session = tracking_service.tracking_session
        tms_session = tracking_service.tms_session
        
        try:
            now = datetime.utcnow()
            today_start = datetime(now.year, now.month, now.day, 0, 0, 0)
            
            # Get all active shipments
            active_shipments = tms_session.query(Shipment).filter(
                Shipment.status.in_(['scheduled', 'in_transit', 'out_for_delivery'])
            ).all()
            
            updated_count = 0
            created_count = 0
            
            for shipment in active_shipments:
                # Check if location tracking exists
                location = tracking_session.query(ShipmentLocation).filter(
                    ShipmentLocation.shipment_id == shipment.shipment_id
                ).first()
                
                # Update shipment dates to be relative to today
                shipment_age_hours = random.uniform(2, 48)  # Random age between 2-48 hours
                
                # Update shipment timestamps
                shipment.scheduled_pickup = today_start + timedelta(hours=random.randint(6, 10))
                shipment.actual_pickup = today_start + timedelta(hours=random.randint(6, 12))
                estimated_duration = random.uniform(24, 72)  # 1-3 days transit
                shipment.estimated_delivery = shipment.actual_pickup + timedelta(hours=estimated_duration)
                
                # Calculate realistic progress based on current time
                if shipment.actual_pickup and shipment.actual_pickup <= now:
                    elapsed_hours = (now - shipment.actual_pickup).total_seconds() / 3600
                    total_hours = (shipment.estimated_delivery - shipment.actual_pickup).total_seconds() / 3600
                    progress = min(0.95, elapsed_hours / total_hours if total_hours > 0 else 0.5)
                    
                    # Update status based on progress
                    if progress < 0.1:
                        shipment.status = 'in_transit'
                        loc_status = 'in_transit'
                    elif progress < 0.85:
                        shipment.status = 'in_transit'
                        loc_status = 'in_transit'
                    elif progress < 0.95:
                        shipment.status = 'out_for_delivery'
                        loc_status = 'out_for_delivery'
                    else:
                        # Some are getting close to delivery
                        if random.random() < 0.3:  # 30% chance of being delivered
                            shipment.status = 'delivered'
                            shipment.actual_delivery = now - timedelta(minutes=random.randint(5, 60))
                            loc_status = 'delivered'
                        else:
                            shipment.status = 'out_for_delivery'
                            loc_status = 'out_for_delivery'
                else:
                    progress = 0.0
                    shipment.status = 'scheduled'
                    loc_status = 'scheduled'
                
                if location:
                    # Update existing location with new progress
                    if loc_status != 'delivered':
                        # Get route segment to calculate new position
                        from services.tracking_service import TrackingService
                        tracking_service = TrackingService()
                        
                        origin_coords = tracking_service._get_location_coords(shipment.origin)
                        dest_coords = tracking_service._get_location_coords(shipment.destination)
                        
                        # Calculate new position based on progress
                        location.latitude = origin_coords[0] + (dest_coords[0] - origin_coords[0]) * progress
                        location.longitude = origin_coords[1] + (dest_coords[1] - origin_coords[1]) * progress
                        location.progress_percentage = progress * 100
                        
                        # Calculate distances
                        total_distance = tracking_service._calculate_distance(
                            origin_coords[0], origin_coords[1],
                            dest_coords[0], dest_coords[1]
                        )
                        location.distance_traveled_miles = total_distance * progress * 0.621371  # km to miles
                        location.distance_remaining_miles = total_distance * (1 - progress) * 0.621371
                        
                        location.location_name = tracking_service._get_nearest_city(
                            location.latitude, location.longitude
                        )
                        location.status = loc_status
                        location.recorded_at = now
                        location.estimated_arrival = shipment.estimated_delivery
                        location.speed_mph = random.uniform(50, 65) if loc_status == 'in_transit' else 0
                        location.is_delayed = shipment.estimated_delivery < now
                        
                        if location.is_delayed:
                            location.delay_reason = random.choice([
                                'Weather delay', 'Traffic congestion', 'Mechanical issue',
                                'Loading delay', 'Route deviation'
                            ])
                        
                        updated_count += 1
                    else:
                        # Delivered - set final position
                        tracking_service = TrackingService()
                        dest_coords = tracking_service._get_location_coords(shipment.destination)
                        location.latitude = dest_coords[0]
                        location.longitude = dest_coords[1]
                        location.progress_percentage = 100.0
                        location.distance_remaining_miles = 0
                        location.status = 'delivered'
                        location.recorded_at = shipment.actual_delivery
                        location.speed_mph = 0
                        updated_count += 1
                else:
                    # Create new tracking location
                    from services.tracking_service import TrackingService
                    tracking_service = TrackingService()
                    tracking_service._create_initial_tracking(shipment)
                    created_count += 1
            
            tms_session.commit()
            tracking_session.commit()
            
            return {
                'updated': updated_count,
                'created': created_count,
                'total': len(active_shipments)
            }
            
        except Exception as e:
            logger.error(f"Error refreshing shipment tracking: {e}")
            raise
    
    def refresh_shipment_statuses(self) -> Dict[str, int]:
        """Update shipment statuses based on current time."""
        tms_session = get_tms_session(settings.tms_db_path)
        
        try:
            now = datetime.utcnow()
            updated = 0
            
            # Find shipments that should have progressed
            scheduled_shipments = tms_session.query(Shipment).filter(
                Shipment.status == 'scheduled',
                Shipment.scheduled_pickup <= now
            ).all()
            
            for shipment in scheduled_shipments:
                shipment.status = 'in_transit'
                shipment.actual_pickup = shipment.scheduled_pickup
                updated += 1
            
            # Find shipments that should be out for delivery
            in_transit_shipments = tms_session.query(Shipment).filter(
                Shipment.status == 'in_transit',
                Shipment.estimated_delivery <= now + timedelta(hours=4)
            ).all()
            
            for shipment in in_transit_shipments:
                if random.random() < 0.6:  # 60% transition to out for delivery
                    shipment.status = 'out_for_delivery'
                    updated += 1
            
            tms_session.commit()
            return {'updated': updated}
            
        finally:
            tms_session.close()
    
    def refresh_order_statuses(self) -> Dict[str, int]:
        """Update order statuses based on current time."""
        oms_session = get_oms_session(settings.oms_db_path)
        
        try:
            now = datetime.utcnow()
            updated = 0
            
            # Update pending orders
            pending_orders = oms_session.query(Order).filter(
                Order.status == 'pending',
                Order.order_date <= now - timedelta(hours=2)
            ).all()
            
            for order in pending_orders:
                if random.random() < 0.7:  # 70% get confirmed
                    order.status = 'confirmed'
                    updated += 1
            
            # Update confirmed orders
            confirmed_orders = oms_session.query(Order).filter(
                Order.status == 'confirmed',
                Order.order_date <= now - timedelta(hours=6)
            ).all()
            
            for order in confirmed_orders:
                if random.random() < 0.5:  # 50% start processing
                    order.status = 'processing'
                    updated += 1
            
            oms_session.commit()
            return {'updated': updated}
            
        finally:
            oms_session.close()
    
    def refresh_picking_tasks(self) -> Dict[str, int]:
        """Update warehouse picking task statuses."""
        wms_session = get_wms_session(settings.wms_db_path)
        
        try:
            now = datetime.utcnow()
            updated = 0
            
            # Update pending tasks
            pending_tasks = wms_session.query(PickingTask).filter(
                PickingTask.status == 'pending',
                PickingTask.created_at <= now - timedelta(hours=1)
            ).all()
            
            for task in pending_tasks:
                if random.random() < 0.6:  # 60% get picked up
                    task.status = 'in_progress'
                    task.started_at = now - timedelta(minutes=random.randint(5, 30))
                    updated += 1
            
            # Complete some in-progress tasks
            in_progress_tasks = wms_session.query(PickingTask).filter(
                PickingTask.status == 'in_progress',
                PickingTask.started_at <= now - timedelta(minutes=20)
            ).all()
            
            for task in in_progress_tasks:
                if random.random() < 0.4:  # 40% get completed
                    task.status = 'completed'
                    task.completed_at = now - timedelta(minutes=random.randint(1, 10))
                    updated += 1
            
            wms_session.commit()
            return {'updated': updated}
            
        finally:
            wms_session.close()


# Singleton instance
data_refresh_service = DataRefreshService()
