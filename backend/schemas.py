"""Pydantic schemas for API request/response models."""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime


# KPI Dashboard Response Models
class KPIMetric(BaseModel):
    """Individual KPI metric."""
    label: str
    value: str
    status: str  # on_target, attention, critical


class KPICategory(BaseModel):
    """KPI category with metrics."""
    title: str
    icon: str
    icon_color: str
    metrics: List[KPIMetric]


class KPIDashboardResponse(BaseModel):
    """Complete KPI dashboard response."""
    last_updated: str
    categories: List[KPICategory]


# Operational Scorecard Response Models
class SystemMetric(BaseModel):
    """Individual system metric."""
    name: str
    value: float
    unit: str
    trend: str  # up, down, stable
    status: str  # good, warning, critical


class SystemScorecard(BaseModel):
    """Scorecard for a single system."""
    system_name: str
    metrics: List[SystemMetric]
    overall_status: str  # healthy, warning, critical


class OperationalScorecardResponse(BaseModel):
    """Complete operational scorecard response."""
    timestamp: datetime
    systems: List[SystemScorecard]
    summary: dict


# Exception & Early Warning Response Models
class Exception(BaseModel):
    """Single exception/alert."""
    id: str
    system: str
    severity: str  # low, medium, high, critical
    category: str
    title: str
    description: str
    affected_entity: str
    created_at: datetime
    status: str  # open, acknowledged, resolved
    recommended_action: Optional[str] = None


class ExceptionSummary(BaseModel):
    """Summary of exceptions by category."""
    total: int
    critical: int
    high: int
    medium: int
    low: int
    by_system: dict


class ExceptionsResponse(BaseModel):
    """Complete exceptions response."""
    timestamp: datetime
    summary: ExceptionSummary
    exceptions: List[Exception]


# Accessorial Charges Response Models
class ChargeOpportunity(BaseModel):
    """Single accessorial charge recovery opportunity."""
    charge_id: str
    charge_type: str  # detention, redelivery, address_correction, fuel_surcharge, etc.
    amount: float
    shipment_id: Optional[str] = None
    carrier: Optional[str] = None
    occurrence_date: datetime
    age_days: int
    status: str  # pending, under_review, billed, recovered
    description: str
    recommended_action: str


class ChargeSummary(BaseModel):
    """Summary of accessorial charges."""
    total_recoverable: float
    total_opportunities: int
    pending_review: int
    billed_mtd: int
    recovered_mtd: float
    by_charge_type: dict
    by_carrier: dict


class AccessorialChargesResponse(BaseModel):
    """Complete accessorial charges response."""
    timestamp: datetime
    summary: ChargeSummary
    opportunities: List[ChargeOpportunity]


# Client Profitability Response Models
class ClientMetrics(BaseModel):
    """Profitability metrics for a single client."""
    customer_id: str
    customer_name: str
    revenue_mtd: float
    revenue_ytd: float
    cost_mtd: float
    cost_ytd: float
    profit_mtd: float
    profit_ytd: float
    margin_pct: float
    orders_mtd: int
    orders_ytd: int
    avg_order_value: float
    growth_mom: float  # month over month growth %
    service_level_pct: float
    days_to_pay: int


class ProfitabilitySummary(BaseModel):
    """Summary of client profitability."""
    total_revenue_mtd: float
    total_profit_mtd: float
    total_revenue_ytd: float
    total_profit_ytd: float
    avg_margin_pct: float
    total_clients: int
    top_revenue_client: str
    top_margin_client: str


class ClientProfitabilityResponse(BaseModel):
    """Complete client profitability response."""
    timestamp: datetime
    summary: ProfitabilitySummary
    clients: List[ClientMetrics]


# Billing Analytics Response Models
class RevenueByService(BaseModel):
    """Revenue breakdown by service type."""
    service_type: str
    revenue: float
    invoice_count: int
    pct_of_total: float


class InvoiceStatusMetrics(BaseModel):
    """Invoice status breakdown."""
    status: str
    count: int
    total_amount: float
    pct_of_count: float


class BillingTrend(BaseModel):
    """Billing trend data point."""
    date: str
    revenue: float
    invoices_issued: int
    invoices_paid: int
    collection_rate: float


class BillingAnalyticsSummary(BaseModel):
    """Summary of billing analytics."""
    total_revenue_mtd: float
    total_revenue_ytd: float
    invoices_issued_mtd: int
    invoices_paid_mtd: int
    collection_rate_mtd: float
    avg_invoice_value: float
    days_sales_outstanding: int
    overdue_amount: float
    disputed_amount: float


class BillingAnalyticsResponse(BaseModel):
    """Complete billing analytics response."""
    timestamp: datetime
    summary: BillingAnalyticsSummary
    revenue_by_service: List[RevenueByService]
    invoice_status: List[InvoiceStatusMetrics]
    trends: List[BillingTrend]


