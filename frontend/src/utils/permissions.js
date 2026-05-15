/**
 * Permission utility functions for role-based access control
 */

/**
 * Check if user has a specific permission
 * @param {Object} user - Current user object with permissions array
 * @param {string} permission - Permission name to check (e.g., 'exceptions.resolve')
 * @returns {boolean} - True if user has permission
 */
export const hasPermission = (user, permission) => {
  if (!user) return false;
  if (user.is_superuser) return true;
  
  const permissions = user.permissions || [];
  return permissions.includes(permission) || permissions.includes('*');
};

/**
 * Check if user has any of the specified permissions
 * @param {Object} user - Current user object
 * @param {Array<string>} permissionList - Array of permission names
 * @returns {boolean} - True if user has at least one permission
 */
export const hasAnyPermission = (user, permissionList) => {
  return permissionList.some(p => hasPermission(user, p));
};

/**
 * Check if user has all of the specified permissions
 * @param {Object} user - Current user object
 * @param {Array<string>} permissionList - Array of permission names
 * @returns {boolean} - True if user has all permissions
 */
export const hasAllPermissions = (user, permissionList) => {
  return permissionList.every(p => hasPermission(user, p));
};

/**
 * Check if user has a specific role
 * @param {Object} user - Current user object
 * @param {string} roleName - Role name to check
 * @returns {boolean} - True if user has the role
 */
export const hasRole = (user, roleName) => {
  if (!user) return false;
  const roles = user.roles || [];
  
  // Handle both string array and object array formats
  return roles.some(role => 
    typeof role === 'string' ? role === roleName : role.name === roleName
  );
};

/**
 * Get user's display name for role
 * @param {Object} user - Current user object
 * @returns {string} - Primary role display name
 */
export const getUserRoleDisplay = (user) => {
  if (!user) return 'Guest';
  if (user.is_superuser) return 'System Administrator';
  
  const roles = user.roles || [];
  if (roles.length === 0) return 'User';
  
  const firstRole = roles[0];
  return typeof firstRole === 'string' ? firstRole : firstRole.display_name || firstRole.name;
};

/**
 * Permission matrix for quick reference
 */
export const PERMISSIONS = {
  // Dashboard
  DASHBOARD_VIEW: 'dashboard.view',
  
  // WMS
  WMS_VIEW: 'wms.view',
  WMS_EDIT: 'wms.edit',
  WMS_INVENTORY_MANAGE: 'wms.inventory.manage',
  WMS_RECEIVING: 'wms.receiving',
  WMS_PICKING: 'wms.picking',
  
  // TMS
  TMS_VIEW: 'tms.view',
  TMS_EDIT: 'tms.edit',
  TMS_CREATE: 'tms.create',
  TMS_CARRIER_MANAGE: 'tms.carrier.manage',
  
  // OMS
  OMS_VIEW: 'oms.view',
  OMS_EDIT: 'oms.edit',
  OMS_CREATE: 'oms.create',
  OMS_CANCEL: 'oms.cancel',
  
  // Billing
  BILLING_VIEW: 'billing.view',
  BILLING_EDIT: 'billing.edit',
  BILLING_APPROVE: 'billing.approve',
  BILLING_EXPORT: 'billing.export',
  
  // Returns
  RETURNS_VIEW: 'returns.view',
  RETURNS_PROCESS: 'returns.process',
  RETURNS_APPROVE: 'returns.approve',
  
  // Yard
  YARD_VIEW: 'yard.view',
  YARD_MANAGE: 'yard.manage',
  
  // Exceptions
  EXCEPTIONS_VIEW: 'exceptions.view',
  EXCEPTIONS_ASSIGN: 'exceptions.assign',
  EXCEPTIONS_RESOLVE: 'exceptions.resolve',
  EXCEPTIONS_ESCALATE: 'exceptions.escalate',
  
  // Reports
  REPORTS_VIEW: 'reports.view',
  REPORTS_GENERATE: 'reports.generate',
  REPORTS_SCHEDULE: 'reports.schedule',
  REPORTS_EXPORT: 'reports.export',
  
  // Analytics
  ANALYTICS_VIEW: 'analytics.view',
  ANALYTICS_ADVANCED: 'analytics.advanced',
  
  // Admin
  ADMIN_USERS: 'admin.users',
  ADMIN_ROLES: 'admin.roles',
  ADMIN_SYSTEM: 'admin.system',
  ADMIN_LOGS: 'admin.logs',
};

/**
 * Role-based access examples for documentation
 */
export const ROLE_EXAMPLES = {
  system_admin: {
    name: 'System Administrator',
    description: 'Full system access',
    canAccess: ['Everything']
  },
  operations_manager: {
    name: 'Operations Manager',
    description: 'Manage all operations',
    canAccess: ['All dashboards', 'Exceptions (assign, resolve, escalate)', 'WMS, TMS, OMS (view, edit)', 'Reports (view, generate)']
  },
  warehouse_manager: {
    name: 'Warehouse Manager',
    description: 'Warehouse operations',
    canAccess: ['WMS (full access)', 'Yard management', 'Inventory', 'Exceptions (view, resolve)']
  },
  transportation_manager: {
    name: 'Transportation Manager',
    description: 'Transportation operations',
    canAccess: ['TMS (full access)', 'Carrier management', 'Shipment tracking', 'Exceptions (view, resolve)']
  },
  billing_manager: {
    name: 'Billing Manager',
    description: 'Financial operations',
    canAccess: ['Billing (full access)', 'Invoice approval', 'Revenue intelligence', 'Financial reports']
  },
  customer_service: {
    name: 'Customer Service',
    description: 'Customer support',
    canAccess: ['View orders, shipments, returns', 'Exception assignment', 'Basic reports']
  },
  dock_supervisor: {
    name: 'Dock Supervisor',
    description: 'Dock operations',
    canAccess: ['Yard management', 'Receiving/Shipping', 'WMS view access']
  },
  returns_manager: {
    name: 'Returns Manager',
    description: 'Returns processing',
    canAccess: ['Returns (full access)', 'Exception handling', 'OMS view access']
  },
  analyst: {
    name: 'Business Analyst',
    description: 'Analytics and reporting',
    canAccess: ['All dashboards (read-only)', 'Reports (view, generate, export)', 'Advanced analytics']
  },
  client_user: {
    name: 'Client User',
    description: 'Client portal access',
    canAccess: ['Own company data only', 'View orders, shipments, billing']
  }
};
