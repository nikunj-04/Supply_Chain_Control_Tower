# Role-Based Access Control (RBAC) - UI Permissions

## Role Overview

### 🔑 System Administrator (`system_admin`)
**Full System Access**
- All menus visible
- All actions enabled
- Can manage users and roles

**UI Access:**
- ✅ All Dashboards
- ✅ All Control Tower features
- ✅ All Revenue Intelligence
- ✅ All Operations features
- ✅ All Reports (view, generate, schedule, export)
- ✅ User & Role Management

---

### 👔 Operations Manager (`operations_manager`)
**Comprehensive Operational Control**

**UI Access:**
- ✅ Dashboards (KPI, Scorecard)
- ✅ Exception Management
  - Can view, assign, resolve, and escalate
- ✅ Real-Time Tracking
- ✅ Order Journey View
- ✅ Warehouse Performance
- ✅ Carrier Scorecards
- ✅ Labor Efficiency
- ✅ Inventory Optimization
- ✅ Reports (view, generate, export)
- ❌ Billing approval
- ❌ User management

**Action Buttons:**
- Exception Center: Assign, Start Work, Resolve, Escalate buttons visible
- Reports: Generate and Export enabled

---

### 📦 Warehouse Manager (`warehouse_manager`)
**Warehouse & Inventory Focus**

**UI Access:**
- ✅ Dashboards
- ✅ Exception Management (view, resolve only)
- ✅ Warehouse Performance
- ✅ Inventory Optimization
- ✅ Labor Efficiency
- ✅ Yard Management (full access)
- ✅ Reports (view, generate)
- ❌ Revenue Intelligence
- ❌ Carrier Scorecards
- ❌ Billing features

**Action Buttons:**
- Exception Center: Start Work, Resolve buttons only
- No Assign or Escalate buttons
- No billing approval buttons

---

### 🚛 Transportation Manager (`transportation_manager`)
**Transportation & Carrier Focus**

**UI Access:**
- ✅ Dashboards
- ✅ Real-Time Tracking
- ✅ Order Journey View
- ✅ Exception Management (view, resolve)
- ✅ Carrier Scorecards
- ✅ Reports (view, generate)
- ❌ Warehouse features
- ❌ Billing approval
- ❌ Revenue Intelligence

---

### 💰 Billing Manager (`billing_manager`)
**Financial & Revenue Focus**

**UI Access:**
- ✅ Dashboards
- ✅ Revenue Intelligence (full section)
  - Accessorial Charges
  - Client Profitability
  - Billing Analytics
- ✅ Reports (view, generate, export)
- ✅ Invoice Approval (when feature added)
- ❌ Operations deep dive
- ❌ Exception resolution
- ❌ Warehouse/Transportation management

**Special Actions:**
- Can approve invoices
- Can export financial data
- View-only for orders and shipments

---

### 👥 Customer Service Rep (`customer_service`)
**Limited Support Access**

**UI Access:**
- ✅ Dashboards (view only)
- ✅ Exception Management
  - Can view and assign only
  - ❌ Cannot resolve or escalate
- ✅ Real-Time Tracking (view)
- ✅ Order Journey View (view)
- ✅ Reports (view only)
- ❌ All edit functions
- ❌ Operations management
- ❌ Billing

**Action Buttons:**
- Exception Center: View and Assign buttons only
- No resolution or status change buttons
- Read-only access to most data

---

### 🚪 Dock Supervisor (`dock_supervisor`)
**Dock & Yard Operations**

**UI Access:**
- ✅ Dashboards
- ✅ Yard Management (full access)
- ✅ Warehouse Performance (limited)
- ✅ Real-Time Tracking (view)
- ❌ Exception resolution
- ❌ Revenue Intelligence
- ❌ Reports generation

---

### 🔄 Returns Manager (`returns_manager`)
**Returns Processing**

**UI Access:**
- ✅ Dashboards
- ✅ Returns Management (full access - when added)
- ✅ Exception Management (returns-related)
- ✅ Order View (read-only)
- ❌ Transportation management
- ❌ Billing
- ❌ Warehouse operations

---

### 📊 Business Analyst (`analyst`)
**Analytics & Reporting Focus**

**UI Access:**
- ✅ All Dashboards (read-only)
- ✅ All Reports
  - Can view, generate, and export
  - Can create custom reports
- ✅ Advanced Analytics
- ✅ Exception View (read-only)
- ❌ No edit or action buttons
- ❌ No operational changes

**Special Features:**
- Advanced analytics access
- Custom report builder
- Scheduled exports
- All view permissions, no action permissions

---

### 🏢 Client User (`client_user`)
**Limited Client Portal**

**UI Access:**
- ✅ Dashboards (own data only)
- ✅ Order Tracking (own orders only)
- ✅ Shipment Tracking (own shipments only)
- ✅ Billing View (own invoices only)
- ✅ Returns View (own returns only)
- ✅ Basic Reports (own data)
- ❌ All internal operations
- ❌ Other clients' data
- ❌ Any edit functions

**Data Filtering:**
- All queries automatically filtered by `client_id`
- Cannot see other clients' information

---

## Permission Matrix

| Feature | Admin | Ops Mgr | Warehouse | Transport | Billing | CS Rep | Dock | Returns | Analyst | Client |
|---------|-------|---------|-----------|-----------|---------|--------|------|---------|---------|--------|
| **Dashboards** |
| View KPIs | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| View Scorecard | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Exceptions** |
| View | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ |
| Assign | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Resolve | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ |
| Escalate | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Warehouse** |
| View | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Edit | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ |
| Inventory Manage | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Transportation** |
| View | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | ✅ |
| Edit | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Carrier Manage | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Billing** |
| View | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ |
| Edit | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| Approve | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **Reports** |
| View | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ |
| Generate | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| Schedule | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| Export | ✅ | ✅ | ❌ | ❌ | ✅ | ❌ | ❌ | ❌ | ✅ | ❌ |

---

## Testing Different Roles

Use these demo accounts to test role-based access:

1. **System Admin**: `admin` / `admin123`
   - See everything, do everything

2. **Operations Manager**: `ops_manager` / `ops123`
   - Full operational control
   - No billing or admin features

3. **Customer Service**: `cs_rep` / `cs123`
   - Limited to viewing and assigning
   - Cannot resolve or edit

---

## How It Works

### Frontend (UI)
- **Sidebar filtering**: Menu items are hidden if user lacks permission
- **Button visibility**: Action buttons conditional on permissions
- **Component access**: Permission checks before rendering features

### Backend (API)
- **Token authentication**: JWT tokens with user info
- **Permission validation**: Each endpoint can check permissions
- **Audit logging**: All actions tracked with user info

### Permission Check Example
```javascript
import { hasPermission, PERMISSIONS } from '../utils/permissions';

// In component
const canResolve = hasPermission(currentUser, PERMISSIONS.EXCEPTIONS_RESOLVE);

// In render
{canResolve && (
  <button onClick={handleResolve}>Resolve</button>
)}
```

---

## Adding New Permissions

To add a new permission:

1. **Backend**: Add to `scripts/seed_auth_data.py`
2. **Frontend**: Add to `utils/permissions.js` PERMISSIONS object
3. **UI**: Use `hasPermission()` to check in components
4. **Sidebar**: Add `requiredPermissions` array to menu items