# Warehouse Performance Response Models
class InventoryMetrics(BaseModel):
    """Inventory health metrics."""
    total_skus: int
    total_quantity: int
    below_reorder_point: int
    out_of_stock: int
    inventory_accuracy_pct: float
    capacity_utilization_pct: float


class PickingMetrics(BaseModel):
    """Picking performance metrics."""
    total_tasks_today: int
    completed_today: int
    pending: int
    delayed: int
    completion_rate_pct: float
    avg_pick_time_minutes: float


class TopPerformer(BaseModel):
    """Top performing picker."""
    picker_name: str
    picks_completed: int
    avg_time_minutes: float


class InventoryItem(BaseModel):
    """Inventory item detail."""
    sku: str
    product_name: str
    location: str
    quantity_on_hand: int
    quantity_available: int
    reorder_point: int
    status: str  # ok, low, critical, out_of_stock


class WarehousePerformanceSummary(BaseModel):
    """Summary of warehouse performance."""
    picks_completed_today: int
    pick_completion_rate: float
    avg_pick_time: float
    inventory_accuracy: float
    capacity_utilization: float
    items_below_reorder: int
    top_performer: str


class WarehousePerformanceResponse(BaseModel):
    """Complete warehouse performance response."""
    timestamp: datetime
    summary: WarehousePerformanceSummary
    inventory_metrics: InventoryMetrics
    picking_metrics: PickingMetrics
    top_performers: List[TopPerformer]
    critical_inventory: List[InventoryItem]


# Carrier Scorecard Response Models
class CarrierMetrics(BaseModel):
    """Metrics for a single carrier."""
    carrier_name: str
    total_shipments: int
    on_time_deliveries: int
    delayed_deliveries: int
    on_time_rate_pct: float
    avg_transit_time_hours: float
    total_cost: float
    cost_per_shipment: float
    active_shipments: int
    exceptions: int
    performance_score: float  # 0-100
    status: str  # excellent, good, fair, poor


class CarrierScorecardSummary(BaseModel):
    """Summary of carrier performance."""
    total_carriers: int
    total_shipments: int
    overall_on_time_rate: float
    avg_cost_per_shipment: float
    best_performer: str
    worst_performer: str
    total_exceptions: int


class CarrierTrend(BaseModel):
    """Carrier performance trend data."""
    date: str
    on_time_rate: float
    shipment_count: int


class CarrierScorecardResponse(BaseModel):
    """Complete carrier scorecard response."""
    timestamp: datetime
    summary: CarrierScorecardSummary
    carriers: List[CarrierMetrics]
    trends: List[CarrierTrend]


# Labor Efficiency Response Models
class WorkerMetrics(BaseModel):
    """Metrics for a single worker."""
    worker_name: str
    tasks_assigned: int
    tasks_completed: int
    tasks_delayed: int
    completion_rate_pct: float
    avg_time_per_task_minutes: float
    total_hours_worked: float
    productivity_score: float  # 0-100
    status: str  # excellent, good, average, needs_improvement


class LaborEfficiencySummary(BaseModel):
    """Summary of labor efficiency metrics."""
    total_workers: int
    total_tasks_today: int
    tasks_completed_today: int
    overall_completion_rate: float
    avg_productivity_score: float
    labor_utilization_pct: float
    top_performer: str
    workers_needing_support: int


class HourlyProductivity(BaseModel):
    """Hourly productivity trend data."""
    hour: str
    tasks_completed: int
    avg_time_minutes: float
    worker_count: int


class TaskBreakdown(BaseModel):
    """Task breakdown by status."""
    status: str
    count: int
    percentage: float


class LaborEfficiencyResponse(BaseModel):
    """Complete labor efficiency response."""
    timestamp: datetime
    summary: LaborEfficiencySummary
    workers: List[WorkerMetrics]
    hourly_trends: List[HourlyProductivity]
    task_breakdown: List[TaskBreakdown]


# Inventory Optimization Response Models
class InventoryAnalysis(BaseModel):
    """Analysis for a single inventory item."""
    sku: str
    product_name: str
    location: str
    quantity_on_hand: int
    quantity_available: int
    quantity_reserved: int
    reorder_point: int
    days_of_supply: float
    turnover_rate: float
    holding_cost_monthly: float
    status: str  # optimal, overstocked, understocked, critical
    recommendation: str


class InventoryOptimizationSummary(BaseModel):
    """Summary of inventory optimization metrics."""
    total_skus: int
    total_value: float
    avg_turnover_rate: float
    optimal_items: int
    overstocked_items: int
    understocked_items: int
    critical_items: int
    total_holding_cost: float
    potential_savings: float


