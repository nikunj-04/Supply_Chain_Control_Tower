"""Unit tests for Journey Service - Testing cross-system orchestration, timeline correlation, and metrics accuracy."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from services.journey_service import JourneyService
from models.oms_models import Order
from models.wms_models import PickingTask
from models.tms_models import Shipment
from models.tracking_models import ShipmentLocation, TrackingEvent
from models.billing_models import Invoice
from models.returns_models import Return


class TestJourneyService:
    """Test suite for Journey Service focusing on cross-system data correlation and workflow sequences."""
    
    @pytest.fixture
    def mock_sessions(self):
        """Create mock database sessions for all systems."""
        return {
            'oms': Mock(),
            'wms': Mock(),
            'tms': Mock(),
            'tracking': Mock(),
            'billing': Mock(),
            'returns': Mock()
        }
    
    @pytest.fixture
    def journey_service(self, mock_sessions):
        """Create journey service with mocked sessions."""
        with patch('services.journey_service.get_oms_session', return_value=mock_sessions['oms']), \
             patch('services.journey_service.get_wms_session', return_value=mock_sessions['wms']), \
             patch('services.journey_service.get_tms_session', return_value=mock_sessions['tms']), \
             patch('services.journey_service.get_tracking_session', return_value=mock_sessions['tracking']), \
             patch('services.journey_service.get_billing_session', return_value=mock_sessions['billing']), \
             patch('services.journey_service.get_returns_session', return_value=mock_sessions['returns']):
            service = JourneyService()
            service.oms_session = mock_sessions['oms']
            service.wms_session = mock_sessions['wms']
            service.tms_session = mock_sessions['tms']
            service.tracking_session = mock_sessions['tracking']
            service.billing_session = mock_sessions['billing']
            service.returns_session = mock_sessions['returns']
            return service
    
    def test_order_age_calculation_accuracy(self, journey_service, mock_sessions):
        """Test that order age is correctly calculated from order date to current time."""
        order_date = datetime.utcnow() - timedelta(hours=48)
        
        mock_order = Mock(spec=Order)
        mock_order.order_id = "ORD-001"
        mock_order.order_date = order_date
        mock_order.customer_name = "Test Customer"
        mock_order.status = "shipped"
        mock_order.total_value = 1000.0
        mock_order.total_items = 5
        
        mock_query = Mock()
        mock_query.filter_by.return_value.first.return_value = mock_order
        mock_sessions['oms'].query.return_value = mock_query
        
        # Mock other sessions to return empty
        for session_name in ['wms', 'tms', 'tracking', 'billing', 'returns']:
            empty_query = Mock()
            empty_query.filter.return_value.first.return_value = None
            empty_query.filter.return_value.all.return_value = []
            empty_query.filter.return_value.order_by.return_value.all.return_value = []
            mock_sessions[session_name].query.return_value = empty_query
        
        metrics = journey_service._calculate_journey_metrics(mock_order)
        
        # Order age should be approximately 48 hours
        assert 47 <= metrics['order_age_hours'] <= 49, \
            f"Order age should be ~48 hours, got {metrics['order_age_hours']}"
    
    def test_transit_time_never_exceeds_order_age(self, journey_service, mock_sessions):
        """Test critical business rule: Transit Time ≤ Order Age."""
        order_date = datetime.utcnow() - timedelta(hours=30)
        pickup_date = order_date + timedelta(hours=5)  # Picked up 5 hours after order
        
        mock_order = Mock(spec=Order)
        mock_order.order_id = "ORD-001"
        mock_order.order_date = order_date
        mock_order.customer_name = "Test Customer"
        mock_order.status = "shipped"
        mock_order.total_value = 1000.0
        mock_order.total_items = 5
        
        mock_shipment = Mock(spec=Shipment)
        mock_shipment.order_id = "ORD-001"
        mock_shipment.shipment_id = "SHIP-001"
        mock_shipment.actual_pickup = pickup_date
        mock_shipment.actual_delivery = None
        
        mock_sessions['oms'].query.return_value.filter_by.return_value.first.return_value = mock_order
        mock_sessions['tms'].query.return_value.filter.return_value.first.return_value = mock_shipment
        
        # Mock other sessions
        for session_name in ['wms', 'tracking', 'billing', 'returns']:
            empty_query = Mock()
            empty_query.filter.return_value.first.return_value = None
            empty_query.filter.return_value.all.return_value = []
            empty_query.filter.return_value.order_by.return_value.all.return_value = []
            mock_sessions[session_name].query.return_value = empty_query
        
        metrics = journey_service._calculate_journey_metrics(mock_order)
        
        # Transit time must be <= order age
        if metrics['transit_time_hours'] is not None:
            assert metrics['transit_time_hours'] <= metrics['order_age_hours'], \
                f"Transit time ({metrics['transit_time_hours']}h) cannot exceed order age ({metrics['order_age_hours']}h)"
    
    def test_journey_stage_sequence_validation(self, journey_service, mock_sessions):
        """Test that journey stages follow logical sequence: Order -> Warehouse -> Transit -> Delivery -> Billing."""
        order_date = datetime.utcnow() - timedelta(days=2)
        
        # Create complete journey data
        mock_order = Mock(spec=Order)
        mock_order.order_id = "ORD-001"
        mock_order.order_date = order_date
        mock_order.customer_name = "Test Customer"
        mock_order.status = "delivered"
        mock_order.total_value = 1000.0
        mock_order.total_items = 3
        
        # Warehouse stage
        mock_picking = Mock(spec=PickingTask)
        mock_picking.order_id = "ORD-001"
        mock_picking.created_at = order_date + timedelta(hours=1)
        mock_picking.status = "completed"
        mock_picking.sku = "SKU-001"
        mock_picking.quantity = 3
        mock_picking.location = "A-01"
        mock_picking.assigned_to = "Worker-1"
        
        # Transit stage
        mock_shipment = Mock(spec=Shipment)
        mock_shipment.order_id = "ORD-001"
        mock_shipment.shipment_id = "SHIP-001"
        mock_shipment.actual_pickup = order_date + timedelta(hours=6)
        mock_shipment.actual_delivery = order_date + timedelta(days=1, hours=12)
        mock_shipment.estimated_delivery = order_date + timedelta(days=2)
        
        # Billing stage
        mock_invoice = Mock(spec=Invoice)
        mock_invoice.order_id = "ORD-001"
        mock_invoice.invoice_id = "INV-001"
        mock_invoice.invoice_date = order_date + timedelta(days=1, hours=13)
        mock_invoice.total = 1000.0
        mock_invoice.status = "paid"
        mock_invoice.due_date = order_date + timedelta(days=30)
        
        # Setup mock queries
        mock_sessions['oms'].query.return_value.filter_by.return_value.first.return_value = mock_order
        mock_sessions['wms'].query.return_value.filter.return_value.all.return_value = [mock_picking]
        mock_sessions['tms'].query.return_value.filter.return_value.first.return_value = mock_shipment
        mock_sessions['billing'].query.return_value.filter.return_value.first.return_value = mock_invoice
        
        # Mock tracking and returns
        mock_sessions['tracking'].query.return_value.filter.return_value.first.return_value = None
        mock_sessions['tracking'].query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_sessions['returns'].query.return_value.filter.return_value.all.return_value = []
        
        stages = journey_service._build_journey_stages(mock_order)
        
        # Extract stage names in order
        stage_names = [s['stage'] for s in stages]
        
        # Verify order_placed is first
        assert stage_names[0] == 'order_placed', "First stage should be order_placed"
        
        # Verify warehouse comes before transit
        if 'warehouse_processing' in stage_names and 'in_transit' in stage_names:
            assert stage_names.index('warehouse_processing') < stage_names.index('in_transit'), \
                "Warehouse processing should occur before transit"
        
        # Verify billing comes last (if present)
        if 'billing' in stage_names:
            assert stage_names[-1] == 'billing' or stage_names[-2] == 'billing', \
                "Billing should be one of the final stages"
    
    def test_timeline_chronological_ordering(self, journey_service, mock_sessions):
        """Test that timeline events from all systems are correctly ordered chronologically."""
        base_date = datetime.utcnow() - timedelta(days=1)
        
        mock_order = Mock(spec=Order)
        mock_order.order_id = "ORD-001"
        mock_order.order_date = base_date
        mock_order.customer_name = "Test"
        mock_order.total_items = 2
        mock_order.total_value = 500.0
        
        # Events from different systems at different times
        mock_picking = Mock(spec=PickingTask)
        mock_picking.order_id = "ORD-001"
        mock_picking.created_at = base_date + timedelta(hours=2)
        mock_picking.status = "completed"
        mock_picking.sku = "SKU-001"
        mock_picking.quantity = 2
        mock_picking.location = "A-01"
        mock_picking.assigned_to = "Worker-1"
        
        mock_event = Mock(spec=TrackingEvent)
        mock_event.order_id = "ORD-001"
        mock_event.timestamp = base_date + timedelta(hours=8)
        mock_event.event_type = "checkpoint"
        mock_event.location = "Phoenix"
        
        mock_invoice = Mock(spec=Invoice)
        mock_invoice.order_id = "ORD-001"
        mock_invoice.invoice_date = base_date + timedelta(hours=25)
        mock_invoice.invoice_id = "INV-001"
        mock_invoice.total = 500.0
        mock_invoice.status = "pending"
        
        # Setup mocks
        mock_sessions['oms'].query.return_value.filter_by.return_value.first.return_value = mock_order
        mock_sessions['wms'].query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_picking]
        mock_sessions['tracking'].query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_event]
        mock_sessions['billing'].query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_sessions['tms'].query.return_value.filter.return_value.first.return_value = None
        mock_sessions['returns'].query.return_value.filter.return_value.all.return_value = []
        
        timeline = journey_service._build_timeline(mock_order)
        
        # Verify chronological order
        timestamps = [datetime.fromisoformat(e['timestamp']) for e in timeline]
        for i in range(len(timestamps) - 1):
            assert timestamps[i] <= timestamps[i + 1], \
                f"Timeline event {i} should occur before or at same time as event {i+1}"
    
    def test_cross_system_data_correlation(self, journey_service, mock_sessions):
        """Test that data from different systems is correctly correlated by order_id."""
        order_id = "ORD-001"
        
        # Data from each system with same order_id
        mock_order = Mock(spec=Order)
        mock_order.order_id = order_id
        mock_order.order_date = datetime.utcnow() - timedelta(hours=24)
        mock_order.customer_name = "Test"
        mock_order.status = "shipped"
        mock_order.total_value = 1000.0
        mock_order.total_items = 5
        
        mock_picking = Mock(spec=PickingTask)
        mock_picking.order_id = order_id
        mock_picking.created_at = datetime.utcnow() - timedelta(hours=20)
        mock_picking.status = "completed"
        mock_picking.sku = "SKU-001"
        mock_picking.quantity = 5
        mock_picking.location = "A-01"
        mock_picking.assigned_to = "Worker-1"
        
        mock_shipment = Mock(spec=Shipment)
        mock_shipment.order_id = order_id
        mock_shipment.shipment_id = "SHIP-001"
        mock_shipment.actual_pickup = datetime.utcnow() - timedelta(hours=18)
        mock_shipment.actual_delivery = None
        mock_shipment.estimated_delivery = datetime.utcnow() + timedelta(hours=6)
        mock_shipment.carrier = "FedEx"
        mock_shipment.origin = "Warehouse A"
        mock_shipment.destination = "Customer"
        
        mock_invoice = Mock(spec=Invoice)
        mock_invoice.order_id = order_id
        mock_invoice.invoice_id = "INV-001"
        mock_invoice.total = 1000.0
        mock_invoice.status = "pending"
        mock_invoice.invoice_date = datetime.utcnow() - timedelta(hours=12)
        mock_invoice.due_date = datetime.utcnow() + timedelta(days=30)
        
        # Setup mocks with proper chaining
        # OMS mock - service uses .filter() not .filter_by()
        mock_oms_filter_result = Mock()
        mock_oms_filter_result.first.return_value = mock_order
        mock_sessions['oms'].query.return_value.filter.return_value = mock_oms_filter_result
        
        # WMS mock - need proper chain for both .filter().all() AND .filter().order_by().all()
        mock_wms_order_by_result = Mock()
        mock_wms_order_by_result.all.return_value = [mock_picking]
        mock_wms_filter_result = Mock()
        mock_wms_filter_result.all.return_value = [mock_picking]  # For .filter().all()
        mock_wms_filter_result.order_by.return_value = mock_wms_order_by_result  # For .filter().order_by().all()
        mock_sessions['wms'].query.return_value.filter.return_value = mock_wms_filter_result
        
        mock_sessions['tms'].query.return_value.filter.return_value.first.return_value = mock_shipment
        mock_sessions['billing'].query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_sessions['tracking'].query.return_value.filter.return_value.first.return_value = None
        mock_sessions['tracking'].query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_sessions['returns'].query.return_value.filter.return_value.all.return_value = []
        
        journey = journey_service.get_order_journey(order_id)
        
        # Verify order_id is consistent
        assert journey['order_id'] == order_id
        
        # Verify data from multiple systems is present
        assert journey['stages'] is not None
        assert len(journey['timeline']) >= 2  # At least order + picking events
    
    def test_journey_stats_aggregation(self, journey_service, mock_sessions):
        """Test that journey statistics correctly aggregate data across all orders."""
        # Create mock orders with different statuses
        orders = [
            Mock(spec=Order, status='pending'),
            Mock(spec=Order, status='pending'),
            Mock(spec=Order, status='processing'),
            Mock(spec=Order, status='processing'),
            Mock(spec=Order, status='processing'),
            Mock(spec=Order, status='shipped'),
            Mock(spec=Order, status='shipped'),
            Mock(spec=Order, status='delivered'),
            Mock(spec=Order, status='delivered'),
            Mock(spec=Order, status='delivered'),
        ]
        
        # Mock count queries
        mock_sessions['oms'].query.return_value.count.return_value = len(orders)
        mock_sessions['oms'].query.return_value.filter.return_value.count.side_effect = [
            2,  # pending
            3,  # processing
            2,  # shipped
            3   # delivered
        ]
        
        # Mock active shipments
        mock_sessions['tms'].query.return_value.filter.return_value.count.return_value = 5
        
        stats = journey_service.get_journey_stats()
        
        assert stats['total_orders'] == 10
        assert stats['pending'] == 2
        assert stats['processing'] == 3
        assert stats['shipped'] == 2
        assert stats['delivered'] == 3
        assert stats['active_shipments'] == 5
    
    def test_stage_status_consistency(self, journey_service, mock_sessions):
        """Test that stage status (completed/in_progress/pending) is consistent with order status."""
        mock_order = Mock(spec=Order)
        mock_order.order_id = "ORD-001"
        mock_order.order_date = datetime.utcnow() - timedelta(hours=10)
        mock_order.customer_name = "Test"
        mock_order.status = "processing"  # Order is in processing
        mock_order.total_value = 500.0
        mock_order.total_items = 2
        
        mock_picking = Mock(spec=PickingTask)
        mock_picking.order_id = "ORD-001"
        mock_picking.created_at = datetime.utcnow() - timedelta(hours=2)
        mock_picking.status = "in_progress"
        mock_picking.sku = "SKU-001"
        mock_picking.quantity = 2
        mock_picking.location = "A-01"
        mock_picking.assigned_to = "Worker-1"
        
        mock_sessions['oms'].query.return_value.filter_by.return_value.first.return_value = mock_order
        mock_sessions['wms'].query.return_value.filter.return_value.all.return_value = [mock_picking]
        mock_sessions['tms'].query.return_value.filter.return_value.first.return_value = None
        mock_sessions['tracking'].query.return_value.filter.return_value.first.return_value = None
        mock_sessions['tracking'].query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_sessions['billing'].query.return_value.filter.return_value.first.return_value = None
        mock_sessions['returns'].query.return_value.filter.return_value.all.return_value = []
        
        stages = journey_service._build_journey_stages(mock_order)
        
        # Order placed should be completed
        order_stage = next((s for s in stages if s['stage'] == 'order_placed'), None)
        assert order_stage is not None
        assert order_stage['status'] == 'completed'
        
        # Warehouse should be in_progress since order status is processing
        warehouse_stage = next((s for s in stages if s['stage'] == 'warehouse_processing'), None)
        if warehouse_stage:
            assert warehouse_stage['status'] == 'in_progress'
    
    def test_metrics_systems_touched_count(self, journey_service, mock_sessions):
        """Test that metrics correctly count unique systems involved in journey."""
        mock_order = Mock(spec=Order)
        mock_order.order_id = "ORD-001"
        mock_order.order_date = datetime.utcnow() - timedelta(hours=24)
        mock_order.customer_name = "Test"
        mock_order.total_items = 2
        mock_order.total_value = 500.0
        
        # Events from 3 systems: OMS, WMS, Billing
        mock_picking = Mock(spec=PickingTask)
        mock_picking.order_id = "ORD-001"
        mock_picking.created_at = datetime.utcnow() - timedelta(hours=20)
        mock_picking.status = "completed"
        mock_picking.sku = "SKU-001"
        mock_picking.quantity = 2
        mock_picking.location = "A-01"
        mock_picking.assigned_to = "Worker-1"
        
        mock_invoice = Mock(spec=Invoice)
        mock_invoice.order_id = "ORD-001"
        mock_invoice.invoice_id = "INV-001"
        mock_invoice.invoice_date = datetime.utcnow() - timedelta(hours=12)
        mock_invoice.total = 500.0
        mock_invoice.status = "pending"
        
        mock_sessions['oms'].query.return_value.filter_by.return_value.first.return_value = mock_order
        mock_sessions['wms'].query.return_value.filter.return_value.order_by.return_value.all.return_value = [mock_picking]
        mock_sessions['billing'].query.return_value.filter.return_value.first.return_value = mock_invoice
        mock_sessions['tms'].query.return_value.filter.return_value.first.return_value = None
        mock_sessions['tracking'].query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_sessions['returns'].query.return_value.filter.return_value.all.return_value = []
        
        metrics = journey_service._calculate_journey_metrics(mock_order)
        
        # Should count OMS, WMS, Billing = 3 systems
        assert metrics['systems_touched'] == 3, f"Expected 3 systems, got {metrics['systems_touched']}"
    
    def test_return_workflow_integration(self, journey_service, mock_sessions):
        """Test that returns are correctly integrated into journey when present."""
        mock_order = Mock(spec=Order)
        mock_order.order_id = "ORD-001"
        mock_order.order_date = datetime.utcnow() - timedelta(days=10)
        mock_order.customer_name = "Test"
        mock_order.status = "delivered"
        mock_order.total_value = 1000.0
        mock_order.total_items = 3
        
        # Mock return
        mock_return = Mock(spec=Return)
        mock_return.order_id = "ORD-001"
        mock_return.return_id = "RET-001"
        mock_return.return_date = datetime.utcnow() - timedelta(days=2)
        mock_return.reason = "defective"
        mock_return.status = "processed"
        mock_return.total_value = 300.0
        mock_return.quantity = 1
        
        mock_sessions['oms'].query.return_value.filter_by.return_value.first.return_value = mock_order
        mock_sessions['returns'].query.return_value.filter.return_value.all.return_value = [mock_return]
        mock_sessions['wms'].query.return_value.filter.return_value.all.return_value = []
        mock_sessions['tms'].query.return_value.filter.return_value.first.return_value = None
        mock_sessions['tracking'].query.return_value.filter.return_value.first.return_value = None
        mock_sessions['tracking'].query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_sessions['billing'].query.return_value.filter.return_value.first.return_value = None
        
        stages = journey_service._build_journey_stages(mock_order)
        
        # Verify returns stage exists
        return_stage = next((s for s in stages if s['stage'] == 'returns'), None)
        assert return_stage is not None, "Returns stage should be present when returns exist"
    
    def test_on_time_delivery_calculation(self, journey_service, mock_sessions):
        """Test on-time delivery metric calculation based on actual vs estimated delivery."""
        mock_order = Mock(spec=Order)
        mock_order.order_id = "ORD-001"
        mock_order.order_date = datetime.utcnow() - timedelta(days=3)
        mock_order.customer_name = "Test"
        mock_order.status = "delivered"
        mock_order.total_value = 500.0
        mock_order.total_items = 2
        
        # Shipment delivered early
        estimated = datetime.utcnow() - timedelta(hours=12)
        actual = datetime.utcnow() - timedelta(hours=24)
        
        mock_shipment = Mock(spec=Shipment)
        mock_shipment.order_id = "ORD-001"
        mock_shipment.shipment_id = "SHIP-001"
        mock_shipment.estimated_delivery = estimated
        mock_shipment.actual_delivery = actual
        mock_shipment.actual_pickup = datetime.utcnow() - timedelta(days=2)
        
        mock_sessions['oms'].query.return_value.filter_by.return_value.first.return_value = mock_order
        mock_sessions['tms'].query.return_value.filter.return_value.first.return_value = mock_shipment
        
        # Mock WMS to return empty list (not a Mock object)
        wms_query = Mock()
        wms_query.filter.return_value.order_by.return_value.all.return_value = []
        mock_sessions['wms'].query.return_value = wms_query
        
        mock_sessions['tracking'].query.return_value.filter.return_value.first.return_value = None
        mock_sessions['tracking'].query.return_value.filter.return_value.order_by.return_value.all.return_value = []
        mock_sessions['billing'].query.return_value.filter.return_value.first.return_value = None
        mock_sessions['returns'].query.return_value.filter.return_value.all.return_value = []
        
        metrics = journey_service._calculate_journey_metrics(mock_order)
        
        # Should be True since actual < estimated
        assert metrics['on_time_delivery'] == True, "Delivery should be marked as on-time"
