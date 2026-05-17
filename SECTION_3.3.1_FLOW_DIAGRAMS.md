# Section 3.3.1 — Flow Diagrams

## Project: E-commerce Fulfillment Operations Control Tower

---

## Overview

This section contains detailed step-by-step process flows for the five core operational workflows of the system. Each flow is described in structured text with enough detail for a developer or diagram tool to generate an accurate flowchart.

The five flows covered are:
1. User Authentication and Login
2. Accessorial Charge Billing ("Bill Now")
3. Exception Detection and Management
4. Real-Time Shipment Tracking
5. Order Journey — End-to-End View

---

## Flow 1 — User Authentication and Login

### Summary

A user visits the frontend, enters credentials, and the system validates them. On success, tokens are returned and the user is shown a role-specific dashboard. On failure, an error is displayed.

### Actors
- User (any role)
- Frontend (React Login component)
- Backend (FastAPI auth endpoint)
- Auth Service (`auth_service.py`)
- Auth Database (`auth.db`)

---

### Step-by-Step Flow

```
START
  │
  ▼
User opens browser and navigates to http://localhost:3000
  │
  ▼
React App checks localStorage for an existing access_token
  │
  ├── Token found and valid  ─────────────────────────────────► Skip login, load dashboard
  │
  └── No token or expired  ───────────────────────────────────► Render Login.jsx component
        │
        ▼
User enters username and password in the login form
  │
  ▼
User clicks "Login" button
  │
  ▼
Frontend sends:  POST /api/v1/auth/login
Body: username and password as form-encoded fields
  │
  ▼
FastAPI routes request to the login endpoint in main.py
  │
  ▼
Auth Service calls authenticate(username, password, ip_address, user_agent)
  │
  ▼
Auth Service queries the users table WHERE username = input AND is_active = true
  │
  ├── User not found  ──────────────────────────────────────────► Log audit entry (login_failed)
  │                                                                Return HTTP 401 Unauthorized
  │                                                                Frontend shows "Invalid credentials" error
  │                                                                FLOW ENDS (failure)
  │
  └── User found
        │
        ▼
Auth Service calls verify_password(input_password, stored_hash)
Hashing algorithm: SHA-256 via hashlib
  │
  ├── Password incorrect  ────────────────────────────────────── ► Log audit entry (login_failed)
  │                                                                Return HTTP 401 Unauthorized
  │                                                                Frontend shows "Invalid credentials" error
  │                                                                FLOW ENDS (failure)
  │
  └── Password correct
        │
        ▼
Auth Service creates a UserSession record:
  - token: secrets.token_hex(32) (access token)
  - refresh_token: secrets.token_hex(32)
  - expires_at: now + 8 hours
  - ip_address: client IP
  - user_agent: browser string
  │
  ▼
Auth Service writes audit log entry:
  - action: "login"
  - user_id, username, ip_address, success: true
  │
  ▼
Auth Service updates user.last_login = now
  │
  ▼
Auth Service returns to FastAPI:
  {
    user: { id, username, email, full_name, roles[], permissions[], client_id },
    token: <access_token>,
    refresh_token: <refresh_token>,
    expires_at: <ISO timestamp>
  }
  │
  ▼
Frontend receives success response
  │
  ▼
Frontend stores in localStorage:
  - access_token
  - refresh_token
  - user object (JSON)
  │
  ▼
Frontend sets isAuthenticated = true in React state
  │
  ▼
Frontend reads user.roles and user.permissions
  │
  ▼
Frontend renders Sidebar with role-appropriate navigation items
  │
  ▼
Frontend loads default dashboard view (KPI Dashboard)

END (success)
```

---

### Decision Points Summary

| Decision | Yes Path | No Path |
|----------|----------|---------|
| Existing valid token in localStorage? | Skip to dashboard | Show login form |
| User exists in database? | Continue to password check | Return 401 |
| Password hash matches? | Create session, return tokens | Return 401 |
| Login response successful? | Store tokens, load dashboard | Show error message |

