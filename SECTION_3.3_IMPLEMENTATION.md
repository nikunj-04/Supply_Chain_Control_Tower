# Section 3.3 — Implementation: Development and Deployment Procedures

## Project: E-commerce Fulfillment Operations Control Tower

---

## Overview

This section documents how the system is set up for development, how it initializes at runtime, how services start in sequence, and what the recommended production deployment structure looks like. It also covers the data population and testing procedures used during development.

---

## 3.3.1 — Development Environment Setup

The project is split into two top-level directories: `backend/` for the FastAPI Python application and `frontend/` for the React application.

### Backend Setup Procedure

```
Step 1:  Navigate to the backend directory
         cd backend

Step 2:  Create a Python virtual environment
         python -m venv venv

Step 3:  Activate the virtual environment
         Windows:  venv\Scripts\activate

Step 4:  Install all Python dependencies
         pip install -r requirements.txt

Step 5:  Copy the environment file template
         copy .env.example .env

Step 6:  Edit .env to set configuration values
         (database paths, app name, debug mode, CORS origins)

Step 7:  Start the backend server
         python main.py
         Server starts on:  http://localhost:8000
         API documentation: http://localhost:8000/api/docs
```

Key backend dependencies (from `requirements.txt`):
- `fastapi` — REST API framework
- `uvicorn` — ASGI server
- `sqlalchemy` — ORM for all six databases
- `reportlab` — PDF generation for invoice files
- `pydantic` — Request/response schema validation

---

### Frontend Setup Procedure

```
Step 1:  Navigate to the frontend directory
         cd frontend

Step 2:  Install Node.js dependencies
         npm install

Step 3:  Verify API base URL in api/dashboard.js
         Default: http://localhost:8000/api/v1

Step 4:  Start the Vite development server
         npm run dev
         Frontend loads at:  http://localhost:3000
```

Key frontend dependencies (from `package.json`):
- `react` — UI library
- `vite` — Build tool and dev server

---

### Directory Structure

```
supplychain/
│
├── backend/
│   ├── main.py                   FastAPI application entry point
│   ├── config.py                 Environment settings (paths, CORS, debug mode)
│   ├── logger.py                 Logging configuration
│   ├── schemas.py                Pydantic request/response models
│   │
│   ├── models/                   SQLAlchemy database models
│   │   ├── auth_models.py        Users, roles, permissions, sessions, audit logs
│   │   ├── billing_models.py     Invoices, billing line items, billing metrics
│   │   ├── exception_models.py   Exceptions, exception actions
│   │   ├── oms_models.py         Orders, order items, order metrics
│   │   ├── returns_models.py     Return orders, return items, return metrics
│   │   ├── tms_models.py         Shipments, tracking data, transport metrics
│   │   ├── wms_models.py         Inventory, picking tasks, warehouse metrics
│   │   └── yard_models.py        Dock appointments, yard locations, yard metrics
│   │
│   ├── services/                 Business logic layer
│   │   ├── auth_service.py       Login, token management, RBAC, audit logging
│   │   ├── billing_service.py    Accessorial charge billing and PDF generation
│   │   ├── dashboard_service.py  Cross-system aggregation, KPIs, scorecard
│   │   ├── exception_service.py  Exception detection, CRUD, state management
│   │   ├── journey_service.py    End-to-end order timeline builder
│   │   └── tracking_service.py   Shipment location tracking and updates
│   │
│   ├── utils/
│   │   └── pdf_generator.py      InvoicePDFGenerator class using ReportLab
│   │
│   ├── scripts/
│   │   ├── seed_data.py          Initial database seeding with sample records
│   │   ├── seed_auth_data.py     Creates 5 default roles and seed users
│   │   ├── populate_live_data.py Adds 30-80 new records across all 6 systems
│   │   └── run_live_data_scheduler.py  Runs populate_live_data.py every 5 minutes
│   │
│   ├── data/                     Auto-created database files at runtime
│   │   ├── wms.db
│   │   ├── oms.db
│   │   ├── tms.db
│   │   ├── billing.db
│   │   ├── returns.db
│   │   └── yard.db
│   │
│   └── invoices/                 Auto-created PDF invoice storage
│
└── frontend/
    ├── index.html
    ├── vite.config.js
    ├── package.json
    └── src/
        ├── App.jsx               Root component, routing, state management
        ├── api/
        │   └── dashboard.js      All API call functions (axios/fetch wrappers)
        ├── components/           21 UI components (see Section 3.1)
        ├── context/
        │   └── GlobalFiltersContext.jsx  React context for shared filter state
        └── utils/
            └── permissions.js    Role/permission check utility functions
```

