"""FastAPI main application."""
from fastapi import FastAPI, HTTPException, Depends, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from datetime import datetime, timedelta
import os

from config import settings
from logger import setup_logger
from schemas import (
    OperationalScorecardResponse,
    ExceptionsResponse,
    HealthCheckResponse,
    KPIDashboardResponse,
    AccessorialChargesResponse,
    ClientProfitabilityResponse,
    BillingAnalyticsResponse,
    WarehousePerformanceResponse,
    CarrierScorecardResponse,
    LaborEfficiencyResponse,
    InventoryOptimizationResponse,
    StandardReportsResponse,
    CustomReportsResponse,
    ScheduledExportsResponse,
    ChatRequest,
    ChatResponse,
    SuggestedQuestionsResponse
)
from services.dashboard_service import dashboard_service
from services.billing_service import BillingService
from services.exception_service import ExceptionService
from services.tracking_service import TrackingService
from services.journey_service import JourneyService
from services.auth_service import auth_service
# TEMPORARILY DISABLED - RAG features require additional dependencies
# from services.rag_chat_service import get_rag_chat_service
from models.billing_models import init_billing_db

# Setup logger
logger = setup_logger(__name__)

# Security
security = HTTPBearer(auto_error=False)

# Initialize billing database
try:
    init_billing_db(settings.billing_db_path)
    logger.info("Billing database initialized")
except Exception as e:
    logger.error(f"Failed to initialize billing database: {e}")

# Initialize services
billing_service = BillingService()
tracking_service = TrackingService()
journey_service = JourneyService()

# Exception service - use fresh instance per request to avoid session issues
def get_exception_service():
    """Get a fresh ExceptionService instance with clean session."""
    return ExceptionService()

# TEMPORARILY DISABLED - RAG chat service requires additional dependencies
# # Initialize RAG chat service (will auto-load on first use)
# def get_chat_service():
#     """Lazy-load chat service to avoid startup delay."""
#     return get_rag_chat_service()

# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="E-commerce Fulfillment Operations Control Tower - Dashboard API",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files for invoice downloads
os.makedirs("invoices", exist_ok=True)
app.mount("/invoices", StaticFiles(directory="invoices"), name="invoices")


# Authentication dependency
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), request: Request = None):
    """Dependency to get current authenticated user."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = auth_service.validate_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return user


async def get_optional_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Optional authentication - returns None if not authenticated."""
    if not credentials:
        return None
    
    user = auth_service.validate_token(credentials.credentials)
    return user


# ============================================================================
# Authentication Endpoints
# ============================================================================

@app.post(f"{settings.api_prefix}/auth/login")
async def login(username: str = Form(...), password: str = Form(...), request: Request = None):
    """
    Authenticate user and return access token.
    
    Args:
        username: User's username (form data)
        password: User's password (form data)
    
    Returns:
        User info, access token, and refresh token
    """
    client_ip = request.client.host if request and request.client else None
    user_agent = request.headers.get("user-agent") if request else None
    
    result = auth_service.authenticate(username, password, client_ip, user_agent)
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    return result