---

## Flow 2 — Accessorial Charge Billing ("Bill Now")

### Summary

An operations manager views the accessorial charges list on the dashboard. For each pending dock detention charge, they can click "Bill Now" to generate an invoice and PDF. The system ensures no duplicate billing.

### Actors
- Operations Manager (user)
- Frontend (AccessorialCharges.jsx)
- Backend (FastAPI billing endpoint)
- Billing Service (`billing_service.py`)
- Dashboard Service (`dashboard_service.py`)
- Billing Database (`billing.db`)
- Yard Database (`yard.db`)
- TMS Database (`tms.db`)
- Invoice PDF Storage (`/invoices/`)

---

### Step-by-Step Flow

```
START
  │
  ▼
User navigates to the Accessorial Charges view
  │
  ▼
Frontend sends:  GET /api/v1/dashboard/accessorial-charges
Header: Authorization: Bearer <access_token>
  │
  ▼
Dashboard Service calls get_accessorial_charges()
  │
  ▼
Dashboard Service queries yard.db:
  SELECT dock_appointments WHERE duration_hours > 2.0
  (These are dock detention charges)
  │
  ▼
For each dock appointment, Dashboard Service queries billing.db:
  SELECT billing_line_items WHERE service_type = 'accessorial_charge'
  AND charge_id = appointment.id
  │
  ├── Record found in billing_line_items  ──────────────────────► Mark charge status: "billed"
  │                                                                Attach: invoice_number, download_url
  │
  └── No record found  ─────────────────────────────────────────► Mark charge status: "pending"
  │
  ▼
Dashboard Service returns list of charges with status and invoice data
  │
  ▼
Frontend renders AccessorialCharges component
  - Charges with status "pending" show a "Bill Now" button
  - Charges with status "billed" show a "Download Invoice" button
  │
  ▼
User clicks "Bill Now" on a pending charge (e.g., charge_id = DOCK-DET-1)
  │
  ▼
Frontend sends:  POST /api/v1/billing/process-accessorial-charge?charge_id=DOCK-DET-1
  │
  ▼
FastAPI routes to process_accessorial_charge(charge_id) in billing_service.py
  │
  ▼
Billing Service queries yard.db for the dock appointment:
  Fields retrieved: dock_id, scheduled_time, actual_duration, detention_hours, rate
  │
  ▼
Billing Service queries tms.db for a related shipment:
  Attempts to find shipment_id by matching dock appointment
  Falls back to using charge_id as the order reference if no shipment found
  │
  ▼
Billing Service queries billing.db to check for duplicate:
  SELECT FROM billing_line_items WHERE service_type = 'accessorial_charge'
  AND charge_id = 'DOCK-DET-1'
  │
  ├── Duplicate found  ─────────────────────────────────────────► Return HTTP 400
  │                                                                Message: "Charge already billed"
  │                                                                Frontend shows error
  │                                                                FLOW ENDS (blocked)
  │
  └── No duplicate — proceed with billing
        │
        ▼
Billing Service generates invoice number:
  Format: INV-{YYYYMMDDHHmmss}-{6-char UUID hex}
  Example: INV-20260516145503-A3F8D2
  (This format prevents collisions even if server restarts)
        │
        ▼
Billing Service inserts invoice record into billing.db:
  Fields: invoice_id, order_id (shipment_id or charge_id), customer_id,
          service_type, amount, status: "pending", created_at: now
        │
        ▼
Billing Service inserts billing_line_item record into billing.db:
  Fields: invoice_id (linked), service_type: "accessorial_charge",
          charge_id: "DOCK-DET-1", description: "Dock Detention Charge",
          quantity: detention_hours, unit_rate, total_amount
        │
        ▼
Billing Service calls InvoicePDFGenerator.generate(invoice_data)
  Library: ReportLab
  Output: PDF file containing invoice details
        │
        ▼
PDF saved to file path:  backend/invoices/{invoice_id}.pdf
        │
        ▼
Billing Service returns to FastAPI:
  {
    invoice_id: "INV-20260516145503-A3F8D2",
    invoice_number: "INV-20260516145503-A3F8D2",
    status: "pending",
    amount: <calculated amount>,
    download_url: "/invoices/INV-20260516145503-A3F8D2.pdf"
  }
  │
  ▼
Frontend receives success response
  │
  ▼
Frontend updates the charge card:
  - Removes "Bill Now" button
  - Shows "Download Invoice" button with PDF link
  - Saves billed status to localStorage key: "accessorialBillingStatus"
  │
  ▼
User clicks "Download Invoice"
  │
  ▼
Browser requests:  GET /invoices/INV-20260516145503-A3F8D2.pdf
FastAPI StaticFiles serves the PDF file directly
  │
  ▼
PDF opens or downloads in the browser

END (success)
```