---

## 3.3.2 — Database Initialization Sequence

At application startup, `main.py` initializes all seven databases before the FastAPI server begins accepting requests. Each database is created at the file path defined in `config.py`. If the file already exists, initialization is skipped gracefully.

### Initialization Order

```
Application Start  →  main.py runs
         │
         ├── 1. init_billing_db(settings.billing_db_path)
         │       Creates: invoices, billing_line_items, billing_metrics tables
         │
         ├── 2. init_wms_db(settings.wms_db_path)
         │       Creates: inventory, picking_tasks, warehouse_metrics tables
         │
         ├── 3. init_oms_db(settings.oms_db_path)
         │       Creates: orders, order_items, order_metrics tables
         │
         ├── 4. init_tms_db(settings.tms_db_path)
         │       Creates: shipments, tracking_data, transport_metrics tables
         │
         ├── 5. init_returns_db(settings.returns_db_path)
         │       Creates: return_orders, return_items, return_metrics tables
         │
         ├── 6. init_yard_db(settings.yard_db_path)
         │       Creates: dock_appointments, yard_locations, yard_metrics tables
         │
         ├── 7. Auth DB initialized on first AuthService() instantiation
         │       Creates: users, roles, permissions, user_roles,
         │                role_permissions, user_sessions, audit_logs tables
         │
         ├── 8. Service Instances Created
         │       billing_service = BillingService()
         │       tracking_service = TrackingService()
         │       journey_service = JourneyService()
         │       (Exception Service created fresh per request)
         │
         └── 9. FastAPI app starts accepting requests on port 8000
```

If any database initialization fails, an error is logged but the application continues starting. Endpoints that depend on the failed database will return HTTP 500 errors.

---

## 3.3.3 — Service Startup Sequence

The following describes the initialization order and dependencies between services when the application boots.

```
Order  Service                 Dependency              Notes
────────────────────────────────────────────────────────────────────
  1    Auth Service            Auth DB                 Required by all endpoints that validate tokens
  2    Dashboard Service       All 6 system DBs        Core aggregation engine, used by most endpoints
  3    Billing Service         Billing DB, Yard DB     Also initializes InvoicePDFGenerator
  4    Tracking Service        TMS DB                  Loads initial shipment data on instantiation
  5    Journey Service         OMS DB, TMS DB,         Pre-caches journey calculation logic
                               Billing DB
  6    Exception Service       All 6 system DBs        Created fresh per request (not pre-initialized)
  7    FastAPI / Uvicorn        All services ready      Begins accepting HTTP connections on port 8000
```

Total typical startup time: 2 to 5 seconds on a standard development machine.

---

## 3.3.4 — Deployment Architecture

### Current Development Deployment

In development, both services run on a single machine. There is no containerization or reverse proxy.

```
Developer Machine
│
├── Backend Process  (python main.py)
│     Port: 8000
│     Server: Uvicorn (ASGI)
│     Databases: 6 SQLite .db files in backend/data/
│     Invoice Files: backend/invoices/ (PDF storage)
│
└── Frontend Process  (npm run dev)
      Port: 3000
      Server: Vite dev server
      API Target: http://localhost:8000
```

---

### Recommended Production Deployment

The following architecture is the recommended production setup. It separates the frontend, backend, and database into distinct infrastructure components.

```
                         ┌─────────────────────────┐
  Internet Traffic  ───► │    Nginx Web Server       │
                         │    (Frontend Host)         │
                         │                           │
                         │  Serves React dist/       │
                         │  Reverse proxies /api/*   │
                         │  to Backend Server        │
                         └────────────┬──────────────┘
                                      │  Proxy /api/*
                                      ▼
                         ┌─────────────────────────┐
                         │    Backend Server         │
                         │    (Gunicorn + Uvicorn)   │
                         │                           │
                         │  FastAPI Application      │
                         │  Multiple worker threads  │
                         │  Reads/writes DB and PDFs │
                         └────────────┬──────────────┘
                                      │
                    ┌─────────────────┼───────────────────┐
                    ▼                 ▼                    ▼
         ┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
         │  PostgreSQL   │   │    Redis      │   │  Object Storage  │
         │  Database     │   │    Cache      │   │  (e.g. AWS S3)   │
         │  (replaces    │   │  (sessions,   │   │  Invoice PDFs    │
         │   SQLite)     │   │   hot data)   │   └──────────────────┘
         └──────────────┘   └──────────────┘
```

**Production Deployment Steps:**

