# Section 3.1 — System Architecture / Block Diagram

## Project: E-commerce Fulfillment Operations Control Tower

---

## Overview

The system is a web-based supply chain control tower that integrates six independent legacy enterprise systems into a single unified dashboard. Users can monitor live operations, detect exceptions, manage billing, track shipments, and view end-to-end order journeys — all from one central interface.

The architecture follows a three-tier pattern:
- **Data Tier** — Six SQLite databases, one per enterprise system
- **Service Tier** — Python FastAPI backend with six service modules
- **Presentation Tier** — React single-page application (SPA) served on port 3000

---

## Block Diagram Description (for Figma)

The block diagram has five horizontal layers stacked top to bottom:

```
┌───────────────────────────────────────────────────────────────────┐
│                      PRESENTATION LAYER                           │
│                React SPA  ·  Frontend Port 3000                   │
│     [Auth UI]  [Dashboard Views]  [Exception Center]  [Reports]   │
└──────────────────────────────┬────────────────────────────────────┘
                               │  HTTP REST API calls (JSON)
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│                       API GATEWAY LAYER                           │
│              FastAPI Application  ·  Backend Port 8000            │
│    CORS Middleware  ·  Bearer Token Auth  ·  Static File Serving  │
└──────────────────────────────┬────────────────────────────────────┘
                               │  Service method calls
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│                       SERVICE LAYER                               │
│  [Dashboard Service]  [Auth Service]  [Billing Service]           │
│  [Exception Service]  [Tracking Service]  [Journey Service]       │
└──────────────────────────────┬────────────────────────────────────┘
                               │  SQLAlchemy ORM queries
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│                        DATA ACCESS LAYER                          │
│  [WMS DB]  [OMS DB]  [TMS DB]  [Billing DB]  [Returns DB]        │
│  [Yard DB]  [Auth DB]  [Invoice PDF Storage /invoices/]           │
└───────────────────────────────────────────────────────────────────┘
```

---

## Layer 1 — Integrated Legacy Systems (Data Sources)

Six simulated enterprise systems act as data sources. Each system has its own isolated SQLite database and data model.

| System | Database File | Tables | Purpose |
|--------|--------------|--------|---------|
| **WMS** — Warehouse Management System | `wms.db` | `inventory`, `picking_tasks`, `warehouse_metrics` | Tracks stock levels, picking tasks, and warehouse performance |
| **OMS** — Order Management System | `oms.db` | `orders`, `order_items`, `order_metrics` | Manages customer orders, order status, and fulfillment metrics |
| **TMS** — Transportation Management System | `tms.db` | `shipments`, `tracking_data`, `transport_metrics` | Manages carrier shipments, routes, and transport performance |
| **Billing System** | `billing.db` | `invoices`, `billing_line_items`, `billing_metrics` | Handles invoices, accessorial charges, and revenue tracking |
| **Returns Management System** | `returns.db` | `return_orders`, `return_items`, `return_metrics` | Manages product returns, RMA processing, and return analytics |
| **Yard Management System** | `yard.db` | `dock_appointments`, `yard_locations`, `yard_metrics` | Tracks dock usage, gate appointments, and yard occupancy |

---

## Layer 2 — Backend Service Layer (FastAPI)

The backend runs as a FastAPI application on **port 8000**. It exposes a RESTful API and houses six service modules, each with a specific domain responsibility.

### Service Modules

**1. Dashboard Service** (`services/dashboard_service.py`)
- Acts as the central aggregation engine
- Queries all six databases to compute KPIs, scorecard metrics, and exception data
- Provides endpoints for: Operational Scorecard, KPI Dashboard, Accessorial Charges, Client Profitability, Billing Analytics, Warehouse Performance, Carrier Scorecards, Labor Efficiency, Inventory Optimization, Standard Reports, Custom Reports, Scheduled Exports
- Applies client-level data isolation for customer role users

**2. Auth Service** (`services/auth_service.py`)
- Handles user login, token generation, token validation, and logout
- Manages RBAC: creates sessions, enforces role-based permissions, writes audit logs
- Manages five roles: `system_admin`, `operations_manager`, `warehouse_manager`, `supervisor`, `customer_user`
- Access token valid for 8 hours; refresh token valid for 30 days

**3. Billing Service** (`services/billing_service.py`)
- Processes accessorial charge billing requests
- Queries dock appointments and shipment data to build invoice records
- Generates unique invoice numbers using timestamp + UUID6 format: `INV-{YYYYMMDDHHmmss}-{UUID6}`
- Creates `invoices` and `billing_line_items` records in billing database
- Generates PDF invoice using `InvoicePDFGenerator` and saves to `/invoices/` folder

**4. Exception Service** (`services/exception_service.py`)
- Detects operational anomalies by querying all six system databases
- Creates exception records classified by severity: `critical`, `warning`, `info`
- Supports CRUD operations: assign, update status, add notes, resolve, dismiss
- Each state change is logged as an action record for audit trail
- A fresh service instance is created per request to prevent stale sessions

**5. Tracking Service** (`services/tracking_service.py`)
- Queries TMS shipments with status `in_transit` or `out_for_delivery`
- Maintains simulated GPS-style location updates per shipment
- Calculates ETA and detects delays by comparing against `expected_delivery`
- Exposes endpoint to initialize tracking data and to push location updates