class TurnoverCategory(BaseModel):
    """Inventory turnover category breakdown."""
    category: str
    count: int
    percentage: float
    avg_turnover: float


class ABCAnalysis(BaseModel):
    """ABC classification item."""
    category: str  # A, B, C
    sku_count: int
    value_percentage: float
    description: str


class InventoryOptimizationResponse(BaseModel):
    """Complete inventory optimization response."""
    timestamp: datetime
    summary: InventoryOptimizationSummary
    items: List[InventoryAnalysis]
    turnover_categories: List[TurnoverCategory]
    abc_analysis: List[ABCAnalysis]


# Standard Reports Response Models
class ReportTemplate(BaseModel):
    """Standard report template."""
    report_id: str
    report_name: str
    category: str  # operational, financial, inventory, transportation
    description: str
    frequency: str  # daily, weekly, monthly, on_demand
    last_run: Optional[datetime] = None
    status: str  # available, running, completed, failed
    record_count: int
    file_size_kb: int
    format: str  # pdf, excel, csv


class ReportSummary(BaseModel):
    """Summary of standard reports."""
    total_reports: int
    available_reports: int
    scheduled_reports: int
    reports_run_today: int
    total_downloads: int


class ReportCategory(BaseModel):
    """Report category breakdown."""
    category: str
    count: int
    description: str


class StandardReportsResponse(BaseModel):
    """Complete standard reports response."""
    timestamp: datetime
    summary: ReportSummary
    reports: List[ReportTemplate]
    categories: List[ReportCategory]


# Custom Reports Response Models
class DataSource(BaseModel):
    """Available data source for custom reports."""
    source_id: str
    source_name: str
    source_type: str  # database, table, view
    description: str
    table_count: int
    record_count: int
    available_fields: int


class ReportField(BaseModel):
    """Available field for custom reports."""
    field_id: str
    field_name: str
    field_type: str  # text, number, date, boolean
    source: str
    description: str
    is_selected: bool = False


class ReportFilter(BaseModel):
    """Filter configuration for custom reports."""
    filter_id: str
    field: str
    operator: str  # equals, contains, greater_than, less_than, between
    value: str
    is_active: bool = True


class SavedReport(BaseModel):
    """User-saved custom report."""
    report_id: str
    report_name: str
    created_by: str
    created_date: datetime
    last_modified: datetime
    data_sources: List[str]
    selected_fields: List[str]
    filters: List[ReportFilter]
    group_by: List[str]
    sort_by: List[str]
    format: str  # excel, csv, pdf
    is_scheduled: bool = False
    run_count: int


class CustomReportsSummary(BaseModel):
    """Summary of custom reports."""
    total_saved_reports: int
    total_data_sources: int
    reports_run_this_week: int
    total_records_exported: int


class CustomReportsResponse(BaseModel):
    """Complete custom reports response."""
    timestamp: datetime
    summary: CustomReportsSummary
    data_sources: List[DataSource]
    available_fields: List[ReportField]
    saved_reports: List[SavedReport]


# Scheduled Exports Response Models
class ScheduledExport(BaseModel):
    """Scheduled export configuration."""
    export_id: str
    export_name: str
    report_type: str  # standard, custom
    schedule_type: str  # daily, weekly, monthly, custom
    frequency: str  # 08:00 AM, Monday 9:00 AM, 1st of month
    recipients: List[str]
    format: str  # excel, csv, pdf
    last_run: Optional[datetime] = None
    next_run: datetime
    status: str  # active, paused, failed
    created_date: datetime
    run_count: int
    success_rate: float


class ExportHistory(BaseModel):
    """Export execution history."""
    history_id: str
    export_name: str
    execution_time: datetime
    status: str  # success, failed, partial
    records_exported: int
    file_size_kb: int
    duration_seconds: int
    recipients_notified: int
    error_message: Optional[str] = None


class ScheduledExportsSummary(BaseModel):
    """Summary of scheduled exports."""
    total_scheduled: int
    active_schedules: int
    paused_schedules: int
    exports_this_week: int
    total_recipients: int
    average_success_rate: float


class ScheduledExportsResponse(BaseModel):
    """Complete scheduled exports response."""
    timestamp: datetime
    summary: ScheduledExportsSummary
    scheduled_exports: List[ScheduledExport]
    recent_history: List[ExportHistory]


# Health Check Response
class HealthCheckResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    systems_connected: dict


# Chat Schemas
class ChatRequest(BaseModel):
    """Chat request model."""
    message: str
    include_context: bool = True


class ChatResponse(BaseModel):
    """Chat response model."""
    response: str
    timestamp: datetime


class SuggestedQuestionsResponse(BaseModel):
    """Suggested questions response."""
    questions: List[str]