@app.post(f"{settings.api_prefix}/auth/logout")
async def logout(request: Request, current_user: dict = Depends(get_current_user), credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Logout user and invalidate token."""
    client_ip = request.client.host if request.client else None
    
    success = auth_service.logout(credentials.credentials, client_ip)
    
    if not success:
        raise HTTPException(status_code=400, detail="Failed to logout")
    
    return {"success": True, "message": "Logged out successfully"}


@app.post(f"{settings.api_prefix}/auth/refresh")
async def refresh_token(refresh_token: str):
    """
    Refresh access token using refresh token.
    
    Args:
        refresh_token: Valid refresh token
    
    Returns:
        New access token and refresh token
    """
    result = auth_service.refresh_session(refresh_token)
    
    if not result:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    return result


@app.get(f"{settings.api_prefix}/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current authenticated user information."""
    return current_user


@app.get(f"{settings.api_prefix}/auth/roles")
async def get_roles(current_user: dict = Depends(get_current_user)):
    """Get all available roles."""
    # Check admin permission
    if "admin.roles" not in current_user.get("permissions", []) and not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return auth_service.get_all_roles()


@app.get(f"{settings.api_prefix}/auth/permissions")
async def get_permissions(current_user: dict = Depends(get_current_user)):
    """Get all available permissions."""
    # Check admin permission
    if "admin.roles" not in current_user.get("permissions", []) and not current_user.get("is_superuser"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return auth_service.get_all_permissions()


# Admin endpoints
@app.get(f"{settings.api_prefix}/admin/users")
async def get_all_users(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get all users (admin only)."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = auth_service.validate_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if not auth_service.check_permission(user['id'], "admin.users"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return auth_service.get_all_users()


@app.post(f"{settings.api_prefix}/admin/users")
async def create_user_endpoint(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Create a new user (admin only)."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = auth_service.validate_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if not auth_service.check_permission(user['id'], "admin.users"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        data = await request.json()
        
        # Convert role_id to role_names for create_user
        role_names = []
        if data.get('role_id'):
            from models.auth_models import Role, get_auth_session
            auth_session = get_auth_session()
            role = auth_session.query(Role).filter(Role.id == data.get('role_id')).first()
            if role:
                role_names = [role.name]
            auth_session.close()
        
        if not role_names:
            raise HTTPException(status_code=400, detail="Valid role_id is required")
        
        new_user = auth_service.create_user(
            username=data.get('username'),
            full_name=data.get('full_name'),
            email=data.get('email'),
            password=data.get('password'),
            role_names=role_names,
            client_id=data.get('client_id'),
            department=data.get('department')
        )
        if not new_user:
            raise HTTPException(status_code=400, detail="Failed to create user - username or email already exists")
        
        return {
            "id": new_user.id,
            "username": new_user.username,
            "full_name": new_user.full_name,
            "email": new_user.email,
            "is_active": new_user.is_active,
            "roles": [{"id": r.id, "name": r.name, "display_name": r.display_name} for r in new_user.roles]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.put(f"{settings.api_prefix}/admin/users/{{user_id}}")
async def update_user_endpoint(
    user_id: int,
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Update a user (admin only)."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = auth_service.validate_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if not auth_service.check_permission(user['id'], "admin.users"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        data = await request.json()
        updated_user = auth_service.update_user(
            user_id=user_id,
            full_name=data.get('full_name'),
            email=data.get('email'),
            password=data.get('password') if data.get('password') else None,
            role_id=data.get('role_id'),
            is_active=data.get('is_active')
        )
        return updated_user
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete(f"{settings.api_prefix}/admin/users/{{user_id}}")
async def delete_user_endpoint(
    user_id: int,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """Delete a user (admin only)."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = auth_service.validate_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if not auth_service.check_permission(user['id'], "admin.users"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    # Prevent self-deletion
    if user["id"] == user_id:
        raise HTTPException(status_code=400, detail="Cannot delete your own account")
    
    try:
        auth_service.delete_user(user_id)
        return {"success": True, "message": "User deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get(f"{settings.api_prefix}/admin/audit-logs")
async def get_audit_logs(
    username: str = None,
    action: str = None,
    resource_type: str = None,
    success: bool = None,
    limit: int = 100,
    offset: int = 0,
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get audit logs (admin only).
    
    Query params:
        - username: Filter by username (partial match)
        - action: Filter by action type
        - resource_type: Filter by resource type
        - success: Filter by success status (true/false)
        - limit: Number of records to return (default: 100)
        - offset: Number of records to skip (default: 0)
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = auth_service.validate_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    if not auth_service.check_permission(user['id'], "admin.logs"):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    try:
        logs = auth_service.get_audit_logs(
            username=username,
            action=action,
            resource_type=resource_type,
            success=success,
            limit=limit,
            offset=offset
        )
        return logs
    except Exception as e:
        logger.error(f"Error fetching audit logs: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch audit logs: {str(e)}"
        )


@app.get(f"{settings.api_prefix}/users/assignable")
async def get_assignable_users(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    """
    Get list of users who can be assigned to exceptions.
    Returns users with exceptions.resolve permission.
    """
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    user = auth_service.validate_token(credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    logger.info("Fetching assignable users")
    
    try:
        # Get all users
        all_users = auth_service.get_all_users()
        
        # Filter users who have exceptions.resolve permission
        assignable_users = []
        for u in all_users:
            if u.get('is_active', True) and auth_service.check_permission(u['id'], 'exceptions.resolve'):
                assignable_users.append({
                    'user_id': u['id'],
                    'username': u['username'],
                    'full_name': u.get('full_name', u['username']),
                    'email': u.get('email', ''),
                    'roles': u.get('roles', [])
                })
        
        return {'users': assignable_users}
    except Exception as e:
        logger.error(f"Error fetching assignable users: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch assignable users: {str(e)}"
        )


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "operational",
        "endpoints": {
            "health": "/api/v1/health",
            "scorecard": "/api/v1/dashboard/scorecard",
            "exceptions": "/api/v1/dashboard/exceptions",
            "docs": "/api/docs"
        }
    }


@app.get(f"{settings.api_prefix}/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    logger.info("Health check requested")
    
    # Check if database files exist
    db_paths = {
        "WMS": settings.wms_db_path,
        "OMS": settings.oms_db_path,
        "TMS": settings.tms_db_path,
        "Billing": settings.billing_db_path,
        "Returns": settings.returns_db_path,
        "Yard": settings.yard_db_path
    }
    
    systems_connected = {}
    for system, path in db_paths.items():
        systems_connected[system] = os.path.exists(path)
    
    all_connected = all(systems_connected.values())
    
    return {
        "status": "healthy" if all_connected else "degraded",
        "timestamp": datetime.utcnow(),
        "version": settings.app_version,
        "systems_connected": systems_connected
    }


@app.get(
    f"{settings.api_prefix}/dashboard/scorecard",
    response_model=OperationalScorecardResponse
)
async def get_operational_scorecard(user: dict = Depends(get_optional_user)):
    """
    Get operational scorecard with metrics from all systems.
    
    Returns real-time metrics for:
    - Warehouse Management (WMS)
    - Order Management (OMS)
    - Transportation (TMS)
    - Billing
    - Returns Management
    - Yard/Dock Management
    """
    logger.info("Operational scorecard requested")
    
    try:
        dashboard_service.set_current_user(user)
        scorecard = dashboard_service.get_operational_scorecard()
        return scorecard
    except Exception as e:
        logger.error(f"Error generating scorecard: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate operational scorecard: {str(e)}"
        )


@app.get(
    f"{settings.api_prefix}/dashboard/exceptions",
    response_model=ExceptionsResponse
)
async def get_exceptions(user: dict = Depends(get_optional_user)):
    """
    Get exceptions and early warnings from all systems.
    
    Returns alerts for:
    - Low inventory
    - Delayed orders
    - Shipment exceptions
    - Overdue invoices
    - Pending returns
    - Missed dock appointments
    """
    logger.info("Exceptions requested")
    
    try:
        dashboard_service.set_current_user(user)
        exceptions = dashboard_service.get_exceptions()
        return exceptions
    except Exception as e:
        logger.error(f"Error generating exceptions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate exceptions: {str(e)}"
        )


@app.get(
    f"{settings.api_prefix}/dashboard/kpis",
    response_model=KPIDashboardResponse
)
async def get_kpi_dashboard(user: dict = Depends(get_optional_user)):
    """
    Get KPI dashboard with key performance indicators.
    
    Returns KPIs for:
    - Service Levels
    - Fulfillment Execution
    - Productivity & Staffing
    - Inventory Health
    - Dock & Carrier Flow
    - Returns & Billing Control
    """
    logger.info("KPI dashboard requested")
    
    try:
        dashboard_service.set_current_user(user)
        kpis = dashboard_service.get_kpi_dashboard()
        return kpis
    except Exception as e:
        logger.error(f"Error generating KPI dashboard: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate KPI dashboard: {str(e)}"
        )


@app.get(
    f"{settings.api_prefix}/dashboard/accessorial-charges",
    response_model=AccessorialChargesResponse
)
async def get_accessorial_charges(user: dict = Depends(get_optional_user)):
    """
    Get accessorial charges recovery opportunities.
    
    Returns opportunities for:
    - Detention charges (pickup/delivery delays)
    - Redelivery charges (failed deliveries)
    - Dock detention charges (yard delays)
    - Address corrections
    - Other billable accessorials
    """
    logger.info("Accessorial charges requested")
    
    try:
        dashboard_service.set_current_user(user)
        charges = dashboard_service.get_accessorial_charges()
        return charges
    except Exception as e:
        logger.error(f"Error generating accessorial charges: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate accessorial charges: {str(e)}"
        )


@app.get(
    f"{settings.api_prefix}/dashboard/client-profitability",
    response_model=ClientProfitabilityResponse
)
async def get_client_profitability(user: dict = Depends(get_optional_user)):
    """
    Get client profitability analysis.
    
    Returns profitability metrics for each client:
    - Revenue and profit (MTD/YTD)
    - Margin percentages
    - Growth trends
    - Service levels
    - Payment performance
    """
    logger.info("Client profitability requested")
    
    try:
        dashboard_service.set_current_user(user)
        profitability = dashboard_service.get_client_profitability()
        return profitability
    except Exception as e:
        logger.error(f"Error generating client profitability: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate client profitability: {str(e)}"
        )


@app.get(
    f"{settings.api_prefix}/dashboard/billing-analytics",
    response_model=BillingAnalyticsResponse
)
async def get_billing_analytics(user: dict = Depends(get_optional_user)):
    """
    Get billing analytics and revenue insights.
    
    Returns comprehensive billing metrics:
    - Revenue trends and forecasts
    - Invoice status breakdown
    - Collection performance (DSO)
    - Revenue by service type
    - Overdue and disputed amounts
    """
    logger.info("Billing analytics requested")
    
    try:
        dashboard_service.set_current_user(user)
        analytics = dashboard_service.get_billing_analytics()
        return analytics
    except Exception as e:
        logger.error(f"Error generating billing analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate billing analytics: {str(e)}"
        )


@app.get(
    f"{settings.api_prefix}/dashboard/warehouse-performance",
    response_model=WarehousePerformanceResponse
)
async def get_warehouse_performance(user: dict = Depends(get_optional_user)):
    """
    Get warehouse performance metrics.
    
    Returns warehouse operational metrics:
    - Inventory health and accuracy
    - Picking performance and productivity
    - Top performers and efficiency
    - Critical stock alerts
    - Capacity utilization
    """
    logger.info("Warehouse performance requested")
    
    try:
        dashboard_service.set_current_user(user)
        performance = dashboard_service.get_warehouse_performance()
        return performance
    except Exception as e:
        logger.error(f"Error generating warehouse performance: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate warehouse performance: {str(e)}"
        )


@app.get(
    f"{settings.api_prefix}/dashboard/carrier-scorecard",
    response_model=CarrierScorecardResponse
)
async def get_carrier_scorecard(user: dict = Depends(get_optional_user)):
    """
    Get carrier performance scorecard.
    
    Returns carrier performance metrics:
    - On-time delivery rates by carrier
    - Transit time and cost per shipment
    - Active shipments and exceptions
    - Performance scores and rankings
    - Historical trends
    """
    logger.info("Carrier scorecard requested")
    
    try:
        dashboard_service.set_current_user(user)
        scorecard = dashboard_service.get_carrier_scorecard()
        return scorecard
    except Exception as e:
        logger.error(f"Error generating carrier scorecard: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate carrier scorecard: {str(e)}"
        )


@app.get(
    f"{settings.api_prefix}/dashboard/labor-efficiency",
    response_model=LaborEfficiencyResponse
)
async def get_labor_efficiency(user: dict = Depends(get_optional_user)):
    """
    Get labor efficiency metrics.
    
    Returns workforce performance metrics:
    - Worker productivity scores and rankings
    - Task completion rates and timing
    - Hourly productivity trends
    - Task breakdown by status
    - Labor utilization rates
    """
    logger.info("Labor efficiency requested")
    
    try:
        dashboard_service.set_current_user(user)
        efficiency = dashboard_service.get_labor_efficiency()
        return efficiency
    except Exception as e:
        logger.error(f"Error generating labor efficiency: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate labor efficiency: {str(e)}"
        )


@app.get(
    f"{settings.api_prefix}/dashboard/inventory-optimization",
    response_model=InventoryOptimizationResponse
)
async def get_inventory_optimization(user: dict = Depends(get_optional_user)):
    """
    Get inventory optimization analysis.
    
    Returns inventory optimization insights:
    - Inventory health by SKU with recommendations
    - Days of supply and turnover rates
    - Overstocked and understocked items
    - ABC analysis and value distribution
    - Holding costs and potential savings
    """
    logger.info("Inventory optimization requested")
    
    try:
        dashboard_service.set_current_user(user)
        optimization = dashboard_service.get_inventory_optimization()
        return optimization
    except Exception as e:
        logger.error(f"Error generating inventory optimization: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate inventory optimization: {str(e)}"
        )


@app.get(
    f"{settings.api_prefix}/dashboard/standard-reports",
    response_model=StandardReportsResponse
)
async def get_standard_reports(user: dict = Depends(get_optional_user)):
    """
    Get standard reports catalog.
    
    Returns available standard reports:
    - Pre-built report templates by category
    - Report frequency and last run status
    - Available formats (PDF, Excel, CSV)
    - Report descriptions and record counts
    """
    logger.info("Standard reports requested")
    
    try:
        dashboard_service.set_current_user(user)
        reports = dashboard_service.get_standard_reports()
        return reports
    except Exception as e:
        logger.error(f"Error generating standard reports: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate standard reports: {str(e)}"
        )


@app.get(
    f"{settings.api_prefix}/dashboard/custom-reports",
    response_model=CustomReportsResponse
)
async def get_custom_reports(user: dict = Depends(get_optional_user)):
    """
    Get custom report builder configuration.
    
    Returns custom reporting tools:
    - Available data sources and field lists
    - Saved custom report templates
    - Report configuration options
    - Export format options (Excel, CSV, PDF)
    """
    logger.info("Custom reports requested")
    
    try:
        dashboard_service.set_current_user(user)
        reports = await dashboard_service.get_custom_reports()
        return reports
    except Exception as e:
        logger.error(f"Error generating custom reports: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate custom reports: {str(e)}"
        )


@app.get(
    f"{settings.api_prefix}/dashboard/scheduled-exports",
    response_model=ScheduledExportsResponse
)
async def get_scheduled_exports(user: dict = Depends(get_optional_user)):
    """
    Get scheduled exports configuration and history.
    
    Returns scheduled export management:
    - Active and paused export schedules
    - Schedule frequency and recipients
    - Recent execution history
    - Success rates and statistics
    """
    logger.info("Scheduled exports requested")
    
    try:
        dashboard_service.set_current_user(user)
        exports = await dashboard_service.get_scheduled_exports()
        return exports
    except Exception as e:
        logger.error(f"Error generating scheduled exports: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate scheduled exports: {str(e)}"
        )


@app.post(f"{settings.api_prefix}/billing/process-accessorial-charge")
async def process_accessorial_charge(charge_id: str):
    """
    Process an accessorial charge by creating an invoice and generating PDF.
    
    Args:
        charge_id: The ID of the charge to process
        
    Returns:
        Invoice details including download URL
    """
    logger.info(f"Processing accessorial charge: {charge_id}")
    
    try:
        result = await billing_service.process_accessorial_charge(charge_id)
        return result
    except Exception as e:
        logger.error(f"Error processing accessorial charge {charge_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process charge: {str(e)}"
        )


@app.get("/invoices/{invoice_filename}")
async def download_invoice(invoice_filename: str):
    """
    Download invoice PDF file.
    
    Args:
        invoice_filename: Name of the invoice file to download
        
    Returns:
        PDF file
    """
    logger.info(f"Invoice download requested: {invoice_filename}")
    
    filepath = os.path.join("invoices", invoice_filename)
    
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Invoice not found")
    
    return FileResponse(
        filepath,
        media_type="application/pdf",
        filename=invoice_filename
    )


# ===== Exception Management Endpoints =====

@app.get(f"{settings.api_prefix}/exceptions/stats")
async def get_exception_stats():
    """Get summary statistics for exceptions."""
    logger.info("Fetching exception statistics")
    
    try:
        service = get_exception_service()
        stats = service.get_exception_stats()
        service.session.close()
        return stats
    except Exception as e:
        logger.error(f"Error fetching exception stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch exception stats: {str(e)}"
        )


@app.get(f"{settings.api_prefix}/exceptions")
async def get_exceptions(
    status: str = None,
    severity: str = None,
    exception_type: str = None
):
    """
    Get all exceptions with optional filters.
    
    Query params:
        - status: Filter by status (open, in_progress, resolved, dismissed)
        - severity: Filter by severity (critical, warning, info)
        - exception_type: Filter by type (delay, inventory, quality, billing, etc.)
    """
    logger.info(f"Fetching exceptions - status: {status}, severity: {severity}, type: {exception_type}")
    
    try:
        service = get_exception_service()
        exceptions = service.get_all_exceptions(
            status=status,
            severity=severity,
            exception_type=exception_type
        )
        service.session.close()
        return {
            "count": len(exceptions),
            "exceptions": exceptions
        }
    except Exception as e:
        logger.error(f"Error fetching exceptions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch exceptions: {str(e)}"
        )


@app.get(f"{settings.api_prefix}/exceptions/{{exception_id}}")
async def get_exception_detail(exception_id: str):
    """Get detailed information for a specific exception."""
    logger.info(f"Fetching exception detail: {exception_id}")
    
    try:
        service = get_exception_service()
        exception = service.get_exception_by_id(exception_id)
        
        if not exception:
            service.session.close()
            raise HTTPException(status_code=404, detail="Exception not found")
        
        # Get action history
        actions = service.get_exception_actions(exception_id)
        service.session.close()
        
        return {
            "exception": exception,
            "actions": actions
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching exception {exception_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch exception: {str(e)}"
        )


@app.post(f"{settings.api_prefix}/exceptions/detect")
async def detect_exceptions():
    """Run exception detection across all systems."""
    logger.info("Running exception detection")
    
    try:
        service = get_exception_service()
        detected = service.detect_exceptions()
        service.session.commit()
        service.session.close()
        return {
            "success": True,
            "detected_count": len(detected),
            "exceptions": detected
        }
    except Exception as e:
        logger.error(f"Error detecting exceptions: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to detect exceptions: {str(e)}"
        )


@app.put(f"{settings.api_prefix}/exceptions/{{exception_id}}/status")
async def update_exception_status(
    exception_id: str,
    status: str,
    user: str = "system",
    notes: str = None
):
    """
    Update exception status.
    
    Body params:
        - status: New status (open, in_progress, resolved, dismissed)
        - user: User making the change
        - notes: Optional resolution notes
    """
    logger.info(f"Updating exception {exception_id} status to {status}")
    
    try:
        service = get_exception_service()
        result = service.update_exception_status(
            exception_id=exception_id,
            new_status=status,
            user=user,
            notes=notes
        )
        service.session.commit()
        service.session.close()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating exception status: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update exception: {str(e)}"
        )


@app.put(f"{settings.api_prefix}/exceptions/{{exception_id}}/assign")
async def assign_exception(
    exception_id: str,
    assigned_to: str,
    assigned_by: str = "system"
):
    """
    Assign exception to a user.
    
    Body params:
        - assigned_to: User to assign to
        - assigned_by: User making the assignment
    """
    logger.info(f"Assigning exception {exception_id} to {assigned_to}")
    
    try:
        service = get_exception_service()
        result = service.assign_exception(
            exception_id=exception_id,
            assigned_to=assigned_to,
            assigned_by=assigned_by
        )
        service.session.commit()
        service.session.close()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error assigning exception: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to assign exception: {str(e)}"
        )


@app.post(f"{settings.api_prefix}/exceptions/{{exception_id}}/notes")
async def add_exception_note(
    exception_id: str,
    user: str,
    note: str
):
    """
    Add a note/comment to an exception.
    
    Body params:
        - user: User adding the note
        - note: Note content
    """
    logger.info(f"Adding note to exception {exception_id}")
    
    try:
        service = get_exception_service()
        result = service.add_exception_note(
            exception_id=exception_id,
            user=user,
            note=note
        )
        service.session.commit()
        service.session.close()
        return result
    except Exception as e:
        logger.error(f"Error adding note to exception: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to add note: {str(e)}"
        )


# ===== Real-Time Tracking Endpoints =====

@app.get(f"{settings.api_prefix}/tracking/stats")
async def get_tracking_stats():
    """Get summary statistics for tracked shipments."""
    logger.info("Fetching tracking statistics")
    
    try:
        stats = tracking_service.get_tracking_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching tracking stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch tracking stats: {str(e)}"
        )


@app.get(f"{settings.api_prefix}/tracking/shipments")
async def get_tracked_shipments(status: str = None):
    """
    Get all tracked shipments with current locations.
    
    Query params:
        - status: Filter by status (in_transit, out_for_delivery, delivered, etc.)
    """
    logger.info(f"Fetching tracked shipments - status: {status}")
    
    try:
        shipments = tracking_service.get_all_tracked_shipments(status_filter=status)
        return {
            "count": len(shipments),
            "shipments": shipments
        }
    except Exception as e:
        logger.error(f"Error fetching tracked shipments: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch tracked shipments: {str(e)}"
        )


@app.get(f"{settings.api_prefix}/tracking/shipments/{{shipment_id}}")
async def get_shipment_tracking_details(shipment_id: str):
    """Get detailed tracking information for a specific shipment."""
    logger.info(f"Fetching tracking details for shipment: {shipment_id}")
    
    try:
        details = tracking_service.get_shipment_details(shipment_id)
        
        if not details:
            raise HTTPException(status_code=404, detail="Shipment not found")
        
        return details
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching shipment tracking: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch shipment tracking: {str(e)}"
        )


@app.post(f"{settings.api_prefix}/tracking/initialize")
async def initialize_tracking():
    """Initialize tracking data for all active shipments."""
    logger.info("Initializing tracking data")
    
    try:
        result = tracking_service.initialize_tracking_data()
        return result
    except Exception as e:
        logger.error(f"Error initializing tracking: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to initialize tracking: {str(e)}"
        )


@app.post(f"{settings.api_prefix}/tracking/update-locations")
async def update_shipment_locations():
    """Update locations for all in-transit shipments (simulation)."""
    logger.info("Updating shipment locations")
    
    try:
        result = tracking_service.update_locations()
        return result
    except Exception as e:
        logger.error(f"Error updating locations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update locations: {str(e)}"
        )


# ===== Order Journey Endpoints =====

@app.get(f"{settings.api_prefix}/journey/stats")
async def get_journey_stats():
    """Get summary statistics for order journeys."""
    logger.info("Fetching journey statistics")
    
    try:
        stats = journey_service.get_journey_stats()
        return stats
    except Exception as e:
        logger.error(f"Error fetching journey stats: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch journey stats: {str(e)}"
        )


@app.get(f"{settings.api_prefix}/journey/orders")
async def get_all_journeys(status: str = None):
    """
    Get all order journeys with summary information.
    
    Query params:
        - status: Filter by order status (pending, processing, shipped, delivered)
    """
    logger.info(f"Fetching order journeys - status: {status}")
    
    try:
        journeys = journey_service.get_all_journeys(status_filter=status)
        return {
            "count": len(journeys),
            "journeys": journeys
        }
    except Exception as e:
        logger.error(f"Error fetching journeys: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch journeys: {str(e)}"
        )


@app.get(f"{settings.api_prefix}/journey/orders/{{order_id}}")
async def get_order_journey_details(order_id: str):
    """Get complete end-to-end journey for a specific order."""
    logger.info(f"Fetching journey details for order: {order_id}")
    
    try:
        journey = journey_service.get_order_journey(order_id)
        
        if not journey:
            raise HTTPException(status_code=404, detail="Order not found")
        
        return journey
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching order journey: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch order journey: {str(e)}"
        )


@app.post(f"{settings.api_prefix}/admin/refresh-data")
async def refresh_dashboard_data():
    """
    Refresh all time-sensitive dashboard data to reflect current time.
    
    Updates:
    - Shipment tracking positions and statuses
    - Uses the existing tracking service update mechanism
    
    This endpoint makes the dashboards show realistic "live" data.
    """
    logger.info("Manual data refresh requested")
    
    try:
        # Use the existing tracking service update method
        update_result = tracking_service.update_locations()
        initialize_result = tracking_service.initialize_tracking_data()
        
        return {
            "status": "success",
            "message": "Dashboard data refreshed successfully",
            "results": {
                "tracking_updated": update_result,
                "tracking_initialized": initialize_result,
                "timestamp": datetime.utcnow().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Error refreshing data: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to refresh data: {str(e)}"
        )


# ============================================================================
# Chat Endpoints (8NAPAI) - TEMPORARILY DISABLED
# Requires RAG dependencies: sentence-transformers, chromadb, faiss-cpu, etc.
# ============================================================================

# @app.post(f"{settings.api_prefix}/chat/message", response_model=ChatResponse)
# async def chat_message(request: ChatRequest, current_user: dict = Depends(get_optional_user)):
#     """
#     Send message to 8NAPAI and get response using RAG.
#     
#     Args:
#         request: Chat request with user message
#         current_user: Optional authenticated user
#     
#     Returns:
#         AI response with timestamp
#     """
#     try:
#         logger.info(f"💬 Chat request: message='{request.message[:50]}...', include_context={request.include_context}")
#         
#         # Get RAG chat service (lazy-loaded)
#         chat_svc = get_chat_service()
#         
#         response = chat_svc.chat(
#             user_message=request.message,
#             include_context=request.include_context
#         )
#         
#         return ChatResponse(
#             response=response,
#             timestamp=datetime.utcnow()
#         )
#     except Exception as e:
#         logger.error(f"Error in chat: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Chat service error: {str(e)}"
#         )


# @app.get(f"{settings.api_prefix}/chat/suggestions", response_model=SuggestedQuestionsResponse)
# async def get_suggestions():
#     """
#     Get suggested questions for users.
#     
#     Returns:
#         List of suggested questions
#     """
#     try:
#         questions = chat_service.get_suggested_questions()
#         return SuggestedQuestionsResponse(questions=questions)
#     except Exception as e:
#         logger.error(f"Error getting suggestions: {e}")
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to get suggestions: {str(e)}"
#         )


# @app.post(f"{settings.api_prefix}/chat/refresh-kpis")
# async def refresh_kpi_data(credentials: HTTPAuthorizationCredentials = Depends(security)):
#     """
#     Refresh KPI data in RAG index.
#     
#     This endpoint updates the vector index with current KPI values
#     from the dashboard service, ensuring chatbot responses match
#     dashboard displays exactly.
#     
#     Should be called:
#     - After significant data changes
#     - On a schedule (hourly/daily)
#     - Before important demos
#     """
#     try:
#         # Verify authentication (admin only)
#         if not credentials:
#             raise HTTPException(status_code=401, detail="Authentication required")
#         
#         user = await auth_service.verify_token(credentials.credentials)
#         if not user or user.get('role') != 'admin':
#             raise HTTPException(status_code=403, detail="Admin access required")
#         
#         logger.info(f"KPI refresh requested by user: {user.get('username')}")
#         
#         # Get RAG service and refresh KPI data
#         rag_service = get_rag_chat_service()
#         
#         # Call rebuild on the indexer
#         logger.info("Starting KPI data refresh...")
#         rag_service.indexer.refresh_kpi_data()
#         
#         stats = rag_service.get_statistics()
#         
#         return {
#             "success": True,
#             "message": "KPI data refreshed successfully",
#             "timestamp": datetime.utcnow().isoformat(),
#             "total_documents": stats.get('total_documents', 0),
#             "refreshed_by": user.get('username')
#         }
#         
#     except HTTPException:
#         raise
#     except Exception as e:
#         logger.error(f"Error refreshing KPI data: {e}", exc_info=True)
#         raise HTTPException(
#             status_code=500,
#             detail=f"Failed to refresh KPI data: {str(e)}"
#         )


# @app.get(f"{settings.api_prefix}/chat/stats")
# async def get_chat_stats():
#     """Get RAG system statistics."""
#     try:
#         rag_service = get_rag_chat_service()
#         stats = rag_service.get_statistics()
#         return stats
#     except Exception as e:
#         logger.error(f"Error getting chat stats: {e}")
#         raise HTTPException(status_code=500, detail=str(e))


# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Handle 404 errors."""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=404,
        content={
            "error": "Not Found",
            "message": "The requested resource was not found",
            "path": str(request.url)
        }
    )


@app.exception_handler(500)
async def internal_error_handler(request, exc):
    """Handle 500 errors."""
    from fastapi.responses import JSONResponse
    logger.error(f"Internal error: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "An unexpected error occurred",
            "details": str(exc) if settings.debug else "Contact support"
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
