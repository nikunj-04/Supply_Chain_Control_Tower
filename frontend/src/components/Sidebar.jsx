import React, { useState } from 'react';
import './Sidebar.css';

function Sidebar({ activeView, setActiveView, currentUser }) {
  const [expandedSection, setExpandedSection] = useState('dashboards');

  const toggleSection = (section) => {
    setExpandedSection(expandedSection === section ? null : section);
  };

  // Check if user has permission
  const hasPermission = (permission) => {
    if (!currentUser) return false;
    if (currentUser.is_superuser) return true;
    const permissions = currentUser.permissions || [];
    return permissions.includes(permission) || permissions.includes('*');
  };

  // Check if user has any of the permissions
  const hasAnyPermission = (permissionList) => {
    return permissionList.some(p => hasPermission(p));
  };

  const menuItems = [
    {
      id: 'dashboards',
      icon: '📊',
      label: 'Dashboards',
      requiredPermissions: ['dashboard.view'],
      items: [
        { id: 'kpis', label: 'KPI Dashboard', requiredPermissions: ['dashboard.view'] },
        { id: 'scorecard', label: 'Operational Scorecard', requiredPermissions: ['dashboard.view'] },
      ]
    },
    {
      id: 'control-tower',
      icon: '🚨',
      label: 'Control Tower',
      badge: 'v3.0',
      requiredPermissions: ['exceptions.view', 'tms.view', 'oms.view'],
      items: [
        { id: 'exception-center', label: 'Exception Management', requiredPermissions: ['exceptions.view'] },
        // { id: 'shipment-tracking', label: 'Real-Time Tracking', requiredPermissions: ['tms.view'] },
        { id: 'order-journey', label: 'Order Journey View', requiredPermissions: ['oms.view'] },
      ]
    },
    {
      id: 'revenue',
      icon: '💰',
      label: 'Revenue Intelligence',
      requiredPermissions: ['billing.view', 'analytics.view'],
      items: [
        { id: 'accessorial-charges', label: 'Accessorial Charges Recovery', requiredPermissions: ['billing.view'] },
        { id: 'client-profitability', label: 'Client Profitability', requiredPermissions: ['billing.view', 'analytics.view'] },
        { id: 'billing-analytics', label: 'Billing Analytics', requiredPermissions: ['billing.view'] },
      ]
    },
    {
      id: 'operations',
      icon: '📦',
      label: 'Operations Deep Dive',
      requiredPermissions: ['wms.view', 'tms.view', 'analytics.view'],
      items: [
        { id: 'warehouse-performance', label: 'Warehouse Performance', requiredPermissions: ['wms.view'] },
        { id: 'carrier-scorecards', label: 'Carrier Scorecards', requiredPermissions: ['tms.view'] },
        // { id: 'labor-efficiency', label: 'Labor Efficiency', requiredPermissions: ['wms.view', 'analytics.view'] },
        { id: 'inventory-optimization', label: 'Inventory Optimization', requiredPermissions: ['wms.view', 'analytics.view'] },
      ]
    },
    /*
    {
      id: 'reports',
      icon: '📄',
      label: 'Reports',
      requiredPermissions: ['reports.view'],
      items: [
        { id: 'standard-reports', label: 'Standard Reports', requiredPermissions: ['reports.view'] },
        { id: 'custom-reports', label: 'Custom Report Builder', requiredPermissions: ['reports.generate'] },
        { id: 'scheduled-exports', label: 'Scheduled Exports', requiredPermissions: ['reports.schedule'] },
      ]
    },
    */
    {
      id: 'admin',
      icon: '⚙️',
      label: 'Administration',
      requiredPermissions: ['admin.users', 'admin.roles', 'admin.logs'],
      items: [
        { id: 'user-management', label: 'User Management', requiredPermissions: ['admin.users'] },
        { id: 'audit-logs', label: 'Audit Logs', requiredPermissions: ['admin.logs'] },
      ]
    },
  ];

  // Filter menu items based on permissions
  const filterMenuItems = (items) => {
    return items
      .map(section => {
        // Filter items within the section
        const filteredItems = section.items.filter(item => 
          hasAnyPermission(item.requiredPermissions) //should be hasPermission according to me but we want to show items if user has any of the required permissions
        );
        
        // Only include section if user has permission and has visible items
        if (filteredItems.length > 0 && hasAnyPermission(section.requiredPermissions)) {
          return { ...section, items: filteredItems };
        }
        return null;
      })
      .filter(Boolean); // Remove null entries
  };

  const visibleMenuItems = filterMenuItems(menuItems);

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <h2 className="sidebar-title">Navigation</h2>
      </div>
      
      <nav className="sidebar-nav">
        {visibleMenuItems.map((section) => (
          <div key={section.id} className="nav-section">
            <button
              className={`nav-section-header ${expandedSection === section.id ? 'expanded' : ''}`}
              onClick={() => toggleSection(section.id)}
            >
              <span className="nav-section-icon">{section.icon}</span>
              <span className="nav-section-label">{section.label}</span>
              {section.badge && <span className="nav-badge">{section.badge}</span>}
              <span className="nav-section-arrow">
                {expandedSection === section.id ? '▼' : '▶'}
              </span>
            </button>
            
            {expandedSection === section.id && (
              <div className="nav-section-items">
                {section.items.map((item) => (
                  <button
                    key={item.id}
                    className={`nav-item ${activeView === item.id ? 'active' : ''}`}
                    onClick={() => setActiveView(item.id)}
                  >
                    {item.label}
                  </button>
                ))}
              </div>
            )}
          </div>
        ))}
      </nav>
    </aside>
  );
}

export default Sidebar;
