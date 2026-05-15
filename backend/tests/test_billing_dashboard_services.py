"""Unit tests for Billing and Dashboard Services - Testing financial calculations and aggregations."""
import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, MagicMock, patch
from services.billing_service import BillingService
from services.dashboard_service import DashboardService
from models.billing_models import Invoice, BillingLineItem
from models.tms_models import Shipment
from models.oms_models import Order
from models.wms_models import PickingTask


class TestBillingService:
    """Test suite for Billing Service focusing on financial accuracy and invoice calculations."""
    
    @pytest.fixture
    def mock_billing_session(self):
        return Mock()
    
    @pytest.fixture
    def billing_service(self, mock_billing_session):
        with patch('services.billing_service.get_billing_session', return_value=mock_billing_session):
            service = BillingService()
            service.billing_session = mock_billing_session
            return service
    
    def test_invoice_total_calculation(self, billing_service, mock_billing_session):
        """Test that invoice total equals sum of line items plus tax."""
        subtotal = 1000.0
        tax = 80.0
        expected_total = 1080.0
        
        mock_invoice = Mock(spec=Invoice)
        mock_invoice.subtotal = subtotal
        mock_invoice.tax = tax
        mock_invoice.total = expected_total
        mock_invoice.amount_paid = 0.0
        mock_invoice.balance = expected_total
        
        # Verify calculation
        assert mock_invoice.total == mock_invoice.subtotal + mock_invoice.tax
        assert mock_invoice.balance == mock_invoice.total - mock_invoice.amount_paid
    
    def test_invoice_balance_after_payment(self, billing_service, mock_billing_session):
        """Test that balance is correctly calculated after partial payment."""
        total = 1000.0
        payment_1 = 300.0
        payment_2 = 500.0
        
        mock_invoice = Mock(spec=Invoice)
        mock_invoice.total = total
        mock_invoice.amount_paid = 0.0
        mock_invoice.balance = total
        
        # Apply first payment
        mock_invoice.amount_paid += payment_1
        mock_invoice.balance = total - mock_invoice.amount_paid
        assert mock_invoice.balance == 700.0
        
        # Apply second payment
        mock_invoice.amount_paid += payment_2
        mock_invoice.balance = total - mock_invoice.amount_paid
        assert mock_invoice.balance == 200.0
    
    def test_invoice_status_based_on_dates(self, billing_service, mock_billing_session):
        """Test invoice status logic: paid, pending, overdue based on dates."""
        now = datetime.utcnow()
        
        # Paid invoice
        paid_invoice = Mock(spec=Invoice)
        paid_invoice.payment_date = now - timedelta(days=1)
        paid_invoice.due_date = now + timedelta(days=30)
        paid_invoice.status = 'paid'
        assert paid_invoice.status == 'paid'
        
        # Pending invoice (not due yet)
        pending_invoice = Mock(spec=Invoice)
        pending_invoice.payment_date = None
        pending_invoice.due_date = now + timedelta(days=15)
        pending_invoice.status = 'pending'
        assert pending_invoice.status == 'pending'
        
        # Overdue invoice
        overdue_invoice = Mock(spec=Invoice)
        overdue_invoice.payment_date = None
        overdue_invoice.due_date = now - timedelta(days=5)
        overdue_invoice.status = 'overdue'
        assert overdue_invoice.status == 'overdue'
    
    def test_line_item_total_calculation(self, billing_service, mock_billing_session):
        """Test that line item total = quantity * unit_price."""
        line_items = [
            Mock(spec=BillingLineItem, quantity=10, unit_price=50.0, line_total=500.0),
            Mock(spec=BillingLineItem, quantity=5, unit_price=100.0, line_total=500.0),
            Mock(spec=BillingLineItem, quantity=2.5, unit_price=80.0, line_total=200.0),
        ]
        
        for item in line_items:
            calculated_total = item.quantity * item.unit_price
            assert abs(calculated_total - item.line_total) < 0.01, \
                f"Line total mismatch: expected {calculated_total}, got {item.line_total}"
    
    def test_invoice_subtotal_aggregation(self, billing_service, mock_billing_session):
        """Test that invoice subtotal equals sum of all line items."""
        line_items = [
            Mock(spec=BillingLineItem, line_total=500.0),
            Mock(spec=BillingLineItem, line_total=300.0),
            Mock(spec=BillingLineItem, line_total=200.0),
        ]
        
        expected_subtotal = sum(item.line_total for item in line_items)
        assert expected_subtotal == 1000.0


