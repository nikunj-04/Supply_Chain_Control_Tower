# Section 3.2 — Proposed Methodology

## Project: E-commerce Fulfillment Operations Control Tower

---

## Overview

This section describes the methodology used to design, integrate, and deliver the control tower platform. It covers: the use case model defining who uses the system and how, the data flow showing how information travels from source systems to the user interface, the request-response cycle for key API interactions, and the data transformation pipeline that converts raw records into actionable dashboard metrics.

---

## 3.2.1 — Use Case Model

### Actors and Roles

The system has five user roles. Each role represents a distinct persona with a different scope of access.

| Actor | Role Name | Description |
|-------|-----------|-------------|
| **System Administrator** | `system_admin` | Full access. Manages users, views all data, accesses audit logs |
| **Operations Manager** | `operations_manager` | Manages exceptions, billing, tracking, and operational reports |
| **Warehouse Manager** | `warehouse_manager` | Focuses on warehouse, inventory, labor, and yard operations |
| **Supervisor** | `supervisor` | Views exceptions, tracking, and basic reports |
| **Customer User** | `customer_user` | Limited to own shipment tracking and order journey |

---

### Use Case Table

The table below lists all implemented use cases and which roles can perform them.

| # | Use Case | Admin | Ops Mgr | WH Mgr | Supervisor | Customer |
|---|----------|:-----:|:-------:|:------:|:----------:|:--------:|
| UC1 | Authenticate and Login | ✅ | ✅ | ✅ | ✅ | ✅ |
| UC2 | View Operational Scorecard | ✅ | ✅ | ✅ | ✅ | ✅ |
| UC3 | View KPI Dashboard (6 categories) | ✅ | ✅ | — | — | — |
| UC4 | View Exceptions and Alerts | ✅ | ✅ | ✅ | ✅ | — |
| UC5 | Assign Exception to a User | ✅ | ✅ | — | — | — |
| UC6 | Resolve or Dismiss Exception | ✅ | ✅ | ✅ | — | — |
| UC7 | Add Note to Exception | ✅ | ✅ | ✅ | ✅ | — |
| UC8 | View Real-Time Shipment Tracking | ✅ | ✅ | — | ✅ | ✅ |
| UC9 | View Order Journey (end-to-end) | ✅ | ✅ | — | — | ✅ |
| UC10 | View Warehouse Performance | ✅ | — | ✅ | — | — |
| UC11 | Bill Accessorial Charges (Bill Now) | ✅ | ✅ | — | — | — |
| UC12 | Download Invoice PDF | ✅ | ✅ | — | — | — |
| UC13 | View Client Profitability | ✅ | ✅ | — | — | — |
| UC14 | View Billing Analytics | ✅ | ✅ | — | — | — |
| UC15 | View Carrier Scorecards | ✅ | ✅ | — | — | — |
| UC16 | View Labor Efficiency | ✅ | — | ✅ | — | — |
| UC17 | View Inventory Optimization | ✅ | — | ✅ | — | — |
| UC18 | Generate Standard Reports | ✅ | ✅ | ✅ | ✅ | — |
| UC19 | Build Custom Reports | ✅ | ✅ | — | — | — |
| UC20 | Manage Scheduled Exports | ✅ | ✅ | — | — | — |
| UC21 | Manage Users and Roles | ✅ | — | — | — | — |
| UC22 | View Audit Logs | ✅ | — | — | — | — |

---

### Use Case Diagram Description (for Figma)

Draw a UML Use Case Diagram with the following structure:

- **System boundary box** labeled "E-commerce Fulfillment Control Tower"
- **Five actor stick figures** on the left side, stacked vertically:
  - System Admin (top)
  - Operations Manager
  - Warehouse Manager
  - Supervisor
  - Customer User (bottom)
- **22 use case ovals** inside the system boundary
- **Arrows from actors to use cases** following the matrix above
- System Admin should have arrows to all 22 use cases
- Customer User should only connect to UC1, UC2, UC8, UC9

---

## 3.2.2 — Data Flow Diagram

This diagram describes how data flows from the six source systems through the backend service layer and into the frontend dashboard.

### Data Flow Stages

**Stage 1 — Data Origination (Source Systems)**

Each of the six enterprise systems produces raw transactional records stored in their own isolated SQLite databases:

- WMS produces: inventory quantities, picking task records, warehouse metrics
- OMS produces: order records with status and delivery dates, order metrics
- TMS produces: shipment records with carrier and route data, transport metrics
- Billing System produces: invoices, billing line items, billing metrics
- Returns System produces: return orders, RMA records, return metrics
- Yard System produces: dock appointments with times and durations, yard metrics

**Stage 2 — Data Aggregation (Dashboard Service)**

The Dashboard Service connects to all six databases using SQLAlchemy ORM sessions. It executes queries across all systems concurrently, merges results, and returns structured response objects. This service is the single source of truth for all dashboard data.

Key operations performed:
- Computes six KPI categories by running SQL aggregation queries
- Identifies exception conditions (e.g., low stock, delayed shipments, overdue invoices)
- Joins shipment and order data to build tracking and journey views
- Applies client-level data filtering for customer-role users