---

### Decision Points Summary

| Decision | Yes Path | No Path |
|----------|----------|---------|
| Existing token valid? | Continue to billing request | Return 401, redirect to login |
| Charge already billed? | Return 400 (blocked) | Continue to generate invoice |
| Shipment found in TMS? | Use shipment_id as order reference | Use charge_id as fallback |
| PDF file saved successfully? | Return invoice details | Return HTTP 500 |

---

## Flow 3 — Exception Detection and Management

### Summary

The system detects anomalies across all six enterprise systems. Each anomaly is stored as an exception record. Users can assign, resolve, dismiss, or add notes to exceptions. All state changes are logged.

### Actors
- Any authenticated user (different permissions for different actions)
- Frontend (ExceptionCenter.jsx)
- Backend (exception endpoints in main.py)
- Exception Service (`exception_service.py`)
- All six system databases

---

### Step-by-Step Flow — Detection

```
START (Detection)
  │
  ▼
User navigates to Exception Center
  │
  ▼
Frontend sends:  GET /api/v1/dashboard/exceptions
  │
  ▼
Dashboard Service triggers exception detection
  │
  ▼
Exception Service runs detection queries in parallel against all 6 databases:
  │
  ├── WMS Database:
  │     Query: SELECT * FROM inventory WHERE quantity_on_hand < reorder_point
  │     Each result  ──────────────────────────────────────────► Exception type: "low_stock"
  │                                                               Severity: warning
  │
  ├── OMS Database:
  │     Query: SELECT * FROM orders WHERE status = 'pending' AND order_date < (today - 3 days)
  │     Each result  ──────────────────────────────────────────► Exception type: "delayed_order"
  │                                                               Severity: warning
  │
  ├── TMS Database:
  │     Query: SELECT * FROM shipments WHERE status = 'in_transit' AND expected_delivery < now
  │     Each result  ──────────────────────────────────────────► Exception type: "delayed_shipment"
  │                                                               Severity: critical
  │
  ├── Billing Database:
  │     Query: SELECT * FROM invoices WHERE status = 'pending' AND invoice_date < (today - 30 days)
  │     Each result  ──────────────────────────────────────────► Exception type: "overdue_invoice"
  │                                                               Severity: critical
  │
  ├── Returns Database:
  │     Query: SELECT * FROM return_orders WHERE status = 'pending' AND created_at < (today - 14 days)
  │     Each result  ──────────────────────────────────────────► Exception type: "pending_return"
  │                                                               Severity: warning
  │
  └── Yard Database:
        Query: SELECT * FROM dock_appointments WHERE status = 'scheduled' AND appointment_time < now
        Each result  ──────────────────────────────────────────► Exception type: "missed_appointment"
                                                                  Severity: info
  │
  ▼
Exception Service creates exception records in the exceptions table:
  Fields: exception_id, system (wms/oms/tms/billing/returns/yard),
          exception_type, severity, description, reference_id,
          status: "open", created_at: now, assigned_to: null
  │
  ▼
Exception Service returns all exception records (including previously created ones)
  │
  ▼
Frontend receives exception list
  │
  ▼
Frontend renders ExceptionCenter:
  - Cards grouped by severity (critical first)
  - Each card shows: type, description, system, reference ID, age
  - Action buttons shown based on user permissions

END (Detection)
```

