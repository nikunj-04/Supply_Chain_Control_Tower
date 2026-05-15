import { useState, useEffect } from 'react';
import { hasPermission, PERMISSIONS } from '../utils/permissions';
import './AuditLogViewer.css';

const AuditLogViewer = () => {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    username: '',
    action: '',
    resource_type: '',
    success: ''
  });
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(50);
  const [totalLogs, setTotalLogs] = useState(0);

  // Get current user from localStorage
  const getCurrentUser = () => {
    try {
      const userStr = localStorage.getItem('user');
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  };

  const currentUser = getCurrentUser();
  const canViewLogs = hasPermission(currentUser, PERMISSIONS.ADMIN_LOGS);

  useEffect(() => {
    if (canViewLogs) {
      fetchLogs();
    }
  }, [filters, currentPage]);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const params = new URLSearchParams();
      
      if (filters.username) params.append('username', filters.username);
      if (filters.action) params.append('action', filters.action);
      if (filters.resource_type) params.append('resource_type', filters.resource_type);
      if (filters.success !== '') params.append('success', filters.success);
      params.append('limit', itemsPerPage);
      params.append('offset', (currentPage - 1) * itemsPerPage);

      const response = await fetch(`http://localhost:8000/api/v1/admin/audit-logs?${params}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setLogs(data.logs || []);
        setTotalLogs(data.total || 0);
      } else {
        console.error('Failed to fetch audit logs');
        setLogs([]);
      }
    } catch (error) {
      console.error('Error fetching audit logs:', error);
      setLogs([]);
    } finally {
      setLoading(false);
    }
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
  };

  const getActionBadgeClass = (action) => {
    if (action.includes('login')) return 'action-login';
    if (action.includes('create')) return 'action-create';
    if (action.includes('update')) return 'action-update';
    if (action.includes('delete')) return 'action-delete';
    return 'action-other';
  };

  const handleFilterChange = (key, value) => {
    setFilters({ ...filters, [key]: value });
    setCurrentPage(1);
  };

  const clearFilters = () => {
    setFilters({
      username: '',
      action: '',
      resource_type: '',
      success: ''
    });
    setCurrentPage(1);
  };

  const totalPages = Math.ceil(totalLogs / itemsPerPage);

  const handlePageChange = (page) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const getPageNumbers = () => {
    const pages = [];
    const maxPagesToShow = 5;
    
    if (totalPages <= maxPagesToShow) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      if (currentPage <= 3) {
        for (let i = 1; i <= 4; i++) pages.push(i);
        pages.push('...');
        pages.push(totalPages);
      } else if (currentPage >= totalPages - 2) {
        pages.push(1);
        pages.push('...');
        for (let i = totalPages - 3; i <= totalPages; i++) pages.push(i);
      } else {
        pages.push(1);
        pages.push('...');
        for (let i = currentPage - 1; i <= currentPage + 1; i++) pages.push(i);
        pages.push('...');
        pages.push(totalPages);
      }
    }
    return pages;
  };

  if (!canViewLogs) {
    return (
      <div className="audit-viewer">
        <div className="access-denied">
          <h2>🔒 Access Denied</h2>
          <p>You don't have permission to view audit logs.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="audit-viewer">
      <div className="audit-header">
        <h1>📋 Audit Log Viewer</h1>
        <div className="log-stats">
          <span className="stat-item">Total Logs: <strong>{totalLogs}</strong></span>
        </div>
      </div>

      {/* Filters (temporarily disabled) */}
      {/*
      <div className="audit-filters">
        <input
          type="text"
          placeholder="Search by username..."
          value={filters.username}
          onChange={(e) => handleFilterChange('username', e.target.value)}
          className="filter-input"
        />

        <select
          value={filters.action}
          onChange={(e) => handleFilterChange('action', e.target.value)}
          className="filter-select"
        >
          <option value="">All Actions</option>
          <option value="user.login">Login</option>
          <option value="user.logout">Logout</option>
          <option value="user.create">Create User</option>
          <option value="user.update">Update User</option>
          <option value="user.delete">Delete User</option>
          <option value="exception.assign">Assign Exception</option>
          <option value="exception.resolve">Resolve Exception</option>
        </select>

        <select
          value={filters.resource_type}
          onChange={(e) => handleFilterChange('resource_type', e.target.value)}
          className="filter-select"
        >
          <option value="">All Resources</option>
          <option value="user">User</option>
          <option value="exception">Exception</option>
          <option value="order">Order</option>
          <option value="shipment">Shipment</option>
        </select>

        <select
          value={filters.success}
          onChange={(e) => handleFilterChange('success', e.target.value)}
          className="filter-select"
        >
          <option value="">All Status</option>
          <option value="true">Success</option>
          <option value="false">Failed</option>
        </select>

        <button onClick={clearFilters} className="clear-filters-btn">
          Clear Filters
        </button>
      </div>
      */}

      {/* Logs Table */}
      <div className="audit-table-container">
        {loading ? (
          <div className="loading">Loading audit logs...</div>
        ) : logs.length === 0 ? (
          <div className="no-logs">No audit logs found</div>
        ) : (
          <table className="audit-table">
            <thead>
              <tr>
                <th>Timestamp</th>
                <th>User</th>
                <th>Action</th>
                <th>Resource</th>
                <th>Details</th>
                <th>IP Address</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.id} className={log.success ? '' : 'log-failed'}>
                  <td className="timestamp">{formatDateTime(log.timestamp)}</td>
                  <td className="username">{log.username}</td>
                  <td>
                    <span className={`action-badge ${getActionBadgeClass(log.action)}`}>
                      {log.action}
                    </span>
                  </td>
                  <td>
                    {log.resource_type && (
                      <span className="resource-info">
                        {log.resource_type}
                        {log.resource_id && <span className="resource-id"> #{log.resource_id}</span>}
                      </span>
                    )}
                  </td>
                  <td className="details">{log.details || '-'}</td>
                  <td className="ip-address">{log.ip_address || '-'}</td>
                  <td>
                    {log.success ? (
                      <span className="status-badge status-success">✓ Success</span>
                    ) : (
                      <span className="status-badge status-failed" title={log.error_message}>
                        ✗ Failed
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {/* Pagination */}
      {!loading && logs.length > 0 && totalPages > 1 && (
        <div className="pagination">
          <button 
            className="pagination-btn"
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
          >
            ← Previous
          </button>
          
          <div className="page-numbers">
            {getPageNumbers().map((page, index) => (
              page === '...' ? (
                <span key={`ellipsis-${index}`} className="pagination-ellipsis">...</span>
              ) : (
                <button
                  key={page}
                  className={`page-number ${currentPage === page ? 'active' : ''}`}
                  onClick={() => handlePageChange(page)}
                >
                  {page}
                </button>
              )
            ))}
          </div>
          
          <button 
            className="pagination-btn"
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
};

export default AuditLogViewer;
