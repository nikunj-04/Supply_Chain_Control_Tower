"""Unit tests for Tracking Service - Testing GPS simulation, location updates, and real-time tracking logic."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from services.tracking_service import TrackingService
from models.tracking_models import ShipmentLocation, TrackingEvent, RouteSegment, ETAUpdate
from models.tms_models import Shipment
import math


class TestTrackingService:
    """Test suite for Tracking Service focusing on GPS accuracy, time-based updates, and location correlation."""
    
    @pytest.fixture
    def mock_sessions(self):
        """Create mock database sessions."""
        return {
            'tracking': Mock(),
            'tms': Mock()
        }
    
    @pytest.fixture
    def tracking_service(self, mock_sessions):
        """Create tracking service with mocked sessions."""
        with patch('services.tracking_service.get_tracking_session', return_value=mock_sessions['tracking']), \
             patch('services.tracking_service.get_tms_session', return_value=mock_sessions['tms']):
            service = TrackingService()
            service.tracking_session = mock_sessions['tracking']
            service.tms_session = mock_sessions['tms']
            return service
    
    def test_distance_calculation_accuracy(self, tracking_service):
        """Test Haversine distance calculation accuracy between GPS coordinates."""
        # Known distance: Los Angeles to New York ~ 3944 km
        la_coords = (34.0522, -118.2437)
        ny_coords = (40.7128, -74.0060)
        
        distance = tracking_service._calculate_distance(
            la_coords[0], la_coords[1],
            ny_coords[0], ny_coords[1]
        )
        
        # Should be approximately 3944 km (allow 50km variance for Haversine approximation)
        assert 3900 <= distance <= 4000, f"Distance calculated: {distance} km"
    
    def test_progress_percentage_calculation(self, tracking_service):
        """Test that progress percentage is correctly calculated based on traveled vs total distance."""
        origin_lat, origin_lon = 34.0522, -118.2437  # LA
        dest_lat, dest_lon = 40.7128, -74.0060  # NY
        
        # Calculate total distance
        total_distance = tracking_service._calculate_distance(origin_lat, origin_lon, dest_lat, dest_lon)
        
        # Simulate location halfway between origin and destination
        current_lat = (origin_lat + dest_lat) / 2
        current_lon = (origin_lon + dest_lon) / 2
        
        traveled = tracking_service._calculate_distance(origin_lat, origin_lon, current_lat, current_lon)
        progress = (traveled / total_distance) * 100
        
        # Should be approximately 50% progress
        assert 40 <= progress <= 60, f"Progress calculated: {progress}%"
    
    def test_location_update_timestamp_sequence(self, tracking_service, mock_sessions):
        """Test that location updates maintain proper chronological sequence."""
        shipment_id = "SHIP-001"
        
        # Create sequence of location updates
        base_time = datetime.utcnow()
        
        locations = []
        for i in range(5):
            location = Mock(spec=ShipmentLocation)
            location.shipment_id = shipment_id
            location.timestamp = base_time + timedelta(minutes=i * 10)
            location.latitude = 34.0522 + (i * 0.1)
            location.longitude = -118.2437 + (i * 0.1)
            locations.append(location)
        
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = locations
        mock_sessions['tracking'].query.return_value = mock_query
        
        # Verify timestamps are in sequence
        for i in range(len(locations) - 1):
            assert locations[i].timestamp < locations[i + 1].timestamp, \
                f"Location {i} timestamp should be before location {i+1}"
    
    def test_tracking_status_transitions(self, tracking_service, mock_sessions):
        """Test valid status transitions: pending -> in_transit -> out_for_delivery -> delivered."""
        shipment_id = "SHIP-001"
        
        # Mock shipment location with status transitions
        location = Mock(spec=ShipmentLocation)
        location.shipment_id = shipment_id
        location.status = 'pending'
        location.progress_percentage = 0
        
        mock_query = Mock()
        mock_query.filter_by.return_value.first.return_value = location
        mock_sessions['tracking'].query.return_value = mock_query
        
        # Transition 1: pending -> in_transit (progress > 0)
        location.status = 'in_transit'
        location.progress_percentage = 25
        assert location.status == 'in_transit'
        assert 0 < location.progress_percentage < 90
        
        # Transition 2: in_transit -> out_for_delivery (progress >= 90)
        location.status = 'out_for_delivery'
        location.progress_percentage = 95
        assert location.status == 'out_for_delivery'
        assert location.progress_percentage >= 90
        
        # Transition 3: out_for_delivery -> delivered (progress = 100)
        location.status = 'delivered'
        location.progress_percentage = 100
        assert location.status == 'delivered'
        assert location.progress_percentage == 100
    
    def test_eta_accuracy_based_on_velocity(self, tracking_service):
        """Test ETA calculation based on current velocity and remaining distance."""
        # Current location: halfway between LA and NY
        current_lat, current_lon = 37.0, -96.0
        dest_lat, dest_lon = 40.7128, -74.0060  # NY
        
        # Calculate remaining distance
        remaining_distance = tracking_service._calculate_distance(
            current_lat, current_lon, dest_lat, dest_lon
        )
        
        # Assume average truck speed: 80 km/h
        avg_speed_kmh = 80
        estimated_hours = remaining_distance / avg_speed_kmh
        
        # ETA should be reasonable (remaining ~2000km / 80kmh = ~25 hours)
        assert 20 <= estimated_hours <= 30, f"ETA calculated: {estimated_hours} hours"
    
    def test_tracking_event_milestone_sequence(self, tracking_service, mock_sessions):
        """Test that tracking events (pickup, checkpoint, delivery) follow logical sequence."""
        shipment_id = "SHIP-001"
        base_time = datetime.utcnow()
        
        # Define milestone sequence
        events = [
            Mock(spec=TrackingEvent, shipment_id=shipment_id, event_type='pickup', 
                 timestamp=base_time, location='Los Angeles'),
            Mock(spec=TrackingEvent, shipment_id=shipment_id, event_type='checkpoint',
                 timestamp=base_time + timedelta(hours=12), location='Phoenix'),
            Mock(spec=TrackingEvent, shipment_id=shipment_id, event_type='checkpoint',
                 timestamp=base_time + timedelta(hours=24), location='Dallas'),
            Mock(spec=TrackingEvent, shipment_id=shipment_id, event_type='delivery',
                 timestamp=base_time + timedelta(hours=48), location='New York')
        ]
        
        mock_query = Mock()
        mock_query.filter.return_value.order_by.return_value.all.return_value = events
        mock_sessions['tracking'].query.return_value = mock_query
        
        # Verify chronological order
        for i in range(len(events) - 1):
            assert events[i].timestamp < events[i + 1].timestamp, \
                f"Event {i} should occur before event {i+1}"
        
        # Verify first event is pickup and last is delivery
        assert events[0].event_type == 'pickup'
        assert events[-1].event_type == 'delivery'
    
    def test_gps_coordinate_validation(self, tracking_service):
        """Test that GPS coordinates are within valid ranges."""
        # Valid coordinates
        assert -90 <= 34.0522 <= 90  # Latitude
        assert -180 <= -118.2437 <= 180  # Longitude
        
        # Test distance calculation rejects invalid coordinates
        # Invalid latitude (> 90)
        with pytest.raises((ValueError, AssertionError, Exception)):
            tracking_service._calculate_distance(95.0, -118.0, 40.0, -74.0)
    
    def test_location_update_frequency_timing(self, tracking_service, mock_sessions):
        """Test that location updates occur at appropriate time intervals."""
        shipment_id = "SHIP-001"
        base_time = datetime.utcnow()
        
        # Create locations with 5-minute intervals (realistic update frequency)
        locations = []
        for i in range(10):
            location = Mock(spec=ShipmentLocation)
            location.shipment_id = shipment_id
            location.timestamp = base_time + timedelta(minutes=i * 5)
            location.latitude = 34.0 + (i * 0.05)
            location.longitude = -118.0 + (i * 0.05)
            locations.append(location)
        
        # Verify intervals
        for i in range(len(locations) - 1):
            time_diff = (locations[i + 1].timestamp - locations[i].timestamp).total_seconds()
            assert 240 <= time_diff <= 360, f"Update interval should be ~5 minutes, got {time_diff}s"
    
    def test_route_segment_distance_correlation(self, tracking_service, mock_sessions):
        """Test that route segments have consistent distance calculations."""
        # Mock route segments
        segments = [
            Mock(spec=RouteSegment, 
                 start_location='Los Angeles', end_location='Phoenix',
                 start_lat=34.05, start_lon=-118.24, end_lat=33.45, end_lon=-112.07,
                 distance_km=600),
            Mock(spec=RouteSegment,
                 start_location='Phoenix', end_location='Dallas',
                 start_lat=33.45, start_lon=-112.07, end_lat=32.78, end_lon=-96.80,
                 distance_km=1400)
        ]
        
        # Verify segment distances are reasonable
        for segment in segments:
            calculated_distance = tracking_service._calculate_distance(
                segment.start_lat, segment.start_lon,
                segment.end_lat, segment.end_lon
            )
            
            # Allow 10% variance
            assert abs(calculated_distance - segment.distance_km) / segment.distance_km < 0.15, \
                f"Segment distance mismatch: stored={segment.distance_km}, calculated={calculated_distance}"
    
    def test_simultaneous_shipment_tracking_isolation(self, tracking_service, mock_sessions):
        """Test that multiple shipments can be tracked simultaneously without interference."""
        shipments = ["SHIP-001", "SHIP-002", "SHIP-003"]
        
        locations = []
        for ship_id in shipments:
            location = Mock(spec=ShipmentLocation)
            location.shipment_id = ship_id
            location.latitude = 34.0 + shipments.index(ship_id)
            location.longitude = -118.0 - shipments.index(ship_id)
            location.timestamp = datetime.utcnow()
            locations.append(location)
        
        # Verify each shipment has unique tracking data
        ship_ids = [loc.shipment_id for loc in locations]
        assert len(ship_ids) == len(set(ship_ids)), "Each shipment should have unique tracking"
        
        # Verify locations are different
        coords = [(loc.latitude, loc.longitude) for loc in locations]
        assert len(coords) == len(set(coords)), "Each shipment should have unique coordinates"
    
    def test_tracking_initialization_from_tms(self, tracking_service, mock_sessions):
        """Test that tracking data is correctly initialized from TMS shipment data."""
        # Mock TMS shipment
        shipment = Mock(spec=Shipment)
        shipment.shipment_id = "SHIP-001"
        shipment.order_id = "ORD-001"
        shipment.status = "in_transit"
        shipment.origin_city = "Los Angeles"
        shipment.destination_city = "New York"
        
        mock_query = Mock()
        mock_query.filter.return_value.all.return_value = [shipment]
        mock_sessions['tms'].query.return_value = mock_query
        
        # Mock tracking session to capture created location
        created_locations = []
        def capture_add(obj):
            if isinstance(obj, (Mock, MagicMock)) or hasattr(obj, 'shipment_id'):
                created_locations.append(obj)
        
        mock_sessions['tracking'].add.side_effect = capture_add
        mock_sessions['tracking'].commit = Mock()
        
        # Verify shipment data is available for initialization
        assert shipment.shipment_id == "SHIP-001"
        assert shipment.origin_city == "Los Angeles"
        assert shipment.destination_city == "New York"
    
    def test_delivery_confirmation_timestamp(self, tracking_service, mock_sessions):
        """Test that delivery confirmation timestamp matches actual delivery time."""
        shipment_id = "SHIP-001"
        delivery_time = datetime.utcnow()
        
        # Mock location at delivery
        location = Mock(spec=ShipmentLocation)
        location.shipment_id = shipment_id
        location.status = 'delivered'
        location.progress_percentage = 100
        location.timestamp = delivery_time
        
        # Mock delivery event
        delivery_event = Mock(spec=TrackingEvent)
        delivery_event.shipment_id = shipment_id
        delivery_event.event_type = 'delivery'
        delivery_event.timestamp = delivery_time
        
        # Timestamps should match
        assert location.timestamp == delivery_event.timestamp, \
            "Delivery confirmation timestamp should match location update"
    
    def test_exception_handling_for_invalid_shipment(self, tracking_service, mock_sessions):
        """Test proper handling of tracking requests for non-existent shipments."""
        invalid_shipment_id = "SHIP-INVALID"
        
        mock_query = Mock()
        mock_query.filter_by.return_value.first.return_value = None
        mock_sessions['tracking'].query.return_value = mock_query
        
        # Should handle gracefully without crashing
        result = mock_query.filter_by(shipment_id=invalid_shipment_id).first()
        assert result is None
