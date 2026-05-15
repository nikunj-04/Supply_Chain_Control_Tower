"""Service for real-time shipment tracking."""
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
import random
import math
from models.tracking_models import (
    ShipmentLocation, TrackingEvent, RouteSegment, ETAUpdate, 
    get_tracking_session
)
from models.tms_models import Shipment, get_tms_session
from config import settings


class TrackingService:
    """Service for shipment tracking and location updates."""
    
    # Major US cities with coordinates for simulation
    LOCATIONS = {
        'Los Angeles, CA': (34.0522, -118.2437),
        'Chicago, IL': (41.8781, -87.6298),
        'New York, NY': (40.7128, -74.0060),
        'Houston, TX': (29.7604, -95.3698),
        'Phoenix, AZ': (33.4484, -112.0740),
        'Philadelphia, PA': (39.9526, -75.1652),
        'Dallas, TX': (32.7767, -96.7970),
        'Atlanta, GA': (33.7490, -84.3880),
        'Miami, FL': (25.7617, -80.1918),
        'Seattle, WA': (47.6062, -122.3321),
        'Denver, CO': (39.7392, -104.9903),
        'Boston, MA': (42.3601, -71.0589),
    }
    
    def __init__(self):
        self.tracking_session = get_tracking_session()
        self.tms_session = get_tms_session(settings.tms_db_path)
    
    def initialize_tracking_data(self) -> Dict:
        """Initialize tracking data for all active shipments."""
        shipments = self.tms_session.query(Shipment).filter(
            Shipment.status.in_(['scheduled', 'in_transit'])
        ).all()
        
        initialized_count = 0
        for shipment in shipments:
            # Check if tracking already exists
            existing = self.tracking_session.query(ShipmentLocation).filter(
                ShipmentLocation.shipment_id == shipment.shipment_id
            ).first()
            
            if not existing:
                self._create_initial_tracking(shipment)
                initialized_count += 1
        
        self.tracking_session.commit()
        
        return {
            'initialized': initialized_count,
            'total_shipments': len(shipments)
        }
    
    def _create_initial_tracking(self, shipment: Shipment):
        """Create initial tracking data for a shipment."""
        # Parse origin and destination
        origin_coords = self._get_location_coords(shipment.origin)
        dest_coords = self._get_location_coords(shipment.destination)
        
        # Calculate total distance
        total_distance = self._calculate_distance(
            origin_coords[0], origin_coords[1],
            dest_coords[0], dest_coords[1]
        )
        
        # Determine current progress based on shipment status and timing
        now = datetime.utcnow()
        if shipment.status == 'scheduled':
            progress = 0.0
            current_lat, current_lon = origin_coords
            status = 'scheduled'
        else:  # in_transit
            # Calculate progress based on time elapsed
            if shipment.actual_pickup:
                elapsed = (now - shipment.actual_pickup).total_seconds() / 3600
                total_time = (shipment.estimated_delivery - shipment.actual_pickup).total_seconds() / 3600
                progress = min(0.95, elapsed / total_time) if total_time > 0 else 0.5
            else:
                progress = 0.3  # Default to 30% if no pickup time
            
            # Interpolate position
            current_lat = origin_coords[0] + (dest_coords[0] - origin_coords[0]) * progress
            current_lon = origin_coords[1] + (dest_coords[1] - origin_coords[1]) * progress
            status = 'in_transit'
        
        distance_traveled = total_distance * progress
        distance_remaining = total_distance * (1 - progress)
        
        # Create location record
        location = ShipmentLocation(
            shipment_id=shipment.shipment_id,
            latitude=current_lat,
            longitude=current_lon,
            location_name=self._get_nearest_city(current_lat, current_lon),
            distance_traveled_miles=distance_traveled,
            distance_remaining_miles=distance_remaining,
            progress_percentage=progress * 100,
            status=status,
            estimated_arrival=shipment.estimated_delivery,
            speed_mph=random.uniform(45, 65) if status == 'in_transit' else 0,
            heading=self._calculate_heading(origin_coords, dest_coords),
            is_delayed=(shipment.status == 'delayed' or shipment.estimated_delivery < now)
        )
        
        self.tracking_session.add(location)
        
        # Create initial tracking event
        event = TrackingEvent(
            shipment_id=shipment.shipment_id,
            event_type='pickup' if shipment.actual_pickup else 'scheduled',
            event_code='PKP' if shipment.actual_pickup else 'SCH',
            location=shipment.origin,
            latitude=origin_coords[0],
            longitude=origin_coords[1],
            facility_type='warehouse',
            description=f"Shipment {'picked up from' if shipment.actual_pickup else 'scheduled at'} {shipment.origin}",
            occurred_at=shipment.actual_pickup or shipment.scheduled_pickup
        )
        
        self.tracking_session.add(event)
        
        # Create route segment
        segment = RouteSegment(
            shipment_id=shipment.shipment_id,
            segment_number=1,
            from_location=shipment.origin,
            to_location=shipment.destination,
            from_latitude=origin_coords[0],
            from_longitude=origin_coords[1],
            to_latitude=dest_coords[0],
            to_longitude=dest_coords[1],
            distance_miles=total_distance,
            estimated_duration_hours=(shipment.estimated_delivery - (shipment.actual_pickup or shipment.scheduled_pickup)).total_seconds() / 3600,
            mode='truck',
            carrier=shipment.carrier,
            status='in_progress' if status == 'in_transit' else 'planned',
            started_at=shipment.actual_pickup
        )
        
        self.tracking_session.add(segment)
    
    def get_all_tracked_shipments(self, status_filter: Optional[str] = None) -> List[Dict]:
        """Get all tracked shipments with current location."""
        query = self.tracking_session.query(ShipmentLocation)
        
        if status_filter:
            query = query.filter(ShipmentLocation.status == status_filter)
        
        # Get latest location for each shipment
        locations = query.order_by(ShipmentLocation.recorded_at.desc()).all()
        
        # Group by shipment_id and take latest
        shipment_map = {}
        for loc in locations:
            if loc.shipment_id not in shipment_map:
                shipment_map[loc.shipment_id] = loc
        
        result = []
        for shipment_id, location in shipment_map.items():
            # Get shipment details from TMS
            shipment = self.tms_session.query(Shipment).filter(
                Shipment.shipment_id == shipment_id
            ).first()
            
            if shipment:
                result.append({
                    'shipment_id': shipment.shipment_id,
                    'order_id': shipment.order_id,
                    'carrier': shipment.carrier,
                    'tracking_number': shipment.tracking_number,
                    'origin': shipment.origin,
                    'destination': shipment.destination,
                    'status': location.status,
                    'current_location': {
                        'latitude': location.latitude,
                        'longitude': location.longitude,
                        'name': location.location_name
                    },
                    'progress': {
                        'percentage': round(location.progress_percentage, 1),
                        'distance_traveled': round(location.distance_traveled_miles, 1),
                        'distance_remaining': round(location.distance_remaining_miles, 1)
                    },
                    'timing': {
                        'scheduled_pickup': shipment.scheduled_pickup.isoformat(),
                        'actual_pickup': shipment.actual_pickup.isoformat() if shipment.actual_pickup else None,
                        'estimated_delivery': location.estimated_arrival.isoformat(),
                        'is_delayed': location.is_delayed
                    },
                    'speed_mph': location.speed_mph,
                    'heading': location.heading,
                    'last_updated': location.recorded_at.isoformat()
                })
        
        return result
    
    def get_shipment_details(self, shipment_id: str) -> Optional[Dict]:
        """Get detailed tracking information for a specific shipment."""
        # Get latest location
        location = self.tracking_session.query(ShipmentLocation).filter(
            ShipmentLocation.shipment_id == shipment_id
        ).order_by(ShipmentLocation.recorded_at.desc()).first()
        
        if not location:
            return None
        
        # Get shipment from TMS
        shipment = self.tms_session.query(Shipment).filter(
            Shipment.shipment_id == shipment_id
        ).first()
        
        if not shipment:
            return None
        
        # Get tracking events
        events = self.tracking_session.query(TrackingEvent).filter(
            TrackingEvent.shipment_id == shipment_id
        ).order_by(TrackingEvent.occurred_at.desc()).all()
        
        # Get route segments
        segments = self.tracking_session.query(RouteSegment).filter(
            RouteSegment.shipment_id == shipment_id
        ).order_by(RouteSegment.segment_number).all()
        
        # Get ETA updates
        eta_updates = self.tracking_session.query(ETAUpdate).filter(
            ETAUpdate.shipment_id == shipment_id
        ).order_by(ETAUpdate.updated_at.desc()).limit(5).all()
        
        return {
            'shipment': {
                'shipment_id': shipment.shipment_id,
                'order_id': shipment.order_id,
                'carrier': shipment.carrier,
                'tracking_number': shipment.tracking_number,
                'origin': shipment.origin,
                'destination': shipment.destination,
                'weight_lbs': shipment.weight_lbs,
                'cost': shipment.cost
            },
            'current_location': {
                'latitude': location.latitude,
                'longitude': location.longitude,
                'name': location.location_name,
                'status': location.status,
                'speed_mph': location.speed_mph,
                'heading': location.heading,
                'last_updated': location.recorded_at.isoformat()
            },
            'progress': {
                'percentage': round(location.progress_percentage, 1),
                'distance_traveled': round(location.distance_traveled_miles, 1),
                'distance_remaining': round(location.distance_remaining_miles, 1)
            },
            'timing': {
                'scheduled_pickup': shipment.scheduled_pickup.isoformat(),
                'actual_pickup': shipment.actual_pickup.isoformat() if shipment.actual_pickup else None,
                'estimated_delivery': location.estimated_arrival.isoformat(),
                'actual_delivery': shipment.actual_delivery.isoformat() if shipment.actual_delivery else None,
                'is_delayed': location.is_delayed,
                'delay_reason': location.delay_reason
            },
            'events': [{
                'event_type': e.event_type,
                'event_code': e.event_code,
                'location': e.location,
                'description': e.description,
                'occurred_at': e.occurred_at.isoformat()
            } for e in events],
            'route': [{
                'segment_number': s.segment_number,
                'from': s.from_location,
                'to': s.to_location,
                'distance_miles': s.distance_miles,
                'status': s.status,
                'carrier': s.carrier
            } for s in segments],
            'eta_history': [{
                'previous_eta': e.previous_eta.isoformat() if e.previous_eta else None,
                'new_eta': e.new_eta.isoformat(),
                'change_hours': e.change_hours,
                'reason': e.reason,
                'updated_at': e.updated_at.isoformat()
            } for e in eta_updates]
        }
    
    def update_locations(self) -> Dict:
        """Simulate location updates for all in-transit shipments."""
        in_transit = self.tracking_session.query(ShipmentLocation).filter(
            ShipmentLocation.status.in_(['in_transit', 'out_for_delivery'])
        ).all()
        
        updated_count = 0
        for location in in_transit:
            # Get destination
            shipment = self.tms_session.query(Shipment).filter(
                Shipment.shipment_id == location.shipment_id
            ).first()
            
            if shipment:
                dest_coords = self._get_location_coords(shipment.destination)
                
                # Move shipment slightly towards destination
                progress_increment = random.uniform(0.01, 0.03)  # 1-3% progress
                new_progress = min(0.99, location.progress_percentage / 100 + progress_increment)
                
                # Get route segment
                segment = self.tracking_session.query(RouteSegment).filter(
                    RouteSegment.shipment_id == location.shipment_id
                ).first()
                
                if segment:
                    # Calculate new position
                    new_lat = segment.from_latitude + (segment.to_latitude - segment.from_latitude) * new_progress
                    new_lon = segment.from_longitude + (segment.to_longitude - segment.from_longitude) * new_progress
                    
                    # Update location
                    location.latitude = new_lat
                    location.longitude = new_lon
                    location.progress_percentage = new_progress * 100
                    location.distance_traveled_miles = segment.distance_miles * new_progress
                    location.distance_remaining_miles = segment.distance_miles * (1 - new_progress)
                    location.location_name = self._get_nearest_city(new_lat, new_lon)
                    location.recorded_at = datetime.utcnow()
                    location.speed_mph = random.uniform(45, 65)
                    
                    # Check if approaching delivery
                    if new_progress > 0.9:
                        location.status = 'out_for_delivery'
                    
                    updated_count += 1
        
        self.tracking_session.commit()
        
        return {
            'updated': updated_count,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _get_location_coords(self, location_name: str) -> Tuple[float, float]:
        """Get coordinates for a location name."""
        # Try to find exact match
        for loc, coords in self.LOCATIONS.items():
            if location_name in loc or loc in location_name:
                return coords
        
        # Return random location if not found
        return random.choice(list(self.LOCATIONS.values()))
    
    def _get_nearest_city(self, lat: float, lon: float) -> str:
        """Get nearest city name from coordinates."""
        min_distance = float('inf')
        nearest_city = "Unknown Location"
        
        for city, (city_lat, city_lon) in self.LOCATIONS.items():
            distance = self._calculate_distance(lat, lon, city_lat, city_lon)
            if distance < min_distance:
                min_distance = distance
                nearest_city = city
        
        return nearest_city
    
    def _calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate distance between two coordinates in kilometers using Haversine formula."""
        # Validate coordinates
        if not (-90 <= lat1 <= 90) or not (-90 <= lat2 <= 90):
            raise ValueError(f"Latitude must be between -90 and 90: lat1={lat1}, lat2={lat2}")
        if not (-180 <= lon1 <= 180) or not (-180 <= lon2 <= 180):
            raise ValueError(f"Longitude must be between -180 and 180: lon1={lon1}, lon2={lon2}")
        
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = math.sin(delta_lat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def _calculate_heading(self, origin: Tuple[float, float], dest: Tuple[float, float]) -> str:
        """Calculate compass heading from origin to destination."""
        lat1, lon1 = origin
        lat2, lon2 = dest
        
        delta_lon = lon2 - lon1
        
        x = math.cos(math.radians(lat2)) * math.sin(math.radians(delta_lon))
        y = math.cos(math.radians(lat1)) * math.sin(math.radians(lat2)) - \
            math.sin(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.cos(math.radians(delta_lon))
        
        angle = math.degrees(math.atan2(x, y))
        angle = (angle + 360) % 360
        
        # Convert to compass direction
        directions = ['N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW']
        index = round(angle / 45) % 8
        return directions[index]
    
    def get_tracking_stats(self) -> Dict:
        """Get summary statistics for tracking."""
        total = self.tracking_session.query(ShipmentLocation).count()
        in_transit = self.tracking_session.query(ShipmentLocation).filter(
            ShipmentLocation.status == 'in_transit'
        ).count()
        out_for_delivery = self.tracking_session.query(ShipmentLocation).filter(
            ShipmentLocation.status == 'out_for_delivery'
        ).count()
        delayed = self.tracking_session.query(ShipmentLocation).filter(
            ShipmentLocation.is_delayed == True
        ).count()
        
        return {
            'total_tracked': total,
            'in_transit': in_transit,
            'out_for_delivery': out_for_delivery,
            'delayed': delayed,
            'on_time': total - delayed
        }
    
    def close(self):
        """Close database sessions."""
        self.tracking_session.close()
        self.tms_session.close()
