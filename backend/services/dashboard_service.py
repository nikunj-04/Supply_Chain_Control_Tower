"""Service layer for dashboard data aggregation and analysis."""
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy import func
import random

from config import settings
from logger import setup_logger
from models.wms_models import get_wms_session, Inventory, PickingTask, WarehouseMetrics
from models.oms_models import get_oms_session, Order, OrderMetrics
from models.tms_models import get_tms_session, Shipment, TransportMetrics
from models.billing_models import get_billing_session, Invoice, BillingMetrics
from models.returns_models import get_returns_session, Return, ReturnMetrics
from models.yard_models import get_yard_session, DockAppointment, YardLocation, YardMetrics

logger = setup_logger(__name__)


class DashboardService:
    """Service for aggregating dashboard data."""
    
    def __init__(self):
        """Initialize dashboard service with client filtering support."""
        self.current_user = None  # Will be set per request
    
    def set_current_user(self, user: Dict[str, Any]):
        """Set the current user for client filtering."""
        self.current_user = user
    
    def _should_filter_by_client(self) -> bool:
        """Check if data should be filtered by client_id."""
        if not self.current_user:
            return False
        # Filter if user has a client_id (is a client user)
        return self.current_user.get('client_id') is not None
    
    def _get_client_id(self) -> str:
        """Get the client_id for filtering."""
        if self.current_user:
            return self.current_user.get('client_id')
        return None
    
    def get_kpi_dashboard(self) -> Dict[str, Any]:
        """Get KPI dashboard with key performance indicators."""
        logger.info("Generating KPI dashboard")
        
        try:
            from datetime import datetime
            
            # Service Levels
            service_levels = self._get_service_levels_kpis()
            
            # Fulfillment Execution
            fulfillment = self._get_fulfillment_kpis()
            
            # Productivity & Staffing
            productivity = self._get_productivity_kpis()
            
            # Inventory Health
            inventory = self._get_inventory_health_kpis()
            
            # Dock & Carrier Flow
            dock_flow = self._get_dock_flow_kpis()
            
            # Returns & Billing Control
            returns_billing = self._get_returns_billing_kpis()
            
            return {
                "last_updated": datetime.utcnow().strftime("%b %d, %Y, %I:%M %p"),
                "categories": [
                    service_levels,
                    fulfillment,
                    productivity,
                    inventory,
                    dock_flow,
                    returns_billing
                ]
            }
        except Exception as e:
            logger.error(f"Error generating KPI dashboard: {e}")
            raise
    
    def _get_service_levels_kpis(self) -> Dict[str, Any]:
        """Get Service Levels KPIs."""
        session = get_oms_session(settings.oms_db_path)
        try:
            latest_metric = session.query(OrderMetrics).order_by(
                OrderMetrics.date.desc()
            ).first()
            
            total_orders = session.query(Order).count()
            on_time_full = session.query(Order).filter(
                Order.status == "delivered",
                Order.actual_delivery_date <= Order.promised_delivery_date
            ).count()
            
            on_time_pct = (on_time_full / total_orders * 100) if total_orders > 0 else 95.0
            on_time_in_full = on_time_pct * 1.04  # Slightly higher
            
            avg_backlog = 2.1
            
            return {
                "title": "Service Levels",
                "icon": "📈",
                "icon_color": "#3b82f6",
                "metrics": [
                    {
                        "label": "On-time ship %",
                        "value": f"{on_time_pct:.1f}%",
                        "status": "attention" if on_time_pct < 95 else "on_target"
                    },
                    {
                        "label": "On Time In Full %",
                        "value": f"{min(on_time_in_full, 99.9):.1f}%",
                        "status": "on_target"
                    },
                    {
                        "label": "Backlog aging",
                        "value": f"{avg_backlog:.1f} days",
                        "status": "on_target"
                    }
                ]
            }
        finally:
            session.close()
    
    def _get_fulfillment_kpis(self) -> Dict[str, Any]:
        """Get Fulfillment Execution KPIs."""
        session = get_oms_session(settings.oms_db_path)
        try:
            latest_metric = session.query(OrderMetrics).order_by(
                OrderMetrics.date.desc()
            ).first()
            
            wms_session = get_wms_session(settings.wms_db_path)
            try:
                total_picks = wms_session.query(PickingTask).count()
                completed_picks = wms_session.query(PickingTask).filter(
                    PickingTask.status == "completed"
                ).count()
                pick_accuracy = (completed_picks / total_picks * 100) if total_picks > 0 else 99.6
            finally:
                wms_session.close()
            
            return {
                "title": "Fulfillment Execution",
                "icon": "📦",
                "icon_color": "#8b5cf6",
                "metrics": [
                    {
                        "label": "Order cycle time",
                        "value": f"{latest_metric.avg_processing_time_hours:.1f} hrs" if latest_metric else "18.3 hrs",
                        "status": "on_target"
                    },
                    {
                        "label": "Pick accuracy",
                        "value": f"{pick_accuracy:.1f}%",
                        "status": "on_target"
                    },
                    {
                        "label": "Rework rate",
                        "value": "1.8%",
                        "status": "attention"
                    }
                ]
            }
        finally:
            session.close()
    
    def _get_productivity_kpis(self) -> Dict[str, Any]:
        """Get Productivity & Staffing KPIs."""
        return {
            "title": "Productivity & Staffing",
            "icon": "👥",
            "icon_color": "#10b981",
            "metrics": [
                {
                    "label": "Units per labor hour",
                    "value": "142",
                    "status": "on_target"
                },
                {
                    "label": "Pick/pack rate",
                    "value": "86 units/hr",
                    "status": "attention"
                },
                {
                    "label": "Overtime %",
                    "value": "8.4%",
                    "status": "critical"
                }
            ]
        }
    
    def _get_inventory_health_kpis(self) -> Dict[str, Any]:
        """Get Inventory Health KPIs."""
        session = get_wms_session(settings.wms_db_path)
        try:
            latest_metric = session.query(WarehouseMetrics).order_by(
                WarehouseMetrics.date.desc()
            ).first()
            
            total_inventory = session.query(Inventory).count()
            stockouts = session.query(Inventory).filter(
                Inventory.quantity_available == 0
            ).count()
            stockout_rate = (stockouts / total_inventory * 100) if total_inventory > 0 else 0.4
            
            return {
                "title": "Inventory Health",
                "icon": "📊",
                "icon_color": "#6366f1",
                "metrics": [
                    {
                        "label": "Inventory accuracy %",
                        "value": f"{latest_metric.inventory_accuracy_pct:.1f}%" if latest_metric else "98.7%",
                        "status": "on_target"
                    },
                    {
                        "label": "Cycle count completion",
                        "value": "92%",
                        "status": "attention"
                    },
                    {
                        "label": "Stockout rate",
                        "value": f"{stockout_rate:.1f}%",
                        "status": "on_target" if stockout_rate < 1 else "attention"
                    }
                ]
            }
        finally:
            session.close()
    
    def _get_dock_flow_kpis(self) -> Dict[str, Any]:
        """Get Dock & Carrier Flow KPIs."""
        session = get_yard_session(settings.yard_db_path)
        try:
            latest_metric = session.query(YardMetrics).order_by(
                YardMetrics.date.desc()
            ).first()
            
            # Calculate detention hours (appointments taking too long)
            completed = session.query(DockAppointment).filter(
                DockAppointment.status == "completed",
                DockAppointment.actual_duration_minutes.isnot(None)
            ).all()
            
            detention_count = sum(1 for a in completed if a.actual_duration_minutes > a.expected_duration_minutes + 30)
            avg_detention = 4.2  # hours
            
            on_time_appointments = session.query(DockAppointment).filter(
                DockAppointment.status == "completed",
                DockAppointment.actual_arrival.isnot(None)
            ).count()
            total_appointments = session.query(DockAppointment).filter(
                DockAppointment.status.in_(["completed", "missed"])
            ).count()
            
            appointment_adherence = (on_time_appointments / total_appointments * 100) if total_appointments > 0 else 89.0
            
            return {
                "title": "Dock & Carrier Flow",
                "icon": "🚛",
                "icon_color": "#f97316",
                "metrics": [
                    {
                        "label": "Dock turn time",
                        "value": f"{int(latest_metric.avg_dock_time_minutes)} min" if latest_metric else "32 min",
                        "status": "attention"
                    },
                    {
                        "label": "Detention hours",
                        "value": f"{avg_detention:.1f} hrs",
                        "status": "critical"
                    },
                    {
                        "label": "Appointment adherence %",
                        "value": f"{appointment_adherence:.0f}%",
                        "status": "attention"
                    }
                ]
            }
        finally:
            session.close()
    
    def _get_returns_billing_kpis(self) -> Dict[str, Any]:
        """Get Returns & Billing Control KPIs."""
        returns_session = get_returns_session(settings.returns_db_path)
        billing_session = get_billing_session(settings.billing_db_path)
        
        try:
            returns_metric = returns_session.query(ReturnMetrics).order_by(
                ReturnMetrics.date.desc()
            ).first()
            
            # Calculate disposition accuracy
            processed_returns = returns_session.query(Return).filter(
                Return.status.in_(["processed", "refunded"])
            ).count()
            
            # Missed charges from billing
            total_invoices = billing_session.query(Invoice).count()
            disputed = billing_session.query(Invoice).filter(
                Invoice.status == "disputed"
            ).count()
            missed_charges_pct = (disputed / total_invoices * 100) if total_invoices > 0 else 2.1
            
            return {
                "title": "Returns & Billing Control",
                "icon": "💰",
                "icon_color": "#06b6d4",
                "metrics": [
                    {
                        "label": "Returns cycle time",
                        "value": f"{returns_metric.avg_processing_time_days:.1f} days" if returns_metric else "3.8 days",
                        "status": "on_target"
                    },
                    {
                        "label": "Disposition accuracy",
                        "value": f"{returns_metric.resaleable_rate_pct:.1f}%" if returns_metric else "96.5%",
                        "status": "on_target"
                    },
                    {
                        "label": "Missed charges",
                        "value": f"{missed_charges_pct:.1f}%",
                        "status": "attention"
                    }
                ]
            }
        finally:
            returns_session.close()
            billing_session.close()
    
    def get_operational_scorecard(self) -> Dict[str, Any]:
        """Get operational scorecard data from all systems."""
        logger.info("Generating operational scorecard")
        
        try:
            systems = [
                self._get_wms_scorecard(),
                self._get_oms_scorecard(),
                self._get_tms_scorecard(),
                self._get_billing_scorecard(),
                self._get_returns_scorecard(),
                self._get_yard_scorecard(),
            ]
            
            # Calculate summary
            healthy_count = sum(1 for s in systems if s["overall_status"] == "healthy")
            warning_count = sum(1 for s in systems if s["overall_status"] == "warning")
            critical_count = sum(1 for s in systems if s["overall_status"] == "critical")
            
            return {
                "timestamp": datetime.utcnow(),
                "systems": systems,
                "summary": {
                    "total_systems": len(systems),
                    "healthy": healthy_count,
                    "warning": warning_count,
                    "critical": critical_count
                }
            }
        except Exception as e:
            logger.error(f"Error generating scorecard: {e}")
            raise
    
    def _get_wms_scorecard(self) -> Dict[str, Any]:
        """Get WMS scorecard."""
        session = get_wms_session(settings.wms_db_path)
        try:
            # Get latest metrics
            latest_metric = session.query(WarehouseMetrics).order_by(
                WarehouseMetrics.date.desc()
            ).first()
            
            # Count low inventory items
            low_inventory = session.query(Inventory).filter(
                Inventory.quantity_available <= Inventory.reorder_point
            ).count()
            
            # Count delayed picks
            delayed_picks = session.query(PickingTask).filter(
                PickingTask.status == "delayed"
            ).count()
            
            # Calculate pick completion rate
            total_picks = session.query(PickingTask).count()
            completed_picks = session.query(PickingTask).filter(
                PickingTask.status == "completed"
            ).count()
            completion_rate = (completed_picks / total_picks * 100) if total_picks > 0 else 0
            
            metrics = [
                {
                    "name": "Pick Completion Rate",
                    "value": round(completion_rate, 1),
                    "unit": "%",
                    "trend": "stable",
                    "status": "good" if completion_rate >= 90 else "warning"
                },
                {
                    "name": "Inventory Accuracy",
                    "value": round(latest_metric.inventory_accuracy_pct, 1) if latest_metric else 99.0,
                    "unit": "%",
                    "trend": "up",
                    "status": "good"
                },
                {
                    "name": "Capacity Utilization",
                    "value": round(latest_metric.capacity_utilization_pct, 1) if latest_metric else 75.0,
                    "unit": "%",
                    "trend": "stable",
                    "status": "good"
                },
                {
                    "name": "Low Inventory Items",
                    "value": low_inventory,
                    "unit": "items",
                    "trend": "down",
                    "status": "warning" if low_inventory > 10 else "good"
                },
                {
                    "name": "Delayed Picks",
                    "value": delayed_picks,
                    "unit": "tasks",
                    "trend": "stable",
                    "status": "warning" if delayed_picks > 5 else "good"
                }
            ]
            
            # Determine overall status
            status_counts = {"critical": 0, "warning": 0, "good": 0}
            for m in metrics:
                status_counts[m["status"]] += 1
            
            if status_counts["critical"] > 0:
                overall_status = "critical"
            elif status_counts["warning"] > 0:
                overall_status = "warning"
            else:
                overall_status = "healthy"
            
            return {
                "system_name": "Warehouse Management (WMS)",
                "metrics": metrics,
                "overall_status": overall_status
            }
        finally:
            session.close()
    
    def _get_oms_scorecard(self) -> Dict[str, Any]:
        """Get OMS scorecard."""
        session = get_oms_session(settings.oms_db_path)
        try:
            # Get latest metrics
            latest_metric = session.query(OrderMetrics).order_by(
                OrderMetrics.date.desc()
            ).first()
            
            # Build base query with optional client filtering
            base_query = session.query(Order)
            if self._should_filter_by_client():
                client_id = self._get_client_id()
                base_query = base_query.filter(Order.customer_id == client_id)
            
            # Count orders by status
            pending_orders = base_query.filter(
                Order.status.in_(["pending", "processing"])
            ).count()
            
            delayed_orders = base_query.filter(
                Order.status.in_(["pending", "processing"]),
                Order.promised_delivery_date < datetime.utcnow()
            ).count()
            
            metrics = [
                {
                    "name": "On-Time Delivery",
                    "value": round(latest_metric.on_time_delivery_pct, 1) if latest_metric else 95.0,
                    "unit": "%",
                    "trend": "up",
                    "status": "good" if (latest_metric and latest_metric.on_time_delivery_pct >= 90) else "warning"
                },
                {
                    "name": "Order Accuracy",
                    "value": round(latest_metric.order_accuracy_pct, 1) if latest_metric else 98.5,
                    "unit": "%",
                    "trend": "stable",
                    "status": "good"
                },
                {
                    "name": "Pending Orders",
                    "value": pending_orders,
                    "unit": "orders",
                    "trend": "stable",
                    "status": "good" if pending_orders < 50 else "warning"
                },
                {
                    "name": "Delayed Orders",
                    "value": delayed_orders,
                    "unit": "orders",
                    "trend": "down",
                    "status": "critical" if delayed_orders > 10 else "warning" if delayed_orders > 5 else "good"
                },
                {
                    "name": "Avg Processing Time",
                    "value": round(latest_metric.avg_processing_time_hours, 1) if latest_metric else 24.0,
                    "unit": "hrs",
                    "trend": "stable",
                    "status": "good"
                }
            ]
            
            status_counts = {"critical": 0, "warning": 0, "good": 0}
            for m in metrics:
                status_counts[m["status"]] += 1
            
            if status_counts["critical"] > 0:
                overall_status = "critical"
            elif status_counts["warning"] > 0:
                overall_status = "warning"
            else:
                overall_status = "healthy"
            
            return {
                "system_name": "Order Management (OMS)",
                "metrics": metrics,
                "overall_status": overall_status
            }
        finally:
            session.close()
    
    def _get_tms_scorecard(self) -> Dict[str, Any]:
        """Get TMS scorecard."""
        session = get_tms_session(settings.tms_db_path)
        try:
            latest_metric = session.query(TransportMetrics).order_by(
                TransportMetrics.date.desc()
            ).first()
            
            in_transit = session.query(Shipment).filter(
                Shipment.status == "in_transit"
            ).count()
            
            delayed_shipments = session.query(Shipment).filter(
                Shipment.status == "delayed"
            ).count()
            
            exception_shipments = session.query(Shipment).filter(
                Shipment.status == "exception"
            ).count()
            
            metrics = [
                {
                    "name": "On-Time Delivery",
                    "value": round(latest_metric.on_time_delivery_pct, 1) if latest_metric else 92.0,
                    "unit": "%",
                    "trend": "stable",
                    "status": "good" if (latest_metric and latest_metric.on_time_delivery_pct >= 88) else "warning"
                },
                {
                    "name": "In Transit",
                    "value": in_transit,
                    "unit": "shipments",
                    "trend": "stable",
                    "status": "good"
                },
                {
                    "name": "Delayed Shipments",
                    "value": delayed_shipments,
                    "unit": "shipments",
                    "trend": "down",
                    "status": "warning" if delayed_shipments > 5 else "good"
                },
                {
                    "name": "Exceptions",
                    "value": exception_shipments,
                    "unit": "shipments",
                    "trend": "stable",
                    "status": "critical" if exception_shipments > 3 else "warning" if exception_shipments > 0 else "good"
                },
                {
                    "name": "Avg Transit Time",
                    "value": round(latest_metric.avg_transit_time_hours, 1) if latest_metric else 48.0,
                    "unit": "hrs",
                    "trend": "stable",
                    "status": "good"
                }
            ]
            
            status_counts = {"critical": 0, "warning": 0, "good": 0}
            for m in metrics:
                status_counts[m["status"]] += 1
            
            if status_counts["critical"] > 0:
                overall_status = "critical"
            elif status_counts["warning"] > 0:
                overall_status = "warning"
            else:
                overall_status = "healthy"
            
            return {
                "system_name": "Transportation (TMS)",
                "metrics": metrics,
                "overall_status": overall_status
            }
        finally:
            session.close()
    
    def _get_billing_scorecard(self) -> Dict[str, Any]:
        """Get Billing scorecard."""
        session = get_billing_session(settings.billing_db_path)
        try:
            latest_metric = session.query(BillingMetrics).order_by(
                BillingMetrics.date.desc()
            ).first()
            
            # Build base query with optional client filtering
            base_query = session.query(Invoice)
            if self._should_filter_by_client():
                client_id = self._get_client_id()
                base_query = base_query.filter(Invoice.customer_id == client_id)
            
            overdue_invoices = base_query.filter(
                Invoice.status == "overdue"
            ).count()
            
            disputed_invoices = base_query.filter(
                Invoice.status == "disputed"
            ).count()
            
            total_outstanding = base_query.with_entities(func.sum(Invoice.balance)).filter(
                Invoice.status.in_(["pending", "overdue"])
            ).scalar() or 0
            
            metrics = [
                {
                    "name": "Collection Rate",
                    "value": round(latest_metric.collection_rate_pct, 1) if latest_metric else 96.0,
                    "unit": "%",
                    "trend": "up",
                    "status": "good" if (latest_metric and latest_metric.collection_rate_pct >= 92) else "warning"
                },
                {
                    "name": "Outstanding Balance",
                    "value": round(total_outstanding, 0),
                    "unit": "$",
                    "trend": "stable",
                    "status": "warning" if total_outstanding > 50000 else "good"
                },
                {
                    "name": "Overdue Invoices",
                    "value": overdue_invoices,
                    "unit": "invoices",
                    "trend": "stable",
                    "status": "critical" if overdue_invoices > 10 else "warning" if overdue_invoices > 5 else "good"
                },
                {
                    "name": "Disputed Invoices",
                    "value": disputed_invoices,
                    "unit": "invoices",
                    "trend": "down",
                    "status": "warning" if disputed_invoices > 3 else "good"
                }
            ]
            
            status_counts = {"critical": 0, "warning": 0, "good": 0}
            for m in metrics:
                status_counts[m["status"]] += 1
            
            if status_counts["critical"] > 0:
                overall_status = "critical"
            elif status_counts["warning"] > 0:
                overall_status = "warning"
            else:
                overall_status = "healthy"
            
            return {
                "system_name": "Billing",
                "metrics": metrics,
                "overall_status": overall_status
            }
        finally:
            session.close()
    
    def _get_returns_scorecard(self) -> Dict[str, Any]:
        """Get Returns scorecard."""
        session = get_returns_session(settings.returns_db_path)
        try:
            latest_metric = session.query(ReturnMetrics).order_by(
                ReturnMetrics.date.desc()
            ).first()
            
            pending_returns = session.query(Return).filter(
                Return.status.in_(["initiated", "in_transit", "received"])
            ).count()
            
            metrics = [
                {
                    "name": "Return Rate",
                    "value": round(latest_metric.return_rate_pct, 1) if latest_metric else 5.0,
                    "unit": "%",
                    "trend": "stable",
                    "status": "warning" if (latest_metric and latest_metric.return_rate_pct > 6) else "good"
                },
                {
                    "name": "Avg Processing Time",
                    "value": round(latest_metric.avg_processing_time_days, 1) if latest_metric else 3.5,
                    "unit": "days",
                    "trend": "down",
                    "status": "good" if (latest_metric and latest_metric.avg_processing_time_days < 4) else "warning"
                },
                {
                    "name": "Pending Returns",
                    "value": pending_returns,
                    "unit": "returns",
                    "trend": "stable",
                    "status": "warning" if pending_returns > 15 else "good"
                },
                {
                    "name": "Resaleable Rate",
                    "value": round(latest_metric.resaleable_rate_pct, 1) if latest_metric else 70.0,
                    "unit": "%",
                    "trend": "stable",
                    "status": "good" if (latest_metric and latest_metric.resaleable_rate_pct >= 65) else "warning"
                }
            ]
            
            status_counts = {"critical": 0, "warning": 0, "good": 0}
            for m in metrics:
                status_counts[m["status"]] += 1
            
            if status_counts["critical"] > 0:
                overall_status = "critical"
            elif status_counts["warning"] > 0:
                overall_status = "warning"
            else:
                overall_status = "healthy"
            
            return {
                "system_name": "Returns Management",
                "metrics": metrics,
                "overall_status": overall_status
            }
        finally:
            session.close()
    
    def _get_yard_scorecard(self) -> Dict[str, Any]:
        """Get Yard scorecard."""
        session = get_yard_session(settings.yard_db_path)
        try:
            latest_metric = session.query(YardMetrics).order_by(
                YardMetrics.date.desc()
            ).first()
            
            missed_appointments = session.query(DockAppointment).filter(
                DockAppointment.status == "missed"
            ).count()
            
            active_appointments = session.query(DockAppointment).filter(
                DockAppointment.status.in_(["checked_in", "loading", "unloading"])
            ).count()
            
            occupied_locations = session.query(YardLocation).filter(
                YardLocation.status == "occupied"
            ).count()
            
            total_locations = session.query(YardLocation).count()
            utilization = (occupied_locations / total_locations * 100) if total_locations > 0 else 0
            
            metrics = [
                {
                    "name": "On-Time Arrival",
                    "value": round(latest_metric.on_time_arrival_pct, 1) if latest_metric else 88.0,
                    "unit": "%",
                    "trend": "up",
                    "status": "good" if (latest_metric and latest_metric.on_time_arrival_pct >= 85) else "warning"
                },
                {
                    "name": "Yard Utilization",
                    "value": round(utilization, 1),
                    "unit": "%",
                    "trend": "stable",
                    "status": "warning" if utilization > 85 else "good"
                },
                {
                    "name": "Active Appointments",
                    "value": active_appointments,
                    "unit": "docks",
                    "trend": "stable",
                    "status": "good"
                },
                {
                    "name": "Missed Appointments",
                    "value": missed_appointments,
                    "unit": "appointments",
                    "trend": "down",
                    "status": "warning" if missed_appointments > 3 else "good"
                },
                {
                    "name": "Avg Dock Time",
                    "value": round(latest_metric.avg_dock_time_minutes, 1) if latest_metric else 45.0,
                    "unit": "min",
                    "trend": "stable",
                    "status": "good" if (latest_metric and latest_metric.avg_dock_time_minutes < 60) else "warning"
                }
            ]
            
            status_counts = {"critical": 0, "warning": 0, "good": 0}
            for m in metrics:
                status_counts[m["status"]] += 1
            
            if status_counts["critical"] > 0:
                overall_status = "critical"
            elif status_counts["warning"] > 0:
                overall_status = "warning"
            else:
                overall_status = "healthy"
            
            return {
                "system_name": "Yard/Dock Management",
                "metrics": metrics,
                "overall_status": overall_status
            }
        finally:
            session.close()
    
    def get_exceptions(self) -> Dict[str, Any]:
        """Get exceptions and early warnings from all systems."""
        logger.info("Generating exceptions and early warnings")
        
        try:
            exceptions = []
            
            # Collect exceptions from each system
            exceptions.extend(self._get_wms_exceptions())
            exceptions.extend(self._get_oms_exceptions())
            exceptions.extend(self._get_tms_exceptions())
            exceptions.extend(self._get_billing_exceptions())
            exceptions.extend(self._get_returns_exceptions())
            exceptions.extend(self._get_yard_exceptions())
            
            # Sort by severity and created_at
            severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
            exceptions.sort(key=lambda x: (severity_order[x["severity"]], x["created_at"]), reverse=True)
            
            # Calculate summary
            summary = {
                "total": len(exceptions),
                "critical": sum(1 for e in exceptions if e["severity"] == "critical"),
                "high": sum(1 for e in exceptions if e["severity"] == "high"),
                "medium": sum(1 for e in exceptions if e["severity"] == "medium"),
                "low": sum(1 for e in exceptions if e["severity"] == "low"),
                "by_system": {}
            }
            
            for exc in exceptions:
                system = exc["system"]
                if system not in summary["by_system"]:
                    summary["by_system"][system] = 0
                summary["by_system"][system] += 1
            
            return {
                "timestamp": datetime.utcnow(),
                "summary": summary,
                "exceptions": exceptions
            }
        except Exception as e:
            logger.error(f"Error generating exceptions: {e}")
            raise
    
    def _get_wms_exceptions(self) -> List[Dict[str, Any]]:
        """Get WMS exceptions."""
        session = get_wms_session(settings.wms_db_path)
        exceptions = []
        
        try:
            # Low inventory alerts
            low_inventory_items = session.query(Inventory).filter(
                Inventory.quantity_available <= Inventory.reorder_point
            ).limit(10).all()
            
            for item in low_inventory_items:
                severity = "critical" if item.quantity_available == 0 else "high" if item.quantity_available < item.reorder_point * 0.5 else "medium"
                exceptions.append({
                    "id": f"WMS-INV-{item.id}",
                    "system": "WMS",
                    "severity": severity,
                    "category": "Inventory",
                    "title": f"Low Stock: {item.sku}",
                    "description": f"{item.product_name} has {item.quantity_available} units available (reorder point: {item.reorder_point})",
                    "affected_entity": item.sku,
                    "created_at": item.last_updated,
                    "status": "open",
                    "recommended_action": "Initiate purchase order or transfer stock from another warehouse"
                })
            
            # Delayed picking tasks
            delayed_tasks = session.query(PickingTask).filter(
                PickingTask.status == "delayed"
            ).limit(10).all()
            
            for task in delayed_tasks:
                exceptions.append({
                    "id": f"WMS-PICK-{task.id}",
                    "system": "WMS",
                    "severity": "high" if task.priority in ["high", "urgent"] else "medium",
                    "category": "Operations",
                    "title": f"Delayed Pick: {task.order_id}",
                    "description": f"Picking task for order {task.order_id} is delayed (created {task.created_at.strftime('%Y-%m-%d %H:%M')})",
                    "affected_entity": task.order_id,
                    "created_at": task.created_at,
                    "status": "open",
                    "recommended_action": "Review task assignment and resource allocation"
                })
        finally:
            session.close()
        
        return exceptions
    
    def _get_oms_exceptions(self) -> List[Dict[str, Any]]:
        """Get OMS exceptions."""
        session = get_oms_session(settings.oms_db_path)
        exceptions = []
        
        try:
            # Build base query with optional client filtering
            base_query = session.query(Order)
            if self._should_filter_by_client():
                client_id = self._get_client_id()
                base_query = base_query.filter(Order.customer_id == client_id)
            
            # Delayed orders
            delayed_orders = base_query.filter(
                Order.status.in_(["pending", "processing"]),
                Order.promised_delivery_date < datetime.utcnow()
            ).limit(10).all()
            
            for order in delayed_orders:
                days_late = (datetime.utcnow() - order.promised_delivery_date).days
                severity = "critical" if days_late > 2 else "high"
                
                exceptions.append({
                    "id": f"OMS-ORD-{order.id}",
                    "system": "OMS",
                    "severity": severity,
                    "category": "Order Fulfillment",
                    "title": f"Late Order: {order.order_id}",
                    "description": f"Order {order.order_id} for {order.customer_name} is {days_late} days past promised delivery",
                    "affected_entity": order.order_id,
                    "created_at": order.promised_delivery_date,
                    "status": "open",
                    "recommended_action": "Contact customer and expedite shipping"
                })
        finally:
            session.close()
        
        return exceptions
    
    def _get_tms_exceptions(self) -> List[Dict[str, Any]]:
        """Get TMS exceptions."""
        session = get_tms_session(settings.tms_db_path)
        exceptions = []
        
        try:
            # Shipment exceptions
            exception_shipments = session.query(Shipment).filter(
                Shipment.status == "exception"
            ).limit(10).all()
            
            for shipment in exception_shipments:
                exceptions.append({
                    "id": f"TMS-SHIP-{shipment.id}",
                    "system": "TMS",
                    "severity": "critical",
                    "category": "Transportation",
                    "title": f"Shipment Exception: {shipment.shipment_id}",
                    "description": f"Shipment {shipment.shipment_id} (Order: {shipment.order_id}) has encountered an exception with {shipment.carrier}",
                    "affected_entity": shipment.shipment_id,
                    "created_at": shipment.scheduled_pickup,
                    "status": "open",
                    "recommended_action": "Contact carrier immediately to resolve issue"
                })
            
            # Delayed shipments
            delayed_shipments = session.query(Shipment).filter(
                Shipment.status == "delayed"
            ).limit(10).all()
            
            for shipment in delayed_shipments:
                exceptions.append({
                    "id": f"TMS-DEL-{shipment.id}",
                    "system": "TMS",
                    "severity": "high",
                    "category": "Transportation",
                    "title": f"Delayed Shipment: {shipment.shipment_id}",
                    "description": f"Shipment {shipment.shipment_id} is delayed. Expected delivery: {shipment.estimated_delivery.strftime('%Y-%m-%d')}",
                    "affected_entity": shipment.shipment_id,
                    "created_at": shipment.estimated_delivery,
                    "status": "open",
                    "recommended_action": "Monitor shipment closely and update customer"
                })
        finally:
            session.close()
        
        return exceptions
    
    def _get_billing_exceptions(self) -> List[Dict[str, Any]]:
        """Get Billing exceptions."""
        session = get_billing_session(settings.billing_db_path)
        exceptions = []
        
        try:
            # Build base query with optional client filtering
            base_query = session.query(Invoice)
            if self._should_filter_by_client():
                client_id = self._get_client_id()
                base_query = base_query.filter(Invoice.customer_id == client_id)
            
            # Overdue invoices
            overdue_invoices = base_query.filter(
                Invoice.status == "overdue"
            ).limit(10).all()
            
            for invoice in overdue_invoices:
                days_overdue = (datetime.utcnow() - invoice.due_date).days
                severity = "critical" if days_overdue > 30 else "high" if days_overdue > 14 else "medium"
                
                exceptions.append({
                    "id": f"BILL-OVD-{invoice.id}",
                    "system": "Billing",
                    "severity": severity,
                    "category": "Accounts Receivable",
                    "title": f"Overdue Invoice: {invoice.invoice_id}",
                    "description": f"Invoice {invoice.invoice_id} for {invoice.customer_name} is {days_overdue} days overdue (Balance: ${invoice.balance:.2f})",
                    "affected_entity": invoice.invoice_id,
                    "created_at": invoice.due_date,
                    "status": "open",
                    "recommended_action": "Send payment reminder or initiate collection process"
                })
            
            # Disputed invoices
            disputed_invoices = base_query.filter(
                Invoice.status == "disputed"
            ).limit(10).all()
            
            for invoice in disputed_invoices:
                exceptions.append({
                    "id": f"BILL-DIS-{invoice.id}",
                    "system": "Billing",
                    "severity": "high",
                    "category": "Accounts Receivable",
                    "title": f"Disputed Invoice: {invoice.invoice_id}",
                    "description": f"Invoice {invoice.invoice_id} for {invoice.customer_name} is disputed (Amount: ${invoice.total:.2f})",
                    "affected_entity": invoice.invoice_id,
                    "created_at": invoice.invoice_date,
                    "status": "open",
                    "recommended_action": "Contact customer to resolve dispute"
                })
        finally:
            session.close()
        
        return exceptions
    

    def get_accessorial_charges(self) -> Dict[str, Any]:
        """Get accessorial charges recovery opportunities."""
        logger.info("Generating accessorial charges dashboard")
        
        try:
            opportunities = []
            
            # Get detention charges from TMS
            opportunities.extend(self._get_detention_charges())
            
            # Get redelivery charges from TMS
            opportunities.extend(self._get_redelivery_charges())
            
            # Get dock detention charges from Yard
            opportunities.extend(self._get_dock_detention_charges())
            
            # Check billing status for each charge
            opportunities = self._enrich_with_billing_status(opportunities)
            
            # Calculate summary
            summary = self._calculate_charge_summary(opportunities)
            
            return {
                "timestamp": datetime.utcnow(),
                "summary": summary,
                "opportunities": opportunities
            }
        except Exception as e:
            logger.error(f"Error generating accessorial charges: {str(e)}")
            raise
    
    def _enrich_with_billing_status(self, opportunities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Check if charges have been billed and update their status."""
        from models.billing_models import get_billing_session, BillingLineItem
        
        session = get_billing_session(settings.billing_db_path)
        
        try:
            # Get all billed charges
            line_items = session.query(BillingLineItem).all()
            billed_charges = {}
            
            for item in line_items:
                # Extract charge_id from description (format: "Type - CHARGE_ID")
                if " - " in item.description:
                    charge_id = item.description.split(" - ")[-1]
                    billed_charges[charge_id] = {
                        "invoice_number": item.invoice_id,
                        "invoice_date": None  # Could get from Invoice table if needed
                    }
            
            # Update opportunities with billing status
            for opp in opportunities:
                charge_id = opp.get("charge_id")
                if charge_id in billed_charges:
                    opp["status"] = "billed"
                    opp["invoice_number"] = billed_charges[charge_id]["invoice_number"]
                    opp["download_url"] = f"/invoices/{billed_charges[charge_id]['invoice_number']}.pdf"
            
            return opportunities
            
        except Exception as e:
            logger.warning(f"Error checking billing status: {e}")
            return opportunities
        finally:
            session.close()
    
    def _get_detention_charges(self) -> List[Dict[str, Any]]:
        """Get detention charges from delayed pickups/deliveries."""
        session = get_tms_session(settings.tms_db_path)
        charges = []
        
        # Excluded shipment IDs (processed/removed charges)
        excluded_shipment_ids = [4, 5, 10, 22]
        
        try:
            # Query shipments with delays
            shipments = session.query(Shipment).filter(
                Shipment.status.in_(["delayed", "exception"])
            ).limit(50).all()
            
            for shipment in shipments:
                # Skip excluded shipments
                if shipment.id in excluded_shipment_ids:
                    continue
                # Check pickup detention (> 2 hours late)
                if shipment.actual_pickup and shipment.scheduled_pickup:
                    delay_hours = (shipment.actual_pickup - shipment.scheduled_pickup).total_seconds() / 3600
                    if delay_hours > 2:
                        age_days = (datetime.utcnow() - shipment.actual_pickup).days
                        charges.append({
                            "charge_id": f"DET-PICK-{shipment.id}",
                            "charge_type": "detention",
                            "amount": 75.0 + (delay_hours - 2) * 25.0,  # $75 base + $25/hr
                            "shipment_id": shipment.shipment_id,
                            "carrier": shipment.carrier,
                            "occurrence_date": shipment.actual_pickup,
                            "age_days": age_days,
                            "status": "pending" if age_days < 30 else "under_review",
                            "description": f"Pickup delayed by {delay_hours:.1f} hours at {shipment.origin}",
                            "recommended_action": "Submit detention claim to carrier"
                        })
                
                # Check delivery detention (> 2 hours late)
                if shipment.actual_delivery and shipment.estimated_delivery:
                    delay_hours = (shipment.actual_delivery - shipment.estimated_delivery).total_seconds() / 3600
                    if delay_hours > 2:
                        age_days = (datetime.utcnow() - shipment.actual_delivery).days
                        charges.append({
                            "charge_id": f"DET-DEL-{shipment.id}",
                            "charge_type": "detention",
                            "amount": 75.0 + (delay_hours - 2) * 25.0,
                            "shipment_id": shipment.shipment_id,
                            "carrier": shipment.carrier,
                            "occurrence_date": shipment.actual_delivery,
                            "age_days": age_days,
                            "status": "pending" if age_days < 30 else "under_review",
                            "description": f"Delivery delayed by {delay_hours:.1f} hours to {shipment.destination}",
                            "recommended_action": "Submit detention claim to carrier"
                        })
        finally:
            session.close()
        
        return charges
    
    def _get_redelivery_charges(self) -> List[Dict[str, Any]]:
        """Get redelivery charges from failed deliveries."""
        session = get_tms_session(settings.tms_db_path)
        charges = []
        
        try:
            # Query shipments with exceptions that may need redelivery
            shipments = session.query(Shipment).filter(
                Shipment.status == "exception"
            ).limit(20).all()
            
            for shipment in shipments:
                if shipment.actual_delivery is None:  # Failed delivery
                    created_date = shipment.estimated_delivery or datetime.utcnow()
                    age_days = (datetime.utcnow() - created_date).days
                    
                    charges.append({
                        "charge_id": f"REDEL-{shipment.id}",
                        "charge_type": "redelivery",
                        "amount": 125.0,  # Standard redelivery fee
                        "shipment_id": shipment.shipment_id,
                        "carrier": shipment.carrier,
                        "occurrence_date": created_date,
                        "age_days": age_days,
                        "status": "pending",
                        "description": f"Failed delivery to {shipment.destination} - redelivery required",
                        "recommended_action": "Verify recipient details and bill redelivery fee"
                    })
        finally:
            session.close()
        
        return charges
    
    def _get_dock_detention_charges(self) -> List[Dict[str, Any]]:
        """Get dock detention charges from yard delays."""
        session = get_yard_session(settings.yard_db_path)
        charges = []
        
        try:
            # Query appointments with detention (delayed completion)
            appointments = session.query(DockAppointment).filter(
                DockAppointment.status.in_(["completed", "delayed"])
            ).limit(30).all()
            
            for appt in appointments:
                if appt.actual_completion and appt.scheduled_time:
                    # Calculate time from scheduled to completion
                    duration_hours = (appt.actual_completion - appt.scheduled_time).total_seconds() / 3600
                    
                    # If loading/unloading took more than 2 hours, charge detention
                    if duration_hours > 2:
                        age_days = (datetime.utcnow() - appt.actual_completion).days
                        charges.append({
                            "charge_id": f"DOCK-DET-{appt.id}",
                            "charge_type": "dock_detention",
                            "amount": 50.0 + (duration_hours - 2) * 40.0,  # $50 base + $40/hr
                            "shipment_id": None,
                            "carrier": appt.carrier,
                            "occurrence_date": appt.actual_completion,
                            "age_days": age_days,
                            "status": "pending" if age_days < 15 else "billed",
                            "description": f"Dock {appt.dock_door} detention - {duration_hours:.1f} hours ({appt.appointment_type})",
                            "recommended_action": "Bill carrier for excessive dock time"
                        })
        finally:
            session.close()
        
        return charges
    
    def _calculate_charge_summary(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for accessorial charges."""
        
        # Calculate totals
        total_recoverable = sum(opp["amount"] for opp in opportunities)
        total_opportunities = len(opportunities)
        
        # Count by status
        pending_review = len([o for o in opportunities if o["status"] == "pending"])
        billed_mtd = len([o for o in opportunities if o["status"] == "billed"])
        recovered_mtd = sum(o["amount"] for o in opportunities if o["status"] == "recovered")
        
        # Group by charge type
        by_charge_type = {}
        for opp in opportunities:
            charge_type = opp["charge_type"]
            if charge_type not in by_charge_type:
                by_charge_type[charge_type] = {"count": 0, "amount": 0}
            by_charge_type[charge_type]["count"] += 1
            by_charge_type[charge_type]["amount"] += opp["amount"]
        
        # Group by carrier
        by_carrier = {}
        for opp in opportunities:
            carrier = opp.get("carrier", "Unknown")
            if carrier not in by_carrier:
                by_carrier[carrier] = {"count": 0, "amount": 0}
            by_carrier[carrier]["count"] += 1
            by_carrier[carrier]["amount"] += opp["amount"]
        
        return {
            "total_recoverable": round(total_recoverable, 2),
            "total_opportunities": total_opportunities,
            "pending_review": pending_review,
            "billed_mtd": billed_mtd,
            "recovered_mtd": round(recovered_mtd, 2),
            "by_charge_type": by_charge_type,
            "by_carrier": by_carrier
        }


    def get_client_profitability(self) -> Dict[str, Any]:
        """Get client profitability analysis."""
        logger.info("Generating client profitability dashboard")
        
        try:
            clients = self._get_client_metrics()
            summary = self._calculate_profitability_summary(clients)
            
            return {
                "timestamp": datetime.utcnow(),
                "summary": summary,
                "clients": clients
            }
        except Exception as e:
            logger.error(f"Error generating client profitability: {str(e)}")
            raise
    
    def _get_client_metrics(self) -> List[Dict[str, Any]]:
        """Calculate profitability metrics for each client."""
        billing_session = get_billing_session(settings.billing_db_path)
        oms_session = get_oms_session(settings.oms_db_path)
        tms_session = get_tms_session(settings.tms_db_path)
        
        clients_data = []
        
        try:
            base_invoice_query = billing_session.query(Invoice)

            # Apply client filtering if user is a client user
            if self._should_filter_by_client():
                client_id = self._get_client_id()
                base_invoice_query = base_invoice_query.filter(Invoice.customer_id == client_id)

            # Anchor rolling windows to latest available invoice data.
            latest_invoice_date = base_invoice_query.with_entities(
                func.max(Invoice.invoice_date)
            ).scalar() or datetime.utcnow()
            latest_invoice_date = min(latest_invoice_date, datetime.utcnow())

            rolling_30_start = latest_invoice_date - timedelta(days=30)
            previous_30_start = latest_invoice_date - timedelta(days=60)
            year_start = datetime(latest_invoice_date.year, 1, 1)

            # Use customer_id as the canonical key; names can vary across random seed runs.
            customers = base_invoice_query.with_entities(Invoice.customer_id).distinct().all()

            for (customer_id,) in customers:
                latest_name_row = billing_session.query(Invoice.customer_name).filter(
                    Invoice.customer_id == customer_id
                ).order_by(Invoice.invoice_date.desc()).first()
                customer_name = latest_name_row[0] if latest_name_row else customer_id

                # Calculate rolling-window revenue from invoices.
                revenue_mtd_result = billing_session.query(
                    func.sum(Invoice.total)
                ).filter(
                    Invoice.customer_id == customer_id,
                    Invoice.invoice_date >= rolling_30_start,
                    Invoice.invoice_date <= latest_invoice_date
                ).scalar() or 0.0
                
                revenue_ytd_result = billing_session.query(
                    func.sum(Invoice.total)
                ).filter(
                    Invoice.customer_id == customer_id,
                    Invoice.invoice_date >= year_start,
                    Invoice.invoice_date <= latest_invoice_date
                ).scalar() or 0.0
                
                revenue_last_month = billing_session.query(
                    func.sum(Invoice.total)
                ).filter(
                    Invoice.customer_id == customer_id,
                    Invoice.invoice_date >= previous_30_start,
                    Invoice.invoice_date < rolling_30_start
                ).scalar() or 0.0

                # Link orders via billing order IDs for reliable cross-system attribution.
                orders_mtd_ids = [
                    row[0] for row in billing_session.query(Invoice.order_id).filter(
                        Invoice.customer_id == customer_id,
                        Invoice.invoice_date >= rolling_30_start,
                        Invoice.invoice_date <= latest_invoice_date
                    ).distinct().all()
                ]

                orders_ytd_ids = [
                    row[0] for row in billing_session.query(Invoice.order_id).filter(
                        Invoice.customer_id == customer_id,
                        Invoice.invoice_date >= year_start,
                        Invoice.invoice_date <= latest_invoice_date
                    ).distinct().all()
                ]

                orders_mtd = len(orders_mtd_ids)
                orders_ytd = len(orders_ytd_ids)
                
                # Calculate average order value
                avg_order_value = revenue_ytd_result / orders_ytd if orders_ytd > 0 else 0
                
                # Estimate costs (simplified: 70% of revenue for cost estimation)
                cost_ratio = 0.70
                cost_mtd = revenue_mtd_result * cost_ratio
                cost_ytd = revenue_ytd_result * cost_ratio
                
                # Calculate profit
                profit_mtd = revenue_mtd_result - cost_mtd
                profit_ytd = revenue_ytd_result - cost_ytd
                
                # Calculate margin
                margin_pct = (profit_ytd / revenue_ytd_result * 100) if revenue_ytd_result > 0 else 0
                
                # Calculate MoM growth
                growth_mom = ((revenue_mtd_result - revenue_last_month) / revenue_last_month * 100) if revenue_last_month > 0 else 0
                
                # Get service level (on-time delivery %)
                if orders_ytd_ids:
                    total_delivered = oms_session.query(Order).filter(
                        Order.order_id.in_(orders_ytd_ids),
                        Order.status == "delivered"
                    ).count()

                    on_time_delivered = oms_session.query(Order).filter(
                        Order.order_id.in_(orders_ytd_ids),
                        Order.status == "delivered",
                        Order.actual_delivery_date <= Order.promised_delivery_date
                    ).count()
                else:
                    total_delivered = 0
                    on_time_delivered = 0
                
                service_level_pct = (on_time_delivered / total_delivered * 100) if total_delivered > 0 else 100
                
                # Get average days to pay
                paid_invoices = billing_session.query(Invoice).filter(
                    Invoice.customer_id == customer_id,
                    Invoice.status == "paid",
                    Invoice.payment_date.isnot(None)
                ).all()
                
                if paid_invoices:
                    total_days = sum((inv.payment_date - inv.invoice_date).days for inv in paid_invoices)
                    days_to_pay = int(total_days / len(paid_invoices))
                else:
                    days_to_pay = 30  # Default
                
                clients_data.append({
                    "customer_id": customer_id,
                    "customer_name": customer_name,
                    # Legacy keys retained for UI compatibility.
                    "revenue_mtd": round(revenue_mtd_result, 2),
                    "revenue_ytd": round(revenue_ytd_result, 2),
                    "cost_mtd": round(cost_mtd, 2),
                    "cost_ytd": round(cost_ytd, 2),
                    "profit_mtd": round(profit_mtd, 2),
                    "profit_ytd": round(profit_ytd, 2),
                    # Explicit rolling-window aliases.
                    "revenue_30d": round(revenue_mtd_result, 2),
                    "revenue_90d": round(revenue_ytd_result, 2),
                    "revenue_ytd": round(revenue_ytd_result, 2),
                    "profit_30d": round(profit_mtd, 2),
                    "profit_90d": round(profit_ytd, 2),
                    "profit_ytd": round(profit_ytd, 2),
                    "margin_pct": round(margin_pct, 1),
                    "orders_mtd": orders_mtd,
                    "orders_ytd": orders_ytd,
                    "orders_30d": orders_mtd,
                    "orders_90d": orders_ytd,
                    "avg_order_value": round(avg_order_value, 2),
                    "growth_mom": round(growth_mom, 1),
                    "growth_30d_vs_prior_30d": round(growth_mom, 1),
                    "service_level_pct": round(service_level_pct, 1),
                    "days_to_pay": days_to_pay
                })
        
        finally:
            billing_session.close()
            oms_session.close()
            tms_session.close()
        
        # Sort by revenue YTD descending
        clients_data.sort(key=lambda x: x["revenue_ytd"], reverse=True)
        
        return clients_data
    
    def _calculate_profitability_summary(self, clients: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for client profitability."""
        
        if not clients:
            return {
                "total_revenue_mtd": 0,
                "total_profit_mtd": 0,
                "total_revenue_ytd": 0,
                "total_profit_ytd": 0,
                "avg_margin_pct": 0,
                "total_clients": 0,
                "top_revenue_client": "N/A",
                "top_margin_client": "N/A"
            }
        
        total_revenue_mtd = sum(c["revenue_mtd"] for c in clients)
        total_profit_mtd = sum(c["profit_mtd"] for c in clients)
        total_revenue_ytd = sum(c["revenue_ytd"] for c in clients)
        total_profit_ytd = sum(c["profit_ytd"] for c in clients)
        avg_margin_pct = sum(c["margin_pct"] for c in clients) / len(clients)
        
        top_revenue_client = max(clients, key=lambda x: x["revenue_ytd"])["customer_name"]
        top_margin_client = max(clients, key=lambda x: x["margin_pct"])["customer_name"]
        
        return {
            "total_revenue_mtd": round(total_revenue_mtd, 2),
            "total_profit_mtd": round(total_profit_mtd, 2),
            "total_revenue_ytd": round(total_revenue_ytd, 2),
            "total_profit_ytd": round(total_profit_ytd, 2),
            "avg_margin_pct": round(avg_margin_pct, 1),
            "total_clients": len(clients),
            "top_revenue_client": top_revenue_client,
            "top_margin_client": top_margin_client
        }


    def get_billing_analytics(self) -> Dict[str, Any]:
        """Get billing analytics and revenue insights."""
        logger.info("Generating billing analytics dashboard")
        
        try:
            billing_session = get_billing_session(settings.billing_db_path)
            
            # Calculate summary metrics
            summary = self._calculate_billing_summary(billing_session)
            
            # Get revenue by service type
            revenue_by_service = self._get_revenue_by_service(billing_session)
            
            # Get invoice status breakdown
            invoice_status = self._get_invoice_status_metrics(billing_session)
            
            # Get billing trends (last 30 days)
            trends = self._get_billing_trends(billing_session)
            
            billing_session.close()
            
            return {
                "timestamp": datetime.utcnow(),
                "summary": summary,
                "revenue_by_service": revenue_by_service,
                "invoice_status": invoice_status,
                "trends": trends
            }
        except Exception as e:
            logger.error(f"Error generating billing analytics: {str(e)}")
            raise
    
    def _calculate_billing_summary(self, session) -> Dict[str, Any]:
        """Calculate billing summary metrics."""
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        year_start = datetime(now.year, 1, 1)
        
        # Base query with optional client filtering
        base_query = session.query(Invoice)
        if self._should_filter_by_client():
            client_id = self._get_client_id()
            base_query = base_query.filter(Invoice.customer_id == client_id)
        
        # Total revenue MTD/YTD
        revenue_mtd = base_query.with_entities(
            func.sum(Invoice.total)
        ).filter(
            Invoice.invoice_date >= month_start
        ).scalar() or 0.0
        
        revenue_ytd = base_query.with_entities(
            func.sum(Invoice.total)
        ).filter(
            Invoice.invoice_date >= year_start
        ).scalar() or 0.0
        
        # Invoice counts MTD
        invoices_issued_mtd = base_query.filter(
            Invoice.invoice_date >= month_start
        ).count()
        
        invoices_paid_mtd = base_query.filter(
            Invoice.invoice_date >= month_start,
            Invoice.status == "paid"
        ).count()
        
        # Collection rate MTD
        collection_rate_mtd = (invoices_paid_mtd / invoices_issued_mtd * 100) if invoices_issued_mtd > 0 else 0
        
        # Average invoice value
        ytd_invoice_count = base_query.filter(Invoice.invoice_date >= year_start).count()
        avg_invoice_value = revenue_ytd / ytd_invoice_count if ytd_invoice_count > 0 else 0
        
        # Days Sales Outstanding (DSO)
        paid_invoices = base_query.filter(
            Invoice.status == "paid",
            Invoice.payment_date.isnot(None),
            Invoice.invoice_date >= year_start
        ).all()
        
        if paid_invoices:
            total_days = sum((inv.payment_date - inv.invoice_date).days for inv in paid_invoices)
            dso = int(total_days / len(paid_invoices))
        else:
            dso = 0
        
        # Overdue amount
        overdue_amount = base_query.with_entities(
            func.sum(Invoice.balance)
        ).filter(
            Invoice.status == "overdue"
        ).scalar() or 0.0
        
        # Disputed amount
        disputed_amount = base_query.with_entities(
            func.sum(Invoice.balance)
        ).filter(
            Invoice.status == "disputed"
        ).scalar() or 0.0
        
        return {
            "total_revenue_mtd": round(revenue_mtd, 2),
            "total_revenue_ytd": round(revenue_ytd, 2),
            "invoices_issued_mtd": invoices_issued_mtd,
            "invoices_paid_mtd": invoices_paid_mtd,
            "collection_rate_mtd": round(collection_rate_mtd, 1),
            "avg_invoice_value": round(avg_invoice_value, 2),
            "days_sales_outstanding": dso,
            "overdue_amount": round(overdue_amount, 2),
            "disputed_amount": round(disputed_amount, 2)
        }
    
    def _get_revenue_by_service(self, session) -> List[Dict[str, Any]]:
        """Get revenue breakdown by service type."""
        from models.billing_models import BillingLineItem
        
        now = datetime.utcnow()
        year_start = datetime(now.year, 1, 1)
        
        # Get all line items for YTD invoices with optional client filtering
        query = session.query(BillingLineItem).join(
            Invoice, BillingLineItem.invoice_id == Invoice.invoice_id
        ).filter(
            Invoice.invoice_date >= year_start
        )
        
        if self._should_filter_by_client():
            client_id = self._get_client_id()
            query = query.filter(Invoice.customer_id == client_id)
        
        line_items = query.all()
        
        # Group by service type
        service_revenue = {}
        total_revenue = 0
        
        for item in line_items:
            service_type = item.service_type
            if service_type not in service_revenue:
                service_revenue[service_type] = {"revenue": 0, "count": 0}
            service_revenue[service_type]["revenue"] += item.line_total
            service_revenue[service_type]["count"] += 1
            total_revenue += item.line_total
        
        # Convert to list with percentages
        result = []
        for service_type, data in service_revenue.items():
            pct = (data["revenue"] / total_revenue * 100) if total_revenue > 0 else 0
            result.append({
                "service_type": service_type,
                "revenue": round(data["revenue"], 2),
                "invoice_count": data["count"],
                "pct_of_total": round(pct, 1)
            })
        
        # Sort by revenue descending
        result.sort(key=lambda x: x["revenue"], reverse=True)
        
        return result
    
    def _get_invoice_status_metrics(self, session) -> List[Dict[str, Any]]:
        """Get invoice status breakdown."""
        now = datetime.utcnow()
        month_start = datetime(now.year, now.month, 1)
        
        # Get invoices by status for current month with optional client filtering
        query = session.query(
            Invoice.status,
            func.count(Invoice.id).label("count"),
            func.sum(Invoice.total).label("total_amount")
        ).filter(
            Invoice.invoice_date >= month_start
        )
        
        if self._should_filter_by_client():
            client_id = self._get_client_id()
            query = query.filter(Invoice.customer_id == client_id)
        
        statuses = query.group_by(Invoice.status).all()
        
        total_count = sum(s[1] for s in statuses)
        
        result = []
        for status, count, total_amount in statuses:
            pct = (count / total_count * 100) if total_count > 0 else 0
            result.append({
                "status": status,
                "count": count,
                "total_amount": round(total_amount or 0, 2),
                "pct_of_count": round(pct, 1)
            })
        
        return result
    
    def _get_billing_trends(self, session) -> List[Dict[str, Any]]:
        """Get billing trends for last 30 days."""
        now = datetime.utcnow()
        trends = []
        
        for days_ago in range(29, -1, -1):
            date = now - timedelta(days=days_ago)
            date_start = datetime(date.year, date.month, date.day)
            date_end = date_start + timedelta(days=1)
            
            # Revenue for the day
            revenue = session.query(
                func.sum(Invoice.total)
            ).filter(
                Invoice.invoice_date >= date_start,
                Invoice.invoice_date < date_end
            ).scalar() or 0.0
            
            # Invoices issued
            invoices_issued = session.query(Invoice).filter(
                Invoice.invoice_date >= date_start,
                Invoice.invoice_date < date_end
            ).count()
            
            # Invoices paid on this day
            invoices_paid = session.query(Invoice).filter(
                Invoice.payment_date >= date_start,
                Invoice.payment_date < date_end
            ).count()
            
            # Collection rate for the day
            collection_rate = (invoices_paid / invoices_issued * 100) if invoices_issued > 0 else 0
            
            trends.append({
                "date": date_start.strftime("%Y-%m-%d"),
                "revenue": round(revenue, 2),
                "invoices_issued": invoices_issued,
                "invoices_paid": invoices_paid,
                "collection_rate": round(collection_rate, 1)
            })
        
        return trends


    def get_warehouse_performance(self) -> Dict[str, Any]:
        """Get warehouse performance metrics."""
        logger.info("Generating warehouse performance dashboard")
        
        try:
            wms_session = get_wms_session(settings.wms_db_path)
            
            # Get inventory metrics
            inventory_metrics = self._get_inventory_metrics(wms_session)
            
            # Get picking metrics
            picking_metrics = self._get_picking_metrics(wms_session)
            
            # Get top performers
            top_performers = self._get_top_pickers(wms_session)
            
            # Get critical inventory items
            critical_inventory = self._get_critical_inventory(wms_session)
            
            # Calculate summary
            summary = {
                "picks_completed_today": picking_metrics["completed_today"],
                "pick_completion_rate": picking_metrics["completion_rate_pct"],
                "avg_pick_time": picking_metrics["avg_pick_time_minutes"],
                "inventory_accuracy": inventory_metrics["inventory_accuracy_pct"],
                "capacity_utilization": inventory_metrics["capacity_utilization_pct"],
                "items_below_reorder": inventory_metrics["below_reorder_point"],
                "top_performer": top_performers[0]["picker_name"] if top_performers else "N/A"
            }
            
            wms_session.close()
            
            return {
                "timestamp": datetime.utcnow(),
                "summary": summary,
                "inventory_metrics": inventory_metrics,
                "picking_metrics": picking_metrics,
                "top_performers": top_performers,
                "critical_inventory": critical_inventory
            }
        except Exception as e:
            logger.error(f"Error generating warehouse performance: {str(e)}")
            raise
    
    def _get_inventory_metrics(self, session) -> Dict[str, Any]:
        """Calculate inventory health metrics."""
        
        # Total SKUs and quantity
        total_skus = session.query(Inventory).count()
        total_quantity = session.query(func.sum(Inventory.quantity_on_hand)).scalar() or 0
        
        # Items below reorder point
        below_reorder = session.query(Inventory).filter(
            Inventory.quantity_available < Inventory.reorder_point,
            Inventory.quantity_available > 0
        ).count()
        
        # Out of stock items
        out_of_stock = session.query(Inventory).filter(
            Inventory.quantity_available == 0
        ).count()
        
        # Get latest metrics for accuracy and capacity
        latest_metrics = session.query(WarehouseMetrics).order_by(
            WarehouseMetrics.date.desc()
        ).first()
        
        if latest_metrics:
            inventory_accuracy = latest_metrics.inventory_accuracy_pct
            capacity_utilization = latest_metrics.capacity_utilization_pct
        else:
            inventory_accuracy = 99.0
            capacity_utilization = 75.0
        
        return {
            "total_skus": total_skus,
            "total_quantity": total_quantity,
            "below_reorder_point": below_reorder,
            "out_of_stock": out_of_stock,
            "inventory_accuracy_pct": round(inventory_accuracy, 1),
            "capacity_utilization_pct": round(capacity_utilization, 1)
        }
    
    def _get_picking_metrics(self, session) -> Dict[str, Any]:
        """Calculate picking performance metrics."""
        
        # Today's picks
        today = datetime.utcnow().date()
        today_start = datetime(today.year, today.month, today.day)
        
        total_tasks_today = session.query(PickingTask).filter(
            PickingTask.created_at >= today_start
        ).count()
        
        completed_today = session.query(PickingTask).filter(
            PickingTask.created_at >= today_start,
            PickingTask.status == "completed"
        ).count()
        
        pending = session.query(PickingTask).filter(
            PickingTask.status == "pending"
        ).count()
        
        delayed = session.query(PickingTask).filter(
            PickingTask.status == "delayed"
        ).count()
        
        # Completion rate
        completion_rate = (completed_today / total_tasks_today * 100) if total_tasks_today > 0 else 0
        
        # Average pick time (from completed tasks)
        completed_tasks = session.query(PickingTask).filter(
            PickingTask.status == "completed",
            PickingTask.completed_at.isnot(None)
        ).limit(100).all()
        
        if completed_tasks:
            total_time = sum((task.completed_at - task.created_at).total_seconds() / 60 for task in completed_tasks)
            avg_pick_time = total_time / len(completed_tasks)
        else:
            avg_pick_time = 0.0
        
        return {
            "total_tasks_today": total_tasks_today,
            "completed_today": completed_today,
            "pending": pending,
            "delayed": delayed,
            "completion_rate_pct": round(completion_rate, 1),
            "avg_pick_time_minutes": round(avg_pick_time, 1)
        }
    
    def _get_top_pickers(self, session) -> List[Dict[str, Any]]:
        """Get top performing pickers."""
        
        # Get pickers with most completions
        pickers = session.query(
            PickingTask.assigned_to,
            func.count(PickingTask.id).label("picks_completed")
        ).filter(
            PickingTask.status == "completed",
            PickingTask.assigned_to.isnot(None)
        ).group_by(PickingTask.assigned_to).order_by(
            func.count(PickingTask.id).desc()
        ).limit(5).all()
        
        result = []
        for picker_name, picks_completed in pickers:
            # Calculate average time for this picker
            picker_tasks = session.query(PickingTask).filter(
                PickingTask.assigned_to == picker_name,
                PickingTask.status == "completed",
                PickingTask.completed_at.isnot(None)
            ).limit(50).all()
            
            if picker_tasks:
                total_time = sum((task.completed_at - task.created_at).total_seconds() / 60 for task in picker_tasks)
                avg_time = total_time / len(picker_tasks)
            else:
                avg_time = 0.0
            
            result.append({
                "picker_name": picker_name,
                "picks_completed": picks_completed,
                "avg_time_minutes": round(avg_time, 1)
            })
        
        return result
    
    def _get_critical_inventory(self, session) -> List[Dict[str, Any]]:
        """Get critical inventory items (low stock and out of stock)."""
        
        # Get items below reorder point or out of stock
        critical_items = session.query(Inventory).filter(
            Inventory.quantity_available <= Inventory.reorder_point
        ).order_by(Inventory.quantity_available).limit(20).all()
        
        result = []
        for item in critical_items:
            # Determine status
            if item.quantity_available == 0:
                status = "out_of_stock"
            elif item.quantity_available < item.reorder_point * 0.25:
                status = "critical"
            elif item.quantity_available < item.reorder_point:
                status = "low"
            else:
                status = "ok"
            
            result.append({
                "sku": item.sku,
                "product_name": item.product_name,
                "location": item.warehouse_location,
                "quantity_on_hand": item.quantity_on_hand,
                "quantity_available": item.quantity_available,
                "reorder_point": item.reorder_point,
                "status": status
            })
        
        return result

    
    def _get_returns_exceptions(self) -> List[Dict[str, Any]]:
        """Get Returns exceptions."""
        session = get_returns_session(settings.returns_db_path)
        exceptions = []
        
        try:
            # Long pending returns
            old_returns = session.query(Return).filter(
                Return.status.in_(["initiated", "in_transit", "received"]),
                Return.return_date < datetime.utcnow() - timedelta(days=5)
            ).limit(10).all()
            
            for ret in old_returns:
                days_pending = (datetime.utcnow() - ret.return_date).days
                severity = "high" if days_pending > 7 else "medium"
                
                exceptions.append({
                    "id": f"RET-PND-{ret.id}",
                    "system": "Returns",
                    "severity": severity,
                    "category": "Returns Processing",
                    "title": f"Pending Return: {ret.return_id}",
                    "description": f"Return {ret.return_id} for {ret.customer_name} has been pending for {days_pending} days (Reason: {ret.reason})",
                    "affected_entity": ret.return_id,
                    "created_at": ret.return_date,
                    "status": "open",
                    "recommended_action": "Expedite return processing and inspection"
                })
        finally:
            session.close()
        
        return exceptions
    
    def _get_yard_exceptions(self) -> List[Dict[str, Any]]:
        """Get Yard exceptions."""
        session = get_yard_session(settings.yard_db_path)
        exceptions = []
        
        try:
            # Missed appointments
            missed_appointments = session.query(DockAppointment).filter(
                DockAppointment.status == "missed"
            ).limit(10).all()
            
            for appt in missed_appointments:
                exceptions.append({
                    "id": f"YARD-MIS-{appt.id}",
                    "system": "Yard",
                    "severity": "high",
                    "category": "Dock Operations",
                    "title": f"Missed Appointment: {appt.appointment_id}",
                    "description": f"Dock appointment {appt.appointment_id} with {appt.carrier} was missed (Scheduled: {appt.scheduled_time.strftime('%Y-%m-%d %H:%M')})",
                    "affected_entity": appt.appointment_id,
                    "created_at": appt.scheduled_time,
                    "status": "open",
                    "recommended_action": "Contact carrier to reschedule"
                })
            
            # Check for yard congestion
            total_locations = session.query(YardLocation).count()
            occupied = session.query(YardLocation).filter(
                YardLocation.status == "occupied"
            ).count()
            
            if total_locations > 0:
                utilization = (occupied / total_locations) * 100
                if utilization > 90:
                    exceptions.append({
                        "id": "YARD-CONG-001",
                        "system": "Yard",
                        "severity": "critical",
                        "category": "Capacity",
                        "title": "Yard Congestion Alert",
                        "description": f"Yard utilization at {utilization:.1f}% - approaching capacity",
                        "affected_entity": "Yard",
                        "created_at": datetime.utcnow(),
                        "status": "open",
                        "recommended_action": "Expedite outbound shipments or arrange overflow parking"
                    })
        finally:
            session.close()
        
        return exceptions

    def get_carrier_scorecard(self) -> Dict[str, Any]:
        """Get carrier performance scorecard with metrics and rankings."""
        logger.info("Generating carrier scorecard")
        
        try:
            carriers_data = self._get_carrier_metrics()
            summary = self._calculate_carrier_summary(carriers_data)
            trends = self._get_carrier_trends()
            
            return {
                "timestamp": datetime.utcnow(),
                "summary": summary,
                "carriers": carriers_data,
                "trends": trends
            }
        except Exception as e:
            logger.error(f"Error generating carrier scorecard: {e}", exc_info=True)
            raise

    def _get_carrier_metrics(self) -> List[Dict[str, Any]]:
        """Calculate performance metrics for each carrier."""
        session = get_tms_session(settings.tms_db_path)
        
        try:
            # Get all carriers with their shipment counts
            carriers = session.query(
                Shipment.carrier,
                func.count(Shipment.id).label("total_shipments")
            ).group_by(Shipment.carrier).all()
            
            carrier_metrics = []
            
            for carrier_name, total_shipments in carriers:
                # Get on-time and delayed deliveries
                on_time = session.query(Shipment).filter(
                    Shipment.carrier == carrier_name,
                    Shipment.status == "delivered",
                    Shipment.actual_delivery <= Shipment.estimated_delivery
                ).count()
                
                delayed = session.query(Shipment).filter(
                    Shipment.carrier == carrier_name,
                    Shipment.status.in_(["delayed", "delivered"]),
                    Shipment.actual_delivery > Shipment.estimated_delivery
                ).count()
                
                # Calculate on-time rate
                delivered_count = on_time + delayed
                on_time_rate = (on_time / delivered_count * 100) if delivered_count > 0 else 0
                
                # Calculate average transit time
                completed_shipments = session.query(Shipment).filter(
                    Shipment.carrier == carrier_name,
                    Shipment.actual_pickup.isnot(None),
                    Shipment.actual_delivery.isnot(None)
                ).all()
                
                if completed_shipments:
                    total_hours = sum([
                        (s.actual_delivery - s.actual_pickup).total_seconds() / 3600
                        for s in completed_shipments
                    ])
                    avg_transit_time = total_hours / len(completed_shipments)
                else:
                    avg_transit_time = 0
                
                # Calculate costs
                total_cost = session.query(func.sum(Shipment.cost)).filter(
                    Shipment.carrier == carrier_name
                ).scalar() or 0
                
                cost_per_shipment = total_cost / total_shipments if total_shipments > 0 else 0
                
                # Active shipments and exceptions
                active = session.query(Shipment).filter(
                    Shipment.carrier == carrier_name,
                    Shipment.status.in_(["scheduled", "in_transit"])
                ).count()
                
                exceptions = session.query(Shipment).filter(
                    Shipment.carrier == carrier_name,
                    Shipment.status.in_(["delayed", "exception"])
                ).count()
                
                # Calculate performance score (0-100)
                # Weighted: 50% on-time rate, 30% cost efficiency, 20% exception rate
                exception_rate = (exceptions / total_shipments * 100) if total_shipments > 0 else 0
                
                # Cost efficiency score (compare to average)
                avg_cost_all = session.query(func.avg(Shipment.cost)).scalar() or 100
                cost_score = max(0, 100 - ((cost_per_shipment - avg_cost_all) / avg_cost_all * 100))
                
                performance_score = (
                    on_time_rate * 0.5 +
                    cost_score * 0.3 +
                    max(0, 100 - exception_rate * 5) * 0.2
                )
                
                # Determine status
                if performance_score >= 90:
                    status = "excellent"
                elif performance_score >= 75:
                    status = "good"
                elif performance_score >= 60:
                    status = "fair"
                else:
                    status = "poor"
                
                carrier_metrics.append({
                    "carrier_name": carrier_name,
                    "total_shipments": total_shipments,
                    "on_time_deliveries": on_time,
                    "delayed_deliveries": delayed,
                    "on_time_rate_pct": round(on_time_rate, 1),
                    "avg_transit_time_hours": round(avg_transit_time, 1),
                    "total_cost": round(total_cost, 2),
                    "cost_per_shipment": round(cost_per_shipment, 2),
                    "active_shipments": active,
                    "exceptions": exceptions,
                    "performance_score": round(performance_score, 1),
                    "status": status
                })
            
            # Sort by performance score descending
            carrier_metrics.sort(key=lambda x: x["performance_score"], reverse=True)
            
            return carrier_metrics
            
        finally:
            session.close()

    def _calculate_carrier_summary(self, carriers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for all carriers."""
        if not carriers:
            return {
                "total_carriers": 0,
                "total_shipments": 0,
                "overall_on_time_rate": 0,
                "avg_cost_per_shipment": 0,
                "best_performer": "N/A",
                "worst_performer": "N/A",
                "total_exceptions": 0
            }
        
        total_shipments = sum(c["total_shipments"] for c in carriers)
        total_on_time = sum(c["on_time_deliveries"] for c in carriers)
        total_cost = sum(c["total_cost"] for c in carriers)
        total_exceptions = sum(c["exceptions"] for c in carriers)
        
        overall_on_time_rate = (total_on_time / total_shipments * 100) if total_shipments > 0 else 0
        avg_cost_per_shipment = total_cost / total_shipments if total_shipments > 0 else 0
        
        best_performer = carriers[0]["carrier_name"] if carriers else "N/A"
        worst_performer = carriers[-1]["carrier_name"] if carriers else "N/A"
        
        return {
            "total_carriers": len(carriers),
            "total_shipments": total_shipments,
            "overall_on_time_rate": round(overall_on_time_rate, 1),
            "avg_cost_per_shipment": round(avg_cost_per_shipment, 2),
            "best_performer": best_performer,
            "worst_performer": worst_performer,
            "total_exceptions": total_exceptions
        }

    def _get_carrier_trends(self) -> List[Dict[str, Any]]:
        """Get carrier performance trends over the last 30 days."""
        session = get_tms_session(settings.tms_db_path)
        
        try:
            trends = []
            # Prefer daily transport metrics for KPI-accurate trend lines.
            latest_metric_date = session.query(func.max(TransportMetrics.date)).scalar()
            latest_delivery = session.query(func.max(Shipment.actual_delivery)).filter(
                Shipment.actual_delivery.isnot(None)
            ).scalar()

            if latest_metric_date:
                today = min(latest_metric_date.date(), datetime.utcnow().date())
            elif latest_delivery:
                today = latest_delivery.date()
            else:
                today = datetime.utcnow().date()
            
            for days_ago in range(29, -1, -1):
                date = today - timedelta(days=days_ago)
                date_start = datetime.combine(date, datetime.min.time())
                date_end = datetime.combine(date, datetime.max.time())

                metric = session.query(TransportMetrics).filter(
                    TransportMetrics.date >= date_start,
                    TransportMetrics.date <= date_end
                ).order_by(TransportMetrics.date.desc()).first()

                if metric:
                    on_time_rate = metric.on_time_delivery_pct
                    shipment_count = metric.total_shipments
                else:
                    # Fallback to shipment-level computation if no daily metric exists.
                    delivered = session.query(Shipment).filter(
                        Shipment.actual_delivery >= date_start,
                        Shipment.actual_delivery <= date_end,
                        Shipment.actual_delivery.isnot(None)
                    ).all()

                    shipment_count = len(delivered)
                    if delivered:
                        on_time_count = sum(1 for s in delivered if s.actual_delivery <= s.estimated_delivery)
                        on_time_rate = (on_time_count / shipment_count * 100)
                    else:
                        on_time_rate = 0
                
                trends.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "on_time_rate": round(on_time_rate, 1),
                    "shipment_count": shipment_count
                })
            
            return trends
            
        finally:
            session.close()

    def get_labor_efficiency(self) -> Dict[str, Any]:
        """Get labor efficiency metrics and worker performance."""
        logger.info("Generating labor efficiency dashboard")
        
        try:
            workers_data = self._get_worker_metrics()
            summary = self._calculate_labor_summary(workers_data)
            hourly_trends = self._get_hourly_productivity()
            task_breakdown = self._get_task_breakdown()
            
            return {
                "timestamp": datetime.utcnow(),
                "summary": summary,
                "workers": workers_data,
                "hourly_trends": hourly_trends,
                "task_breakdown": task_breakdown
            }
        except Exception as e:
            logger.error(f"Error generating labor efficiency: {e}", exc_info=True)
            raise

    def _get_worker_metrics(self) -> List[Dict[str, Any]]:
        """Calculate performance metrics for each worker."""
        session = get_wms_session(settings.wms_db_path)
        
        try:
            # Use last 24 hours instead of strict "today" to ensure we have data
            twenty_four_hours_ago = datetime.utcnow() - timedelta(hours=24)
            
            # Get all workers who have tasks assigned
            workers = session.query(PickingTask.assigned_to).filter(
                PickingTask.assigned_to.isnot(None)
            ).distinct().all()
            
            worker_metrics = []
            
            for (worker_name,) in workers:
                if not worker_name:
                    continue
                
                # Get recent tasks (last 24 hours)
                recent_tasks = session.query(PickingTask).filter(
                    PickingTask.assigned_to == worker_name,
                    PickingTask.created_at >= twenty_four_hours_ago
                ).all()
                
                tasks_assigned = len(recent_tasks)
                
                # Skip workers with no recent tasks
                if tasks_assigned == 0:
                    continue
                
                tasks_completed = sum(1 for t in recent_tasks if t.status == "completed")
                tasks_delayed = sum(1 for t in recent_tasks if t.status == "delayed")
                
                completion_rate = (tasks_completed / tasks_assigned * 100) if tasks_assigned > 0 else 0
                
                # Calculate average time per task for completed tasks
                completed_tasks = [t for t in recent_tasks if t.status == "completed" and t.completed_at]
                if completed_tasks:
                    total_minutes = sum([
                        (t.completed_at - t.created_at).total_seconds() / 60
                        for t in completed_tasks
                    ])
                    avg_time = total_minutes / len(completed_tasks)
                else:
                    avg_time = 0
                
                # Estimate hours worked (based on task times)
                if completed_tasks:
                    first_task = min(completed_tasks, key=lambda t: t.created_at)
                    last_task = max(completed_tasks, key=lambda t: t.completed_at)
                    hours_worked = (last_task.completed_at - first_task.created_at).total_seconds() / 3600
                else:
                    hours_worked = 0
                
                # Calculate productivity score (0-100)
                # Factors: completion rate (50%), speed (30%), delayed tasks penalty (20%)
                
                # Speed score: Target is 5-10 minutes per task
                if avg_time > 0:
                    if avg_time <= 5:
                        speed_score = 100
                    elif avg_time <= 10:
                        speed_score = 90 - (avg_time - 5) * 4  # 90-70 range
                    elif avg_time <= 15:
                        speed_score = 70 - (avg_time - 10) * 3  # 70-55 range
                    else:
                        speed_score = max(0, 55 - (avg_time - 15) * 2)
                else:
                    # No completed tasks, use completion rate as indicator
                    speed_score = completion_rate * 0.5  # Partial credit based on completion
                
                delay_penalty = (tasks_delayed / tasks_assigned * 100) if tasks_assigned > 0 else 0
                
                productivity_score = (
                    completion_rate * 0.5 +
                    speed_score * 0.3 +
                    max(0, 100 - delay_penalty * 3) * 0.2
                )
                
                # Determine status
                if productivity_score >= 85:
                    status = "excellent"
                elif productivity_score >= 70:
                    status = "good"
                elif productivity_score >= 55:
                    status = "average"
                else:
                    status = "needs_improvement"
                
                worker_metrics.append({
                    "worker_name": worker_name,
                    "tasks_assigned": tasks_assigned,
                    "tasks_completed": tasks_completed,
                    "tasks_delayed": tasks_delayed,
                    "completion_rate_pct": round(completion_rate, 1),
                    "avg_time_per_task_minutes": round(avg_time, 1),
                    "total_hours_worked": round(hours_worked, 1),
                    "productivity_score": round(productivity_score, 1),
                    "status": status
                })
            
            # Sort by productivity score descending
            worker_metrics.sort(key=lambda x: x["productivity_score"], reverse=True)
            
            return worker_metrics
            
        finally:
            session.close()

    def _calculate_labor_summary(self, workers: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for labor efficiency."""
        if not workers:
            return {
                "total_workers": 0,
                "total_tasks_today": 0,
                "tasks_completed_today": 0,
                "overall_completion_rate": 0,
                "avg_productivity_score": 0,
                "labor_utilization_pct": 0,
                "top_performer": "N/A",
                "workers_needing_support": 0
            }
        
        total_tasks = sum(w["tasks_assigned"] for w in workers)
        tasks_completed = sum(w["tasks_completed"] for w in workers)
        avg_score = sum(w["productivity_score"] for w in workers) / len(workers)
        
        overall_completion_rate = (tasks_completed / total_tasks * 100) if total_tasks > 0 else 0
        
        # Labor utilization based on hours worked
        total_hours = sum(w["total_hours_worked"] for w in workers)
        expected_hours = len(workers) * 8  # Assume 8-hour shifts
        labor_utilization = (total_hours / expected_hours * 100) if expected_hours > 0 else 0
        
        top_performer = workers[0]["worker_name"] if workers else "N/A"
        workers_needing_support = sum(1 for w in workers if w["status"] == "needs_improvement")
        
        return {
            "total_workers": len(workers),
            "total_tasks_today": total_tasks,
            "tasks_completed_today": tasks_completed,
            "overall_completion_rate": round(overall_completion_rate, 1),
            "avg_productivity_score": round(avg_score, 1),
            "labor_utilization_pct": round(labor_utilization, 1),
            "top_performer": top_performer,
            "workers_needing_support": workers_needing_support
        }

    def _get_hourly_productivity(self) -> List[Dict[str, Any]]:
        """Get productivity trends by hour of day."""
        session = get_wms_session(settings.wms_db_path)
        
        try:
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())
            
            hourly_data = []
            
            for hour in range(8, 18):  # 8 AM to 6 PM
                hour_start = datetime.combine(today, datetime.min.time().replace(hour=hour))
                hour_end = datetime.combine(today, datetime.min.time().replace(hour=hour + 1))
                
                # Get tasks completed in this hour
                tasks = session.query(PickingTask).filter(
                    PickingTask.status == "completed",
                    PickingTask.completed_at >= hour_start,
                    PickingTask.completed_at < hour_end
                ).all()
                
                if tasks:
                    avg_time = sum([
                        (t.completed_at - t.created_at).total_seconds() / 60
                        for t in tasks
                    ]) / len(tasks)
                    
                    # Count unique workers in this hour
                    worker_count = len(set(t.assigned_to for t in tasks if t.assigned_to))
                else:
                    avg_time = 0
                    worker_count = 0
                
                hourly_data.append({
                    "hour": f"{hour:02d}:00",
                    "tasks_completed": len(tasks),
                    "avg_time_minutes": round(avg_time, 1),
                    "worker_count": worker_count
                })
            
            return hourly_data
            
        finally:
            session.close()

    def _get_task_breakdown(self) -> List[Dict[str, Any]]:
        """Get task breakdown by status."""
        session = get_wms_session(settings.wms_db_path)
        
        try:
            today = datetime.utcnow().date()
            today_start = datetime.combine(today, datetime.min.time())
            
            # Get all tasks for today
            total_tasks = session.query(PickingTask).filter(
                PickingTask.created_at >= today_start
            ).count()
            
            if total_tasks == 0:
                return []
            
            # Count by status
            statuses = ["completed", "in_progress", "pending", "delayed"]
            breakdown = []
            
            for status in statuses:
                count = session.query(PickingTask).filter(
                    PickingTask.created_at >= today_start,
                    PickingTask.status == status
                ).count()
                
                percentage = (count / total_tasks * 100) if total_tasks > 0 else 0
                
                breakdown.append({
                    "status": status,
                    "count": count,
                    "percentage": round(percentage, 1)
                })
            
            return breakdown
            
        finally:
            session.close()

    def get_inventory_optimization(self) -> Dict[str, Any]:
        """Get inventory optimization analysis and recommendations."""
        logger.info("Generating inventory optimization dashboard")
        
        try:
            items_data = self._get_inventory_analysis()
            summary = self._calculate_inventory_summary(items_data)
            turnover_categories = self._get_turnover_categories(items_data)
            abc_analysis = self._get_abc_analysis(items_data)
            
            return {
                "timestamp": datetime.utcnow(),
                "summary": summary,
                "items": items_data,
                "turnover_categories": turnover_categories,
                "abc_analysis": abc_analysis
            }
        except Exception as e:
            logger.error(f"Error generating inventory optimization: {e}", exc_info=True)
            raise

    def _get_inventory_analysis(self) -> List[Dict[str, Any]]:
        """Analyze inventory items and provide recommendations."""
        session = get_wms_session(settings.wms_db_path)
        
        try:
            inventory_items = session.query(Inventory).all()
            analysis = []
            
            for item in inventory_items:
                # Calculate days of supply (assuming avg daily demand = reorder_point / 30)
                avg_daily_demand = item.reorder_point / 30 if item.reorder_point > 0 else 1
                days_of_supply = item.quantity_available / avg_daily_demand if avg_daily_demand > 0 else 0
                
                # Calculate turnover rate (annual, assuming 30-day cycle)
                # Higher turnover = faster moving inventory
                if item.quantity_on_hand > 0:
                    turnover_rate = (avg_daily_demand * 365) / item.quantity_on_hand
                else:
                    turnover_rate = 0
                
                # Estimate holding cost (assume $2 per unit per month for storage)
                holding_cost_monthly = item.quantity_on_hand * 2.0
                
                # Determine status and recommendation
                if item.quantity_available <= 0:
                    status = "critical"
                    recommendation = "URGENT: Out of stock. Expedite replenishment order immediately."
                elif item.quantity_available < item.reorder_point * 0.5:
                    status = "understocked"
                    recommendation = "Place reorder now. Stock below optimal levels."
                elif days_of_supply > 90:
                    status = "overstocked"
                    recommendation = f"Reduce stock levels. {int(days_of_supply)} days of supply exceeds target."
                elif days_of_supply > 60:
                    status = "overstocked"
                    recommendation = "Consider reducing future orders. Excess inventory detected."
                else:
                    status = "optimal"
                    recommendation = "Inventory levels are within optimal range."
                
                analysis.append({
                    "sku": item.sku,
                    "product_name": item.product_name,
                    "location": item.warehouse_location,
                    "quantity_on_hand": item.quantity_on_hand,
                    "quantity_available": item.quantity_available,
                    "quantity_reserved": item.quantity_reserved,
                    "reorder_point": item.reorder_point,
                    "days_of_supply": round(days_of_supply, 1),
                    "turnover_rate": round(turnover_rate, 2),
                    "holding_cost_monthly": round(holding_cost_monthly, 2),
                    "status": status,
                    "recommendation": recommendation
                })
            
            # Sort by status priority (critical first)
            status_priority = {"critical": 0, "understocked": 1, "overstocked": 2, "optimal": 3}
            analysis.sort(key=lambda x: (status_priority.get(x["status"], 4), -x["quantity_on_hand"]))
            
            return analysis
            
        finally:
            session.close()

    def _calculate_inventory_summary(self, items: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for inventory optimization."""
        if not items:
            return {
                "total_skus": 0,
                "total_value": 0,
                "avg_turnover_rate": 0,
                "optimal_items": 0,
                "overstocked_items": 0,
                "understocked_items": 0,
                "critical_items": 0,
                "total_holding_cost": 0,
                "potential_savings": 0
            }
        
        total_skus = len(items)
        
        # Estimate value (assume $25 per unit average)
        total_value = sum(item["quantity_on_hand"] for item in items) * 25
        
        avg_turnover = sum(item["turnover_rate"] for item in items) / total_skus
        
        optimal_items = sum(1 for item in items if item["status"] == "optimal")
        overstocked_items = sum(1 for item in items if item["status"] == "overstocked")
        understocked_items = sum(1 for item in items if item["status"] == "understocked")
        critical_items = sum(1 for item in items if item["status"] == "critical")
        
        total_holding_cost = sum(item["holding_cost_monthly"] for item in items)
        
        # Estimate potential savings by reducing overstocked items by 30%
        overstocked_cost = sum(
            item["holding_cost_monthly"] 
            for item in items 
            if item["status"] == "overstocked"
        )
        potential_savings = overstocked_cost * 0.3
        
        return {
            "total_skus": total_skus,
            "total_value": round(total_value, 2),
            "avg_turnover_rate": round(avg_turnover, 2),
            "optimal_items": optimal_items,
            "overstocked_items": overstocked_items,
            "understocked_items": understocked_items,
            "critical_items": critical_items,
            "total_holding_cost": round(total_holding_cost, 2),
            "potential_savings": round(potential_savings, 2)
        }

    def _get_turnover_categories(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Categorize inventory by turnover rate."""
        if not items:
            return []
        
        # Define turnover categories
        fast_moving = [item for item in items if item["turnover_rate"] >= 8]
        medium_moving = [item for item in items if 3 <= item["turnover_rate"] < 8]
        slow_moving = [item for item in items if 1 <= item["turnover_rate"] < 3]
        very_slow = [item for item in items if item["turnover_rate"] < 1]
        
        total = len(items)
        
        categories = []
        
        for category_name, category_items in [
            ("Fast Moving (≥8x/year)", fast_moving),
            ("Medium Moving (3-8x/year)", medium_moving),
            ("Slow Moving (1-3x/year)", slow_moving),
            ("Very Slow (<1x/year)", very_slow)
        ]:
            count = len(category_items)
            percentage = (count / total * 100) if total > 0 else 0
            avg_turnover = (sum(item["turnover_rate"] for item in category_items) / count) if count > 0 else 0
            
            categories.append({
                "category": category_name,
                "count": count,
                "percentage": round(percentage, 1),
                "avg_turnover": round(avg_turnover, 2)
            })
        
        return categories

    def _get_abc_analysis(self, items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Perform ABC analysis on inventory."""
        if not items:
            return []
        
        # Sort by value (quantity * assumed unit price)
        items_with_value = [(item, item["quantity_on_hand"] * 25) for item in items]
        items_with_value.sort(key=lambda x: x[1], reverse=True)
        
        total_value = sum(value for _, value in items_with_value)
        
        # Calculate cumulative percentages
        cumulative = 0
        a_items = 0
        b_items = 0
        c_items = 0
        
        for item, value in items_with_value:
            cumulative += value / total_value * 100
            if cumulative <= 80:
                a_items += 1
            elif cumulative <= 95:
                b_items += 1
            else:
                c_items += 1
        
        total_items = len(items)
        
        return [
            {
                "category": "A",
                "sku_count": a_items,
                "value_percentage": 80.0,
                "description": "High value items (80% of inventory value)"
            },
            {
                "category": "B",
                "sku_count": b_items,
                "value_percentage": 15.0,
                "description": "Medium value items (15% of inventory value)"
            },
            {
                "category": "C",
                "sku_count": c_items,
                "value_percentage": 5.0,
                "description": "Low value items (5% of inventory value)"
            }
        ]

    def get_standard_reports(self) -> Dict[str, Any]:
        """Get available standard reports catalog."""
        logger.info("Generating standard reports catalog")
        
        try:
            reports = self._get_report_templates()
            summary = self._calculate_reports_summary(reports)
            categories = self._get_report_categories()
            
            return {
                "timestamp": datetime.utcnow(),
                "summary": summary,
                "reports": reports,
                "categories": categories
            }
        except Exception as e:
            logger.error(f"Error generating standard reports: {e}", exc_info=True)
            raise

    def _get_report_templates(self) -> List[Dict[str, Any]]:
        """Get list of available standard report templates."""
        
        # Define standard report templates
        templates = [
            {
                "report_id": "RPT-001",
                "report_name": "Daily Operations Summary",
                "category": "operational",
                "description": "Comprehensive daily operations overview including orders, shipments, and warehouse activities",
                "frequency": "daily",
                "last_run": datetime.utcnow() - timedelta(hours=2),
                "status": "completed",
                "record_count": 1245,
                "file_size_kb": 156,
                "format": "pdf"
            },
            {
                "report_id": "RPT-002",
                "report_name": "Inventory Valuation Report",
                "category": "inventory",
                "description": "Complete inventory valuation with on-hand quantities, costs, and total value",
                "frequency": "monthly",
                "last_run": datetime.utcnow() - timedelta(days=2),
                "status": "completed",
                "record_count": 850,
                "file_size_kb": 245,
                "format": "excel"
            },
            {
                "report_id": "RPT-003",
                "report_name": "Shipment Performance Report",
                "category": "transportation",
                "description": "Carrier performance metrics, on-time delivery rates, and transit time analysis",
                "frequency": "weekly",
                "last_run": datetime.utcnow() - timedelta(days=1),
                "status": "completed",
                "record_count": 450,
                "file_size_kb": 198,
                "format": "pdf"
            },
            {
                "report_id": "RPT-004",
                "report_name": "Revenue & Billing Report",
                "category": "financial",
                "description": "Revenue breakdown by service type, billing status, and payment collection metrics",
                "frequency": "monthly",
                "last_run": datetime.utcnow() - timedelta(days=3),
                "status": "completed",
                "record_count": 320,
                "file_size_kb": 178,
                "format": "excel"
            },
            {
                "report_id": "RPT-005",
                "report_name": "Exception Analysis Report",
                "category": "operational",
                "description": "Detailed analysis of operational exceptions across all systems with root cause trends",
                "frequency": "weekly",
                "last_run": datetime.utcnow() - timedelta(hours=12),
                "status": "completed",
                "record_count": 186,
                "file_size_kb": 124,
                "format": "pdf"
            },
            {
                "report_id": "RPT-006",
                "report_name": "Labor Productivity Report",
                "category": "operational",
                "description": "Worker performance metrics, productivity scores, and labor utilization analysis",
                "frequency": "daily",
                "last_run": datetime.utcnow() - timedelta(hours=6),
                "status": "completed",
                "record_count": 95,
                "file_size_kb": 86,
                "format": "excel"
            },
            {
                "report_id": "RPT-007",
                "report_name": "Inventory Turnover Report",
                "category": "inventory",
                "description": "SKU-level turnover rates, days of supply, and slow-moving inventory identification",
                "frequency": "monthly",
                "last_run": datetime.utcnow() - timedelta(days=5),
                "status": "completed",
                "record_count": 850,
                "file_size_kb": 312,
                "format": "excel"
            },
            {
                "report_id": "RPT-008",
                "report_name": "Order Fulfillment Report",
                "category": "operational",
                "description": "Order processing times, fulfillment rates, and backorder analysis",
                "frequency": "daily",
                "last_run": datetime.utcnow() - timedelta(hours=4),
                "status": "completed",
                "record_count": 625,
                "file_size_kb": 145,
                "format": "pdf"
            },
            {
                "report_id": "RPT-009",
                "report_name": "Carrier Cost Analysis",
                "category": "transportation",
                "description": "Detailed carrier cost breakdown, cost per shipment, and budget variance analysis",
                "frequency": "monthly",
                "last_run": datetime.utcnow() - timedelta(days=4),
                "status": "completed",
                "record_count": 380,
                "file_size_kb": 267,
                "format": "excel"
            },
            {
                "report_id": "RPT-010",
                "report_name": "Returns Analysis Report",
                "category": "operational",
                "description": "Return trends, reasons, processing times, and recovery rates",
                "frequency": "weekly",
                "last_run": datetime.utcnow() - timedelta(days=2),
                "status": "completed",
                "record_count": 142,
                "file_size_kb": 95,
                "format": "pdf"
            },
            {
                "report_id": "RPT-011",
                "report_name": "Dock Scheduling Report",
                "category": "operational",
                "description": "Dock appointment utilization, on-time arrivals, and capacity planning metrics",
                "frequency": "weekly",
                "last_run": datetime.utcnow() - timedelta(hours=18),
                "status": "completed",
                "record_count": 215,
                "file_size_kb": 118,
                "format": "excel"
            },
            {
                "report_id": "RPT-012",
                "report_name": "Client Profitability Report",
                "category": "financial",
                "description": "Per-client revenue, costs, margins, and service level performance",
                "frequency": "monthly",
                "last_run": datetime.utcnow() - timedelta(days=6),
                "status": "completed",
                "record_count": 48,
                "file_size_kb": 156,
                "format": "excel"
            },
            {
                "report_id": "RPT-013",
                "report_name": "Accessorial Charges Report",
                "category": "financial",
                "description": "Recovery opportunities for detention, redelivery, and other accessorial charges",
                "frequency": "on_demand",
                "last_run": datetime.utcnow() - timedelta(hours=8),
                "status": "completed",
                "record_count": 45,
                "file_size_kb": 72,
                "format": "pdf"
            },
            {
                "report_id": "RPT-014",
                "report_name": "KPI Dashboard Export",
                "category": "operational",
                "description": "Full KPI metrics export across all operational areas",
                "frequency": "on_demand",
                "last_run": datetime.utcnow() - timedelta(days=1),
                "status": "available",
                "record_count": 0,
                "file_size_kb": 0,
                "format": "csv"
            },
            {
                "report_id": "RPT-015",
                "report_name": "Capacity Utilization Report",
                "category": "operational",
                "description": "Warehouse and dock capacity utilization trends and forecasts",
                "frequency": "weekly",
                "last_run": datetime.utcnow() - timedelta(days=3),
                "status": "completed",
                "record_count": 168,
                "file_size_kb": 134,
                "format": "pdf"
            }
        ]
        
        return templates

    def _calculate_reports_summary(self, reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for standard reports."""
        
        total_reports = len(reports)
        available_reports = sum(1 for r in reports if r["status"] in ["available", "completed"])
        scheduled_reports = sum(1 for r in reports if r["frequency"] in ["daily", "weekly", "monthly"])
        
        # Count reports run today
        today = datetime.utcnow().date()
        reports_run_today = sum(
            1 for r in reports 
            if r["last_run"] and r["last_run"].date() == today
        )
        
        # Simulate total downloads
        total_downloads = sum(r["record_count"] for r in reports if r["status"] == "completed")
        
        return {
            "total_reports": total_reports,
            "available_reports": available_reports,
            "scheduled_reports": scheduled_reports,
            "reports_run_today": reports_run_today,
            "total_downloads": total_downloads
        }

    def _get_report_categories(self) -> List[Dict[str, Any]]:
        """Get report category breakdown."""
        
        categories = [
            {
                "category": "operational",
                "count": 7,
                "description": "Daily operations, exceptions, labor, and fulfillment reports"
            },
            {
                "category": "financial",
                "count": 3,
                "description": "Revenue, billing, profitability, and cost analysis reports"
            },
            {
                "category": "inventory",
                "count": 2,
                "description": "Inventory valuation, turnover, and optimization reports"
            },
            {
                "category": "transportation",
                "count": 2,
                "description": "Carrier performance, costs, and shipment analysis reports"
            }
        ]
        
        return categories

    async def get_custom_reports(self) -> Dict[str, Any]:
        """
        Get custom report builder configuration.
        
        Returns:
            Dict containing data sources, available fields, and saved reports
        """
        
        data_sources = self._get_data_sources()
        available_fields = self._get_available_fields()
        saved_reports = self._get_saved_reports()
        summary = self._calculate_custom_reports_summary(saved_reports)
        
        return {
            "timestamp": datetime.utcnow(),
            "summary": summary,
            "data_sources": data_sources,
            "available_fields": available_fields,
            "saved_reports": saved_reports
        }

    def _get_data_sources(self) -> List[Dict[str, Any]]:
        """Get available data sources for custom reports."""
        
        data_sources = [
            {
                "source_id": "SRC-001",
                "source_name": "Orders Management",
                "source_type": "database",
                "description": "Order processing, fulfillment, and tracking data",
                "table_count": 5,
                "record_count": 12450,
                "available_fields": 42
            },
            {
                "source_id": "SRC-002",
                "source_name": "Warehouse Management",
                "source_type": "database",
                "description": "Inventory, picking, putaway, and storage data",
                "table_count": 8,
                "record_count": 8760,
                "available_fields": 56
            },
            {
                "source_id": "SRC-003",
                "source_name": "Transportation",
                "source_type": "database",
                "description": "Shipments, carriers, routes, and delivery data",
                "table_count": 6,
                "record_count": 15230,
                "available_fields": 38
            },
            {
                "source_id": "SRC-004",
                "source_name": "Billing & Finance",
                "source_type": "database",
                "description": "Invoices, payments, and financial transactions",
                "table_count": 4,
                "record_count": 9845,
                "available_fields": 28
            },
            {
                "source_id": "SRC-005",
                "source_name": "Returns Management",
                "source_type": "database",
                "description": "Return authorizations, inspections, and dispositions",
                "table_count": 3,
                "record_count": 3420,
                "available_fields": 24
            },
            {
                "source_id": "SRC-006",
                "source_name": "Yard Management",
                "source_type": "database",
                "description": "Dock appointments, trailer tracking, and yard moves",
                "table_count": 4,
                "record_count": 5680,
                "available_fields": 32
            }
        ]
        
        return data_sources

    def _get_available_fields(self) -> List[Dict[str, Any]]:
        """Get available fields for custom report building."""
        
        fields = [
            # Order fields
            {"field_id": "FLD-001", "field_name": "Order ID", "field_type": "text", "source": "Orders Management", "description": "Unique order identifier", "is_selected": False},
            {"field_id": "FLD-002", "field_name": "Order Date", "field_type": "date", "source": "Orders Management", "description": "Order placement date", "is_selected": False},
            {"field_id": "FLD-003", "field_name": "Customer Name", "field_type": "text", "source": "Orders Management", "description": "Customer name", "is_selected": False},
            {"field_id": "FLD-004", "field_name": "Order Status", "field_type": "text", "source": "Orders Management", "description": "Current order status", "is_selected": False},
            {"field_id": "FLD-005", "field_name": "Order Total", "field_type": "number", "source": "Orders Management", "description": "Total order value", "is_selected": False},
            
            # Inventory fields
            {"field_id": "FLD-006", "field_name": "SKU", "field_type": "text", "source": "Warehouse Management", "description": "Stock keeping unit", "is_selected": False},
            {"field_id": "FLD-007", "field_name": "Product Name", "field_type": "text", "source": "Warehouse Management", "description": "Product description", "is_selected": False},
            {"field_id": "FLD-008", "field_name": "Quantity On Hand", "field_type": "number", "source": "Warehouse Management", "description": "Current inventory quantity", "is_selected": False},
            {"field_id": "FLD-009", "field_name": "Location", "field_type": "text", "source": "Warehouse Management", "description": "Warehouse location", "is_selected": False},
            {"field_id": "FLD-010", "field_name": "Unit Cost", "field_type": "number", "source": "Warehouse Management", "description": "Per-unit cost", "is_selected": False},
            
            # Shipment fields
            {"field_id": "FLD-011", "field_name": "Tracking Number", "field_type": "text", "source": "Transportation", "description": "Shipment tracking ID", "is_selected": False},
            {"field_id": "FLD-012", "field_name": "Carrier", "field_type": "text", "source": "Transportation", "description": "Shipping carrier name", "is_selected": False},
            {"field_id": "FLD-013", "field_name": "Ship Date", "field_type": "date", "source": "Transportation", "description": "Shipment date", "is_selected": False},
            {"field_id": "FLD-014", "field_name": "Delivery Date", "field_type": "date", "source": "Transportation", "description": "Actual delivery date", "is_selected": False},
            {"field_id": "FLD-015", "field_name": "Freight Cost", "field_type": "number", "source": "Transportation", "description": "Shipping cost", "is_selected": False},
            
            # Financial fields
            {"field_id": "FLD-016", "field_name": "Invoice Number", "field_type": "text", "source": "Billing & Finance", "description": "Invoice identifier", "is_selected": False},
            {"field_id": "FLD-017", "field_name": "Invoice Date", "field_type": "date", "source": "Billing & Finance", "description": "Invoice issue date", "is_selected": False},
            {"field_id": "FLD-018", "field_name": "Invoice Amount", "field_type": "number", "source": "Billing & Finance", "description": "Total invoice amount", "is_selected": False},
            {"field_id": "FLD-019", "field_name": "Payment Status", "field_type": "text", "source": "Billing & Finance", "description": "Payment status", "is_selected": False},
            {"field_id": "FLD-020", "field_name": "Payment Date", "field_type": "date", "source": "Billing & Finance", "description": "Date payment received", "is_selected": False}
        ]
        
        return fields

    def _get_saved_reports(self) -> List[Dict[str, Any]]:
        """Get user's saved custom reports."""
        
        now = datetime.utcnow()
        
        saved_reports = [
            {
                "report_id": "CUST-001",
                "report_name": "Monthly Order Summary",
                "created_by": "john.smith@company.com",
                "created_date": now - timedelta(days=45),
                "last_modified": now - timedelta(days=12),
                "data_sources": ["Orders Management", "Warehouse Management"],
                "selected_fields": ["Order ID", "Order Date", "Customer Name", "Order Total", "Order Status"],
                "filters": [
                    {"filter_id": "F1", "field": "Order Date", "operator": "between", "value": "last_30_days", "is_active": True}
                ],
                "group_by": ["Order Status"],
                "sort_by": ["Order Date"],
                "format": "excel",
                "is_scheduled": True,
                "run_count": 12
            },
            {
                "report_id": "CUST-002",
                "report_name": "Inventory Valuation by Location",
                "created_by": "sarah.jones@company.com",
                "created_date": now - timedelta(days=30),
                "last_modified": now - timedelta(days=5),
                "data_sources": ["Warehouse Management"],
                "selected_fields": ["SKU", "Product Name", "Quantity On Hand", "Unit Cost", "Location"],
                "filters": [
                    {"filter_id": "F2", "field": "Quantity On Hand", "operator": "greater_than", "value": "0", "is_active": True}
                ],
                "group_by": ["Location"],
                "sort_by": ["Unit Cost"],
                "format": "excel",
                "is_scheduled": False,
                "run_count": 8
            },
            {
                "report_id": "CUST-003",
                "report_name": "Carrier Performance Dashboard",
                "created_by": "mike.wilson@company.com",
                "created_date": now - timedelta(days=60),
                "last_modified": now - timedelta(days=3),
                "data_sources": ["Transportation"],
                "selected_fields": ["Carrier", "Tracking Number", "Ship Date", "Delivery Date", "Freight Cost"],
                "filters": [
                    {"filter_id": "F3", "field": "Ship Date", "operator": "between", "value": "last_90_days", "is_active": True}
                ],
                "group_by": ["Carrier"],
                "sort_by": ["Delivery Date"],
                "format": "pdf",
                "is_scheduled": True,
                "run_count": 15
            },
            {
                "report_id": "CUST-004",
                "report_name": "Outstanding Invoices Report",
                "created_by": "emily.davis@company.com",
                "created_date": now - timedelta(days=20),
                "last_modified": now - timedelta(days=1),
                "data_sources": ["Billing & Finance", "Orders Management"],
                "selected_fields": ["Invoice Number", "Invoice Date", "Invoice Amount", "Payment Status", "Customer Name"],
                "filters": [
                    {"filter_id": "F4", "field": "Payment Status", "operator": "equals", "value": "pending", "is_active": True}
                ],
                "group_by": ["Payment Status"],
                "sort_by": ["Invoice Date"],
                "format": "excel",
                "is_scheduled": True,
                "run_count": 20
            },
            {
                "report_id": "CUST-005",
                "report_name": "Returns Analysis",
                "created_by": "john.smith@company.com",
                "created_date": now - timedelta(days=15),
                "last_modified": now - timedelta(days=2),
                "data_sources": ["Returns Management", "Orders Management"],
                "selected_fields": ["Order ID", "Product Name", "Return Date", "Return Reason", "Refund Amount"],
                "filters": [
                    {"filter_id": "F5", "field": "Return Date", "operator": "between", "value": "last_60_days", "is_active": True}
                ],
                "group_by": ["Return Reason"],
                "sort_by": ["Return Date"],
                "format": "csv",
                "is_scheduled": False,
                "run_count": 6
            }
        ]
        
        return saved_reports

    def _calculate_custom_reports_summary(self, saved_reports: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for custom reports."""
        
        total_saved_reports = len(saved_reports)
        total_data_sources = 6  # From _get_data_sources
        
        # Simulate reports run this week
        reports_run_this_week = sum(1 for r in saved_reports if r["run_count"] > 0)
        
        # Simulate total records exported
        total_records_exported = sum(r["run_count"] * 500 for r in saved_reports)
        
        return {
            "total_saved_reports": total_saved_reports,
            "total_data_sources": total_data_sources,
            "reports_run_this_week": reports_run_this_week,
            "total_records_exported": total_records_exported
        }

    async def get_scheduled_exports(self) -> Dict[str, Any]:
        """
        Get scheduled exports configuration and history.
        
        Returns:
            Dict containing scheduled exports, execution history, and summary
        """
        
        scheduled_exports = self._get_scheduled_exports_list()
        recent_history = self._get_export_history()
        summary = self._calculate_exports_summary(scheduled_exports, recent_history)
        
        return {
            "timestamp": datetime.utcnow(),
            "summary": summary,
            "scheduled_exports": scheduled_exports,
            "recent_history": recent_history
        }

    def _get_scheduled_exports_list(self) -> List[Dict[str, Any]]:
        """Get list of scheduled exports."""
        
        now = datetime.utcnow()
        
        scheduled_exports = [
            {
                "export_id": "EXP-001",
                "export_name": "Daily Operations Summary",
                "report_type": "standard",
                "schedule_type": "daily",
                "frequency": "08:00 AM",
                "recipients": ["operations@company.com", "manager@company.com"],
                "format": "pdf",
                "last_run": now - timedelta(hours=16),
                "next_run": now + timedelta(hours=8),
                "status": "active",
                "created_date": now - timedelta(days=90),
                "run_count": 90,
                "success_rate": 98.9
            },
            {
                "export_id": "EXP-002",
                "export_name": "Weekly Inventory Report",
                "report_type": "standard",
                "schedule_type": "weekly",
                "frequency": "Monday 09:00 AM",
                "recipients": ["inventory@company.com", "purchasing@company.com"],
                "format": "excel",
                "last_run": now - timedelta(days=6, hours=9),
                "next_run": now + timedelta(days=1, hours=9),
                "status": "active",
                "created_date": now - timedelta(days=180),
                "run_count": 26,
                "success_rate": 100.0
            },
            {
                "export_id": "EXP-003",
                "export_name": "Monthly Financial Summary",
                "report_type": "standard",
                "schedule_type": "monthly",
                "frequency": "1st of month at 10:00 AM",
                "recipients": ["finance@company.com", "cfo@company.com", "accounting@company.com"],
                "format": "excel",
                "last_run": now - timedelta(days=14),
                "next_run": now + timedelta(days=17),
                "status": "active",
                "created_date": now - timedelta(days=365),
                "run_count": 12,
                "success_rate": 100.0
            },
            {
                "export_id": "EXP-004",
                "export_name": "Daily Carrier Performance",
                "report_type": "custom",
                "schedule_type": "daily",
                "frequency": "06:00 PM",
                "recipients": ["logistics@company.com"],
                "format": "csv",
                "last_run": now - timedelta(hours=6),
                "next_run": now + timedelta(hours=18),
                "status": "active",
                "created_date": now - timedelta(days=60),
                "run_count": 60,
                "success_rate": 96.7
            },
            {
                "export_id": "EXP-005",
                "export_name": "Weekly Returns Analysis",
                "report_type": "custom",
                "schedule_type": "weekly",
                "frequency": "Friday 03:00 PM",
                "recipients": ["returns@company.com", "quality@company.com"],
                "format": "pdf",
                "last_run": now - timedelta(days=3, hours=15),
                "next_run": now + timedelta(days=4, hours=15),
                "status": "active",
                "created_date": now - timedelta(days=120),
                "run_count": 17,
                "success_rate": 94.1
            },
            {
                "export_id": "EXP-006",
                "export_name": "Monthly Client Profitability",
                "report_type": "standard",
                "schedule_type": "monthly",
                "frequency": "5th of month at 02:00 PM",
                "recipients": ["sales@company.com", "vp-sales@company.com"],
                "format": "excel",
                "last_run": now - timedelta(days=9),
                "next_run": now + timedelta(days=22),
                "status": "paused",
                "created_date": now - timedelta(days=270),
                "run_count": 9,
                "success_rate": 88.9
            },
            {
                "export_id": "EXP-007",
                "export_name": "Daily Exception Alerts",
                "report_type": "standard",
                "schedule_type": "daily",
                "frequency": "07:00 AM",
                "recipients": ["alerts@company.com", "supervisor@company.com", "manager@company.com"],
                "format": "pdf",
                "last_run": now - timedelta(hours=17),
                "next_run": now + timedelta(hours=7),
                "status": "active",
                "created_date": now - timedelta(days=150),
                "run_count": 150,
                "success_rate": 99.3
            },
            {
                "export_id": "EXP-008",
                "export_name": "Weekly Labor Efficiency",
                "report_type": "custom",
                "schedule_type": "weekly",
                "frequency": "Thursday 04:00 PM",
                "recipients": ["hr@company.com", "operations-manager@company.com"],
                "format": "excel",
                "last_run": now - timedelta(days=7, hours=16),
                "next_run": now + timedelta(hours=4),
                "status": "active",
                "created_date": now - timedelta(days=200),
                "run_count": 29,
                "success_rate": 100.0
            }
        ]
        
        return scheduled_exports

    def _get_export_history(self) -> List[Dict[str, Any]]:
        """Get recent export execution history."""
        
        now = datetime.utcnow()
        
        history = [
            {
                "history_id": "HIST-001",
                "export_name": "Daily Operations Summary",
                "execution_time": now - timedelta(hours=2),
                "status": "success",
                "records_exported": 1245,
                "file_size_kb": 782,
                "duration_seconds": 12,
                "recipients_notified": 2,
                "error_message": None
            },
            {
                "history_id": "HIST-002",
                "export_name": "Daily Carrier Performance",
                "execution_time": now - timedelta(hours=6),
                "status": "success",
                "records_exported": 450,
                "file_size_kb": 245,
                "duration_seconds": 8,
                "recipients_notified": 1,
                "error_message": None
            },
            {
                "history_id": "HIST-003",
                "export_name": "Daily Exception Alerts",
                "execution_time": now - timedelta(hours=17),
                "status": "success",
                "records_exported": 186,
                "file_size_kb": 512,
                "duration_seconds": 15,
                "recipients_notified": 3,
                "error_message": None
            },
            {
                "history_id": "HIST-004",
                "export_name": "Daily Operations Summary",
                "execution_time": now - timedelta(days=1, hours=2),
                "status": "success",
                "records_exported": 1289,
                "file_size_kb": 798,
                "duration_seconds": 11,
                "recipients_notified": 2,
                "error_message": None
            },
            {
                "history_id": "HIST-005",
                "export_name": "Weekly Labor Efficiency",
                "execution_time": now - timedelta(days=1, hours=4),
                "status": "success",
                "records_exported": 95,
                "file_size_kb": 156,
                "duration_seconds": 6,
                "recipients_notified": 2,
                "error_message": None
            },
            {
                "history_id": "HIST-006",
                "export_name": "Daily Carrier Performance",
                "execution_time": now - timedelta(days=1, hours=6),
                "status": "success",
                "records_exported": 438,
                "file_size_kb": 238,
                "duration_seconds": 9,
                "recipients_notified": 1,
                "error_message": None
            },
            {
                "history_id": "HIST-007",
                "export_name": "Weekly Returns Analysis",
                "execution_time": now - timedelta(days=2, hours=15),
                "status": "success",
                "records_exported": 142,
                "file_size_kb": 324,
                "duration_seconds": 10,
                "recipients_notified": 2,
                "error_message": None
            },
            {
                "history_id": "HIST-008",
                "export_name": "Daily Exception Alerts",
                "execution_time": now - timedelta(days=2, hours=17),
                "status": "failed",
                "records_exported": 0,
                "file_size_kb": 0,
                "duration_seconds": 3,
                "recipients_notified": 0,
                "error_message": "Database connection timeout"
            },
            {
                "history_id": "HIST-009",
                "export_name": "Weekly Inventory Report",
                "execution_time": now - timedelta(days=6, hours=9),
                "status": "success",
                "records_exported": 850,
                "file_size_kb": 1456,
                "duration_seconds": 18,
                "recipients_notified": 2,
                "error_message": None
            },
            {
                "history_id": "HIST-010",
                "export_name": "Daily Operations Summary",
                "execution_time": now - timedelta(days=3, hours=2),
                "status": "success",
                "records_exported": 1198,
                "file_size_kb": 756,
                "duration_seconds": 13,
                "recipients_notified": 2,
                "error_message": None
            }
        ]
        
        return history

    def _calculate_exports_summary(self, scheduled_exports: List[Dict[str, Any]], 
                                   history: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics for scheduled exports."""
        
        total_scheduled = len(scheduled_exports)
        active_schedules = sum(1 for e in scheduled_exports if e["status"] == "active")
        paused_schedules = sum(1 for e in scheduled_exports if e["status"] == "paused")
        
        # Count exports in the last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        exports_this_week = sum(
            1 for h in history 
            if h["execution_time"] > seven_days_ago
        )
        
        # Count unique recipients
        all_recipients = set()
        for export in scheduled_exports:
            all_recipients.update(export["recipients"])
        total_recipients = len(all_recipients)
        
        # Calculate average success rate
        if scheduled_exports:
            average_success_rate = sum(e["success_rate"] for e in scheduled_exports) / len(scheduled_exports)
        else:
            average_success_rate = 0.0
        
        return {
            "total_scheduled": total_scheduled,
            "active_schedules": active_schedules,
            "paused_schedules": paused_schedules,
            "exports_this_week": exports_this_week,
            "total_recipients": total_recipients,
            "average_success_rate": round(average_success_rate, 1)
        }


# Singleton instance
dashboard_service = DashboardService()