```
Step 1:  Build the React frontend for production
         cd frontend && npm run build
         Output: frontend/dist/ folder

Step 2:  Configure Nginx
         - Serve frontend/dist/ as the web root
         - Proxy all /api/* requests to backend:8000

Step 3:  Replace SQLite databases with PostgreSQL
         - Update database connection strings in config.py
         - Run database migrations

Step 4:  Configure Redis for session caching (optional)
         - Speeds up token validation on high-traffic deployments

Step 5:  Configure S3 or equivalent for invoice PDF storage
         - Update InvoicePDFGenerator to write to cloud storage
         - Update download URLs to point to cloud storage bucket

Step 6:  Start backend with Gunicorn
         gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

Step 7:  Configure SSL certificates on Nginx (HTTPS)

Step 8:  Set CORS origins in config.py to production domain
```

---

## 3.3.5 — Data Population Procedures

Three scripts are provided to populate databases with realistic sample data for development and demonstration purposes.

### Script 1 — One-Time Initial Seed (`scripts/seed_data.py`)

Run via `setup.bat`. Populates all six system databases with baseline records. Creates realistic data: customers, orders, shipments, inventory items, invoices, returns, and dock appointments.

Use case: First-time environment setup or resetting data to a clean baseline.

---

### Script 2 — Auth Data Seed (`scripts/seed_auth_data.py`)

Creates the five default roles and their associated permissions. Creates a set of seed user accounts for each role.

Default seed user credentials:
| Username | Role |
|----------|------|
| admin | system_admin |
| ops_manager | operations_manager |
| wh_manager | warehouse_manager |
| supervisor | supervisor |
| customer1 | customer_user |

---

### Script 3 — Live Data Population (`scripts/populate_live_data.py`)

Run via `populate-data.bat`. Adds 30 to 80 new records across all six systems in a single run. Designed to simulate a wave of business activity.

Records created per run:
| System | New Records |
|--------|------------|
| OMS | 3 to 7 new orders |
| TMS | 3 to 7 new shipments |
| WMS | 20 inventory quantity updates |
| WMS | 5 to 10 new picking tasks |
| Billing | 2 to 5 new invoices |
| Returns | 1 to 3 new return orders |
| Yard | 2 to 5 new dock appointments |

---

### Script 4 — Continuous Scheduler (`scripts/run_live_data_scheduler.py`)

Run via `run-data-scheduler.bat`. Calls `populate_live_data.py` every 5 minutes automatically.

Use case: Long-running demos where the dashboard should show changing data over time.

---

## 3.3.6 — Testing Procedures

Unit and integration tests are located in `backend/tests/` and several standalone test files in `backend/`.

### Running Tests

```
cd backend
pytest                        Run all tests
pytest tests/                 Run tests in tests/ directory
pytest test_billing_service.py    Run specific test file
pytest --tb=short             Show concise failure output
```

### Test Files

| File | What it Tests |
|------|--------------|
| `tests/test_billing_dashboard_services.py` | Billing service methods, invoice creation |
| `tests/test_exception_service.py` | Exception detection and CRUD operations |
| `tests/test_journey_service.py` | Order journey timeline construction |
| `tests/test_tracking_service.py` | Shipment tracking queries and location updates |
| `test_kpi_calculation.py` | KPI aggregation formulas |
| `test_chat_context.py` | Context building for chat service |
| `test_context_build.py` | Context assembly logic |

### Test Configuration

`pytest.ini` in the backend directory configures the test runner with:
- Test discovery paths
- Log level settings
- Custom markers (if any)

---

## 3.3.7 — Configuration Reference

All backend configuration is managed through the `config.py` file, which reads values from the `.env` file using Pydantic's `BaseSettings`.

| Setting | Default Value | Description |
|---------|--------------|-------------|
| `app_name` | E-commerce Fulfillment Control Tower | Application name shown in API docs |
| `app_version` | 1.0.0 | Version string |
| `debug` | False | Enables debug logging |
| `api_prefix` | /api/v1 | URL prefix for all API routes |
| `cors_origins` | ["http://localhost:3000"] | Allowed CORS origins |
| `billing_db_path` | data/billing.db | Path to billing SQLite file |
| `wms_db_path` | data/wms.db | Path to WMS SQLite file |
| `oms_db_path` | data/oms.db | Path to OMS SQLite file |
| `tms_db_path` | data/tms.db | Path to TMS SQLite file |
| `returns_db_path` | data/returns.db | Path to Returns SQLite file |
| `yard_db_path` | data/yard.db | Path to Yard SQLite file |
| `auth_db_path` | data/auth.db | Path to Auth SQLite file |