**Stage 3 — Exception Detection (Exception Service)**

The Exception Service runs separate detection queries against each system:
- WMS: finds items where `quantity_on_hand` < `reorder_point`
- OMS: finds orders where `status = pending` and `order_date` > 3 days ago
- TMS: finds shipments where `status = in_transit` and `expected_delivery` < today
- Billing: finds invoices where `status = pending` and `invoice_date` > 30 days ago
- Returns: finds return orders where `status = pending` and `created_at` > 14 days ago
- Yard: finds dock appointments where `status = scheduled` and `appointment_time` < now

Detected anomalies are classified by severity (`critical`, `warning`, `info`) and stored as exception records.

**Stage 4 — Billing Processing (Billing Service)**

When a user clicks "Bill Now" for an accessorial charge:
1. Billing Service reads dock appointment details from Yard DB
2. Reads shipment reference from TMS DB (falls back to charge ID if no shipment)
3. Creates an invoice record in Billing DB
4. Creates a billing line item linking the invoice to the accessorial charge
5. Generates a PDF file and saves it to `/invoices/`
6. Returns the invoice number and download URL to the frontend

**Stage 5 — Presentation (React Frontend)**

The frontend calls specific API endpoints for each dashboard section. It renders data based on the logged-in user's role and permissions. Action buttons (e.g., "Bill Now", "Resolve", "Assign") are shown or hidden depending on the user's permission set.

---

### Data Flow Diagram Description (for Figma)

Draw a Data Flow Diagram with three vertical columns:

**Left Column — Source Systems (6 boxes)**
- WMS System
- OMS System
- TMS System
- Billing System
- Returns System
- Yard System

**Middle Column — Backend Services (6 boxes)**
- Dashboard Service (receives from all 6 source systems)
- Exception Service (receives from all 6 source systems)
- Billing Service (receives from TMS and Yard)
- Tracking Service (receives from TMS)
- Journey Service (receives from OMS, TMS, Billing)
- Auth Service (standalone — reads/writes Auth DB)

**Right Column — Output Targets (4 boxes)**
- KPI Metrics → React KPI Dashboard
- Exception Log → React Exception Center
- Invoice Records + PDF Files → React Billing View
- Audit Log → React Audit Log Viewer

Draw arrows from each source system to the relevant backend services, and from each backend service to its output target. Label each arrow with a short description of what data is transferred.

---

## 3.2.3 — API Request-Response Cycle

This section describes the step-by-step sequence for five key operations.

---

### Sequence 1 — User Login

```
1. User submits username and password in the Login form
2. Frontend sends:  POST /api/v1/auth/login  (form-encoded body)
3. FastAPI routes request to the login endpoint function
4. Auth Service queries the users table for the given username
5. Verifies the SHA-256 password hash
6. Creates a UserSession record with a generated access token and refresh token
7. Writes a login audit log entry
8. Returns: { user object, access_token, refresh_token, expires_at }
9. Frontend stores tokens in localStorage
10. Frontend loads the default dashboard view based on user role
```

---

### Sequence 2 — Dashboard Data Load

```
1. Frontend calls:  GET /api/v1/dashboard/scorecard
   Header: Authorization: Bearer <access_token>
2. FastAPI validates the Bearer token via get_current_user dependency
3. Auth Service looks up the session, verifies token, returns user object
4. Dashboard Service sets current_user for client filtering
5. Dashboard Service executes queries against all 6 databases:
   - WMS DB → inventory counts, pick completion rate
   - OMS DB → order counts, on-time delivery %
   - TMS DB → shipment counts, delayed count
   - Billing DB → outstanding balance, collection rate
   - Returns DB → return rate, processing time
   - Yard DB → dock utilization, missed appointments
6. Aggregates results into OperationalScorecardResponse object
7. Returns JSON with metrics for all 6 systems
8. Frontend renders the Operational Scorecard component
```

---

### Sequence 3 — Exception Detection and Update

```
Detection:
1. Frontend calls:  GET /api/v1/dashboard/exceptions
2. Dashboard Service calls exception detection logic
3. Exception Service queries all 6 databases for anomalies
4. Each anomaly is classified by type (low_stock, delay, overdue, etc.) and severity
5. Exception records are stored in the exceptions table
6. Returns list of exceptions with id, type, severity, description, status

Update (Resolve):
1. User clicks "Resolve" on an exception card
2. Frontend sends:  PUT /api/v1/exceptions/{exception_id}/status?status=resolved
3. Exception Service updates the exception record's status field
4. Creates an ExceptionAction record logging who resolved it and when
5. Returns updated exception object
6. Frontend removes the exception from the open list
```

---

### Sequence 4 — Accessorial Charge Billing