---

### Step-by-Step Flow — Exception Actions

```
START (User takes action on an exception)
  │
  ▼
─── ACTION: Assign ───────────────────────────────────────────────────────────────
  User clicks "Assign" button on an exception card
  User selects an assignee from the dropdown
  Frontend sends:  PUT /api/v1/exceptions/{exception_id}/assign?assigned_to=username
  Exception Service updates exception record: assigned_to = username
  Exception Service inserts ExceptionAction record:
    action_type: "assigned", performed_by: current_user, timestamp: now
  Frontend updates card to show assigned user name

─── ACTION: Update Status (Resolve / Dismiss / Start Work) ───────────────────────
  User clicks "Resolve" or "Dismiss"
  Frontend sends:  PUT /api/v1/exceptions/{exception_id}/status?status=resolved
  Exception Service updates exception record: status = "resolved", resolved_at = now
  Exception Service inserts ExceptionAction record:
    action_type: "status_changed", new_status: "resolved",
    performed_by: current_user, timestamp: now
  Frontend removes the exception from the open list

─── ACTION: Add Note ─────────────────────────────────────────────────────────────
  User types a note and clicks "Add Note"
  Frontend sends:  POST /api/v1/exceptions/{exception_id}/notes?user=username&note=text
  Exception Service inserts ExceptionAction record:
    action_type: "note_added", note_text: user_input,
    performed_by: current_user, timestamp: now
  Frontend appends the note to the exception's history section

END (Action)
```

---

### Decision Points Summary

| Decision | Yes Path | No Path |
|----------|----------|---------|
| Anomaly found in WMS? | Create low_stock exception | Skip |
| Anomaly found in TMS? | Create delayed_shipment exception | Skip |
| Anomaly found in Billing? | Create overdue_invoice exception | Skip |
| User has exceptions.resolve permission? | Show Resolve button | Hide button |
| User has exceptions.assign permission? | Show Assign button | Hide button |

---

## Flow 4 — Real-Time Shipment Tracking

### Summary

Users view a list of in-transit shipments with their current locations. Selecting a shipment shows detailed tracking with route history. The system simulates location updates periodically.

### Actors
- Any user with tracking access
- Frontend (ShipmentTracking.jsx)
- Backend (tracking endpoints in main.py)
- Tracking Service (`tracking_service.py`)
- TMS Database (`tms.db`)

---

### Step-by-Step Flow