**6. Journey Service** (`services/journey_service.py`)
- Builds end-to-end order timelines by joining data from OMS, WMS, TMS, Billing, and Returns
- Constructs a chronological milestone list per order
- Calculates cycle time metrics: order-to-ship days, in-transit days, total cycle time

---

## Layer 3 — Security & Access Control

Security is enforced via two mechanisms: JWT-based token authentication and Role-Based Access Control (RBAC).

### Authentication Flow
- User submits credentials via `POST /api/v1/auth/login`
- Auth Service validates password hash using SHA-256
- On success: returns `access_token`, `refresh_token`, and full user object
- All protected endpoints validate the `Bearer` token via the `get_current_user` dependency
- Optional authentication (`get_optional_user`) is used for dashboard endpoints — unauthenticated users still receive data but without client filtering

### Role-Based Access Control (RBAC)

| Role | Display Name | Key Access |
|------|-------------|-----------|
| `system_admin` | System Administrator | Full access to all views, user management, audit logs |
| `operations_manager` | Operations Manager | Dashboards, exceptions, tracking, billing, reports |
| `warehouse_manager` | Warehouse Manager | Warehouse performance, inventory, labor, yard |
| `supervisor` | Supervisor | Exceptions view, tracking, basic reports |
| `customer_user` | Customer | Shipment tracking, order journey (own data only) |

Permissions follow the format `module.action` (e.g., `billing.process`, `exceptions.resolve`, `admin.users`). Each role maps to a set of permissions stored in the `role_permissions` table. All permission checks are enforced at the service layer.

---

## Layer 4 — Data Layer

Each system has a dedicated SQLite database stored in `backend/data/`. Databases are initialized at application startup via `init_*_db()` functions in each model file.

An additional **Auth Database** (`auth.db`) holds the identity and access management tables: `users`, `roles`, `permissions`, `user_roles`, `role_permissions`, `user_sessions`, and `audit_logs`.

**Invoice Storage:** PDF files generated during billing are saved to `backend/invoices/`. They are served by FastAPI's `StaticFiles` mount at the `/invoices/` URL path.

---

## Layer 5 — Frontend (React SPA)

The frontend is a React Single-Page Application built with Vite, served on **port 3000** during development. The application uses `localStorage` for token storage and session management.

### Implemented Components (21 total)

| Component | Dashboard Section |
|-----------|-----------------|
| `Login.jsx` | Authentication screen |
| `Header.jsx` | Top navigation bar |
| `Sidebar.jsx` | Left navigation menu (role-based visibility) |
| `OperationalScorecard.jsx` | System-wide KPI overview |
| `KPIDashboard.jsx` | 6-category KPI metrics |
| `ExceptionsPanel.jsx` | Lightweight exception alerts widget |
| `ExceptionCenter.jsx` | Full exception management (assign, resolve, note) |
| `ShipmentTracking.jsx` | Real-time shipment location view |
| `OrderJourney.jsx` | End-to-end order timeline |
| `AccessorialCharges.jsx` | Revenue recovery — Bill Now and download invoice |
| `ClientProfitability.jsx` | Per-client revenue and margin analytics |
| `BillingAnalytics.jsx` | Invoice status, DSO, revenue trends |
| `WarehousePerformance.jsx` | Inventory accuracy, pick rates, capacity |
| `CarrierScorecards.jsx` | On-time delivery rates per carrier |
| `LaborEfficiency.jsx` | Worker productivity and task completion |
| `InventoryOptimization.jsx` | Stock health, ABC analysis, reorder recommendations |
| `StandardReports.jsx` | Pre-built report catalog |
| `CustomReports.jsx` | Report builder with field selector |
| `ScheduledExports.jsx` | Scheduled report management |
| `UserManagement.jsx` | Create, edit, deactivate users (admin only) |
| `AuditLogViewer.jsx` | Full audit trail viewer (admin only) |

---

## Key Architecture Decisions

1. **One Database Per System** — Each of the six legacy systems has its own SQLite database, simulating real-world isolation between enterprise systems. The control tower reads across them without coupling the systems to each other.

2. **Stateless Services** — All service modules are stateless. The Exception Service is explicitly re-instantiated per request to avoid SQLAlchemy session conflicts.

3. **Aggregation at the Service Layer** — The Dashboard Service performs all cross-system joins and calculations at query time. There is no separate data warehouse or ETL pipeline.

4. **PDF Generation at Billing Time** — Invoice PDFs are generated synchronously when the "Bill Now" action is triggered. The file is written to disk and a download URL is returned immediately.

5. **Role-Based UI Rendering** — The frontend uses a `permissions.js` utility to conditionally render navigation items, action buttons, and data views based on the logged-in user's permissions.

6. **Client-Level Data Isolation** — Users with the `customer_user` role have a `client_id` attribute. The Dashboard Service filters all query results to records matching that `client_id`, preventing cross-client data exposure.

---

## Technology Stack Summary

| Layer | Technology | Version |
|-------|-----------|---------|
| Frontend Framework | React | 18.x |
| Frontend Build Tool | Vite | 5.x |
| Backend Framework | FastAPI | Latest |
| Backend Server | Uvicorn (ASGI) | Latest |
| ORM | SQLAlchemy | Latest |
| Database | SQLite | Per-system |
| PDF Generation | ReportLab (custom generator) | Latest |
| Password Hashing | SHA-256 (hashlib) | stdlib |
| Token Generation | secrets.token_hex | stdlib |
| CORS | FastAPI CORSMiddleware | Built-in |