```
1. Frontend loads:  GET /api/v1/dashboard/accessorial-charges
2. Dashboard Service queries dock_appointments WHERE duration > 2 hours
3. For each dock appointment, checks billing_line_items for existing charges
4. Returns list with status: "pending" or "billed" per charge

5. User clicks "Bill Now" for a pending charge
6. Frontend sends:  POST /api/v1/billing/process-accessorial-charge?charge_id=DOCK-DET-1
7. Billing Service queries dock appointment for detention details
8. Checks billing_line_items to confirm not already billed
9. Generates invoice number:  INV-{YYYYMMDDHHmmss}-{UUID6}
10. Inserts invoice record into invoices table (status: pending)
11. Inserts billing_line_item record (service_type: accessorial_charge)
12. Calls InvoicePDFGenerator to produce the PDF file
13. Saves PDF to /invoices/{invoice_id}.pdf
14. Returns: { invoice_number, download_url, status }
15. Frontend updates the charge card to show "Download Invoice" button
```

---

### Sequence 5 — Shipment Tracking View

```
1. Frontend calls:  GET /api/v1/tracking/shipments
2. Tracking Service queries TMS DB for shipments with status in_transit or out_for_delivery
3. For each shipment: retrieves current_location, ETA, carrier, route
4. Compares actual_delivery vs expected_delivery to flag delayed shipments
5. Returns shipment list with location and delay status

6. User clicks a shipment for detail
7. Frontend calls:  GET /api/v1/tracking/shipments/{shipment_id}
8. Tracking Service returns full detail:
   { origin, destination, current_location, carrier, progress_percent,
     expected_delivery, estimated_delivery, delay_hours, tracking_history }
9. Frontend renders detailed tracking card

Background update:
10. POST /api/v1/tracking/update-locations runs periodically
11. Tracking Service simulates location movement for in-transit shipments
12. Updates current_location field in TMS DB
```

---

## 3.2.4 — Data Transformation Pipeline

This pipeline describes how raw transaction records stored in the six databases are transformed into the KPI values displayed on the dashboard.

### Pipeline Stages

**Stage 1 — Raw Data Collection**

The Dashboard Service opens a database session for each of the six systems and runs SQL SELECT queries. All queries run at request time; there is no pre-computed cache or data warehouse.

Data collected per system:
- WMS: all inventory rows (quantity_on_hand, reorder_point, location), all picking_task rows
- OMS: all order rows (status, order_date, expected_delivery, actual_delivery)
- TMS: all shipment rows (status, carrier, expected_delivery, actual_delivery)
- Billing: all invoice rows (amount, status, invoice_date, paid_date)
- Returns: all return_order rows (status, created_at, completed_at, reason)
- Yard: all dock_appointment rows (scheduled_time, actual_time, duration, status)

---

**Stage 2 — KPI Calculation**

The raw records are processed into six KPI categories:

| KPI Category | Metrics Calculated | Source Systems |
|-------------|-------------------|---------------|
| **Service Levels** | On-time ship %, OTIF %, Backlog aging (avg days) | OMS, TMS |
| **Fulfillment Execution** | Order cycle time, Pick accuracy %, Rework rate | OMS, WMS |
| **Productivity & Staffing** | Units per hour, Pick/pack rate, Overtime % | WMS |
| **Inventory Health** | Inventory accuracy %, Cycle count variance, Stockout rate | WMS |
| **Dock & Carrier Flow** | Dock turn time, Detention hours, Appointment adherence % | Yard, TMS |
| **Returns & Billing Control** | Return rate %, Processing time, Missed charge % | Returns, Billing |

---

**Stage 3 — Exception Detection**

The Exception Service applies threshold rules to identify anomalies:

| Exception Type | Detection Rule | Source | Default Severity |
|----------------|---------------|--------|-----------------|
| Low Stock | `quantity_on_hand < reorder_point` | WMS | Warning |
| Delayed Order | `status = pending AND order_date < (today - 3 days)` | OMS | Warning |
| Delayed Shipment | `status = in_transit AND expected_delivery < now` | TMS | Critical |
| Overdue Invoice | `status = pending AND invoice_date < (today - 30 days)` | Billing | Critical |
| Pending Return | `status = pending AND created_at < (today - 14 days)` | Returns | Warning |
| Missed Appointment | `status = scheduled AND appointment_time < now` | Yard | Info |
| Billing Anomaly | Detected during invoice processing | Billing | Warning |

---

**Stage 4 — Audit Log Generation**

Every user action that modifies data is written to the `audit_logs` table in the Auth database. Each audit log entry records:
- `user_id` and `username` of the actor
- `action` type (e.g., `login`, `exception_resolved`, `charge_billed`)
- `ip_address` and `user_agent` of the request
- `success` flag and optional `error_message`
- `created_at` timestamp

The `AuditLogViewer` component in the frontend allows System Administrators to search and filter the full audit trail.

---

**Stage 5 — Role-Based Rendering**

Before sending data to the browser, the backend enforces permission checks at the endpoint level using the `check_permission()` function on the Auth Service. At the frontend level, the `permissions.js` utility reads the user's permission array and controls:
- Which sidebar menu items are visible
- Which action buttons appear on each card
- Which dashboard sections can be navigated to
- Whether data is filtered to a specific client_id

The customer_user role additionally has all dashboard data filtered to records matching their `client_id`, so they never see data belonging to other clients.