```
START
  │
  ▼
User navigates to Shipment Tracking view
  │
  ▼
Frontend sends:  GET /api/v1/tracking/shipments
  │
  ▼
Tracking Service queries TMS Database:
  SELECT * FROM shipments
  WHERE status IN ('in_transit', 'out_for_delivery')
  (Optional: filtered by status query parameter if provided)
  │
  ▼
For each shipment, Tracking Service retrieves:
  - shipment_id, carrier, tracking_number
  - origin city, destination city
  - current_location (from tracking_data table)
  - expected_delivery date
  - last_update timestamp
  │
  ▼
Tracking Service calculates for each shipment:
  - progress_percent: estimated % of route completed based on location
  - is_delayed: actual location vs expected schedule
  - delay_hours: how many hours behind schedule (if delayed)
  │
  ▼
Tracking Service returns shipment list
  │
  ▼
Frontend renders ShipmentTracking component:
  - Summary statistics card at top:
      Total tracked shipments, In transit count, Delayed count, Delivered today
  - One card per shipment showing:
      Carrier logo, route (Origin → Destination), current location,
      status badge, ETA, delay flag (if applicable)
  │
  ▼
User clicks on a specific shipment card
  │
  ▼
Frontend sends:  GET /api/v1/tracking/shipments/{shipment_id}
  │
  ▼
Tracking Service queries TMS Database for full shipment detail:
  Joins shipments table with tracking_data table for history
  │
  ▼
Tracking Service returns detailed object:
  {
    shipment_id, carrier, tracking_number,
    origin, destination, current_location,
    status, progress_percent, delay_hours,
    expected_delivery, estimated_delivery,
    last_update,
    tracking_history: [
      { timestamp, location, status, note },
      { timestamp, location, status, note },
      ...
    ]
  }
  │
  ▼
Frontend renders detailed view:
  - Full route with location history timeline
  - Progress bar showing % complete
  - Each tracking event listed with timestamp and location
  │
  ▼
  ─── Background Location Update (periodic simulation) ───────────────────────
  POST /api/v1/tracking/update-locations is called (by admin or scheduler)
  Tracking Service iterates over all in_transit shipments
  For each shipment:
    - Moves current_location forward along the simulated route
    - Updates last_update timestamp in tracking_data table
    - If shipment has reached destination: sets status = "delivered", actual_delivery = now
  Returns count of updated shipments
  Frontend re-fetches shipments on next user action or manual refresh

END
```

---

### Decision Points Summary

| Decision | Yes Path | No Path |
|----------|----------|---------|
| Shipment status = in_transit or out_for_delivery? | Include in tracking list | Exclude |
| actual_delivery > expected_delivery? | Mark as delayed | Mark as on-time |
| Shipment reached destination in update? | Set status = delivered | Continue tracking |
| User has tracking permission? | Show tracking view | Hide from sidebar |

---

## Flow 5 — Order Journey (End-to-End View)

### Summary

A user selects an order and views a complete chronological timeline of all events from order placement through delivery, spanning multiple enterprise systems. The system joins data from OMS, WMS, TMS, Billing, and Returns to build the timeline.

### Actors
- User (Operations Manager, System Admin, Customer User)
- Frontend (OrderJourney.jsx)
- Backend (journey endpoints in main.py)
- Journey Service (`journey_service.py`)
- OMS Database, WMS Database, TMS Database, Billing Database, Returns Database

---

### Step-by-Step Flow