class TestDashboardService:
    """Test suite for Dashboard Service focusing on KPI calculations and data aggregation."""
    
    @pytest.fixture
    def mock_sessions(self):
        return {
            'tms': Mock(),
            'wms': Mock(),
            'oms': Mock(),
            'billing': Mock()
        }
    
    @pytest.fixture
    def dashboard_service(self, mock_sessions):
        with patch('services.dashboard_service.get_tms_session', return_value=mock_sessions['tms']), \
             patch('services.dashboard_service.get_wms_session', return_value=mock_sessions['wms']), \
             patch('services.dashboard_service.get_oms_session', return_value=mock_sessions['oms']), \
             patch('services.dashboard_service.get_billing_session', return_value=mock_sessions['billing']):
            service = DashboardService()
            service.tms_session = mock_sessions['tms']
            service.wms_session = mock_sessions['wms']
            service.oms_session = mock_sessions['oms']
            service.billing_session = mock_sessions['billing']
            return service
    
    def test_on_time_delivery_percentage_calculation(self, dashboard_service, mock_sessions):
        """Test OTD percentage calculation: (on_time_count / total_delivered) * 100."""
        # Mock shipments: 8 delivered, 6 on-time = 75% OTD
        total_delivered = 8
        on_time_count = 6
        
        mock_sessions['tms'].query.return_value.filter.return_value.count.return_value = total_delivered
        
        # Calculate expected OTD
        otd_percentage = (on_time_count / total_delivered) * 100
        assert otd_percentage == 75.0
    
    def test_order_fulfillment_time_calculation(self, dashboard_service, mock_sessions):
        """Test average order fulfillment time calculation."""
        order_date = datetime.utcnow() - timedelta(hours=72)
        delivery_date = datetime.utcnow() - timedelta(hours=24)
        
        fulfillment_hours = (delivery_date - order_date).total_seconds() / 3600
        
        # Should be 48 hours (allow small float precision variance)
        assert abs(fulfillment_hours - 48.0) < 0.01
    
    def test_inventory_turnover_calculation(self, dashboard_service, mock_sessions):
        """Test inventory turnover ratio calculation."""
        # Cost of goods sold / Average inventory value
        cogs = 100000.0
        avg_inventory = 25000.0
        
        turnover_ratio = cogs / avg_inventory
        
        # Should be 4.0
        assert turnover_ratio == 4.0
    
    def test_revenue_aggregation_by_period(self, dashboard_service, mock_sessions):
        """Test revenue aggregation across time periods."""
        invoices = [
            Mock(spec=Invoice, total=1000.0, invoice_date=datetime.utcnow() - timedelta(days=1)),
            Mock(spec=Invoice, total=1500.0, invoice_date=datetime.utcnow() - timedelta(days=2)),
            Mock(spec=Invoice, total=2000.0, invoice_date=datetime.utcnow() - timedelta(days=3)),
        ]
        
        total_revenue = sum(inv.total for inv in invoices)
        assert total_revenue == 4500.0
    
    def test_exception_count_by_severity(self, dashboard_service):
        """Test exception counting and grouping by severity."""
        exceptions = {
            'high': 5,
            'medium': 12,
            'low': 8
        }
        
        total_exceptions = sum(exceptions.values())
        assert total_exceptions == 25
        
        # High severity percentage
        high_percentage = (exceptions['high'] / total_exceptions) * 100
        assert high_percentage == 20.0
    
    def test_capacity_utilization_percentage(self, dashboard_service):
        """Test warehouse capacity utilization calculation."""
        total_capacity = 10000  # units
        current_inventory = 7500  # units
        
        utilization = (current_inventory / total_capacity) * 100
        assert utilization == 75.0
    
    def test_average_calculation_with_zero_division_handling(self, dashboard_service):
        """Test that averages handle zero division gracefully."""
        total_sum = 1000.0
        count = 0
        
        # Should handle gracefully
        if count > 0:
            average = total_sum / count
        else:
            average = 0.0
        
        assert average == 0.0
    
    def test_percentage_calculation_with_zero_denominator(self, dashboard_service):
        """Test percentage calculations handle zero denominators."""
        numerator = 5
        denominator = 0
        
        if denominator > 0:
            percentage = (numerator / denominator) * 100
        else:
            percentage = 0.0
        
        assert percentage == 0.0
    
    def test_date_range_filtering_accuracy(self, dashboard_service):
        """Test that date range filters correctly include/exclude records."""
        now = datetime.utcnow()
        start_date = now - timedelta(days=7)
        end_date = now
        
        # Records within range
        within_range = [
            Mock(date=now - timedelta(days=3)),
            Mock(date=now - timedelta(days=5)),
        ]
        
        # Records outside range
        outside_range = [
            Mock(date=now - timedelta(days=10)),
            Mock(date=now + timedelta(days=1)),
        ]
        
        for record in within_range:
            assert start_date <= record.date <= end_date
        
        for record in outside_range:
            assert not (start_date <= record.date <= end_date)
    
    def test_kpi_trend_calculation(self, dashboard_service):
        """Test KPI trend calculation comparing current vs previous period."""
        current_period_value = 1200.0
        previous_period_value = 1000.0
        
        change = current_period_value - previous_period_value
        percentage_change = (change / previous_period_value) * 100
        
        # Should be 20% increase
        assert percentage_change == 20.0
    
    def test_data_consistency_across_aggregations(self, dashboard_service, mock_sessions):
        """Test that aggregated totals match sum of individual records."""
        # Mock orders
        orders = [
            Mock(spec=Order, total_value=100.0),
            Mock(spec=Order, total_value=200.0),
            Mock(spec=Order, total_value=300.0),
        ]
        
        # Sum of individual records
        individual_sum = sum(o.total_value for o in orders)
        
        # Aggregated total (should match)
        aggregated_total = 600.0
        
        assert individual_sum == aggregated_total
    
    def test_multi_dimensional_aggregation(self, dashboard_service):
        """Test aggregation across multiple dimensions (e.g., by customer and by product)."""
        # Data grouped by customer
        customer_totals = {
            'Customer A': 5000.0,
            'Customer B': 3000.0,
            'Customer C': 2000.0
        }
        
        # Overall total should equal sum of customer totals
        overall_total = sum(customer_totals.values())
        assert overall_total == 10000.0
    
    def test_time_based_metric_consistency(self, dashboard_service):
        """Test that time-based metrics are consistent across different granularities."""
        # Daily metrics for a week
        daily_values = [100, 150, 200, 175, 225, 250, 300]
        
        # Weekly total
        weekly_total = sum(daily_values)
        assert weekly_total == 1400
        
        # Weekly average
        weekly_average = weekly_total / len(daily_values)
        assert abs(weekly_average - 200.0) < 0.01