```
START
  │
  ▼
User navigates to Order Journey view
  │
  ▼
Frontend sends:  GET /api/v1/journey/orders
  (Optional: ?status=shipped filter)
  │
  ▼
Journey Service queries OMS Database:
  SELECT * FROM orders
  (Filtered by status if provided; filtered by client_id for customer_user role)
  │
  ▼
Journey Service returns summary list:
  - order_id, customer_name, order_date, status, total_amount
  │
  ▼
Frontend renders order list (one row per order)
  │
  ▼
User clicks on an order row
  │
  ▼
Frontend sends:  GET /api/v1/journey/orders/{order_id}
  │
  ▼
Journey Service begins multi-system data collection for this order:
  │
  ├── Step A — OMS Database
  │     Query: SELECT orders WHERE order_id = input
  │     Retrieves: customer_id, order_date, status, expected_delivery,
  │                actual_delivery, total_amount, notes
  │
  ├── Step B — OMS Database (line items)
  │     Query: SELECT order_items WHERE order_id = input
  │     Retrieves: sku, quantity, unit_price for each line item
  │
  ├── Step C — WMS Database (fulfillment)
  │     Query: SELECT picking_tasks WHERE order_id = input
  │     Retrieves: task_id, pick_status, started_at, completed_at, picker_name
  │
  ├── Step D — TMS Database (shipment)
  │     Query: SELECT shipments WHERE order_id = input
  │     Retrieves: shipment_id, carrier, tracking_number, status,
  │                current_location, expected_delivery, actual_delivery
  │
  ├── Step E — Billing Database (invoice)
  │     Query: SELECT invoices WHERE order_id = input
  │     Retrieves: invoice_id, invoice_number, amount, status, invoice_date, paid_date
  │
  └── Step F — Returns Database (if applicable)
        Query: SELECT return_orders WHERE original_order_id = input
        Retrieves: return_id, reason, status, created_at, completed_at
  │
  ▼
Journey Service constructs chronological timeline:
  Event 1:  Order Received        — order_date from OMS
  Event 2:  Payment Confirmed     — invoice_date from Billing
  Event 3:  Picking Started       — earliest picking_task.started_at from WMS
  Event 4:  Picking Completed     — latest picking_task.completed_at from WMS
  Event 5:  Shipment Created      — shipment created_at from TMS
  Event 6:  In Transit            — status change timestamp from TMS
  Event 7:  Out for Delivery      — status change timestamp from TMS (if available)
  Event 8:  Delivered             — actual_delivery from TMS
  Event 9:  Return Initiated      — return created_at from Returns (if return exists)
  Event 10: Return Completed      — return completed_at from Returns (if return exists)
  │
  ▼
Journey Service calculates metrics:
  - Order-to-Ship Time:  days between order_date and shipment created_at
  - In-Transit Time:     days between shipment created_at and actual_delivery
  - Total Cycle Time:    days between order_date and actual_delivery (or today if pending)
  - On-Time:             actual_delivery <= expected_delivery  →  true/false
  │
  ▼
Journey Service returns complete journey object:
  {
    order_id, customer_name, status,
    order_items: [ { sku, quantity, price } ],
    shipment: { carrier, tracking_number, current_location, status },
    invoice: { invoice_number, amount, payment_status },
    return: { return_id, reason, status } or null,
    timeline: [
      { event_name, timestamp, status, description, system_source }
    ],
    metrics: { order_to_ship_days, in_transit_days, total_cycle_days, is_on_time }
  }
  │
  ▼
Frontend renders OrderJourney component:
  - Header card: order ID, customer name, status badge, total amount
  - Order items table: SKU, quantity, price per line
  - Vertical timeline:
      Each milestone shown as a dot on a vertical line
      Completed milestones: colored (green/blue)
      Pending milestones: grey
      Each dot shows event name, timestamp, and description
  - Metrics bar: order-to-ship, in-transit, total cycle time, on-time flag
  - Shipment tracking snippet: carrier, current location, ETA
  - Invoice section: invoice number, amount, payment status
  - Returns section (only shown if a return exists): reason, status, timeline

END
```

---

### Decision Points Summary

| Decision | Yes Path | No Path |
|----------|----------|---------|
| User role is customer_user? | Filter orders by client_id | Return all orders |
| Picking tasks found in WMS? | Add picking milestones to timeline | Skip picking milestones |
| Shipment found in TMS? | Add shipment milestones | Show "Not yet shipped" |
| Invoice found in Billing? | Add invoice section | Skip invoice section |
| Return found in Returns? | Add return milestones and section | Skip return section |
| actual_delivery <= expected_delivery? | Mark as On-Time | Mark as Delayed |

---

## Summary Table — All Flows

| Flow | Trigger | Systems Involved | Key Output |
|------|---------|-----------------|-----------|
| **F1: Authentication** | User submits login form | Auth DB | JWT access token + user session |
| **F2: Billing** | User clicks "Bill Now" | Yard DB, TMS DB, Billing DB | Invoice record + PDF file |
| **F3: Exception Detection** | User opens Exception Center | All 6 databases | Exception records with severity |
| **F4: Tracking** | User opens Shipment Tracking | TMS DB | Shipment locations + ETA |
| **F5: Order Journey** | User selects an order | OMS, WMS, TMS, Billing, Returns | End-to-end timeline |
