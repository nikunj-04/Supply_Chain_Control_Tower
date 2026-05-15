import { useState, useEffect } from 'react';
import { hasPermission, PERMISSIONS } from '../utils/permissions';
import './ExceptionCenter.css';

const ExceptionCenter = () => {
  const [exceptions, setExceptions] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({
    status: '',
    severity: '',
    type: ''
  });
  const [selectedExc, setSelectedExc] = useState(null);
  const [detailView, setDetailView] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const [assignableUsers, setAssignableUsers] = useState([]);
  const [showAssignModal, setShowAssignModal] = useState(false);
  const [assigningException, setAssigningException] = useState(null);
  
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
  
  // Permission checks
  const canResolve = hasPermission(currentUser, PERMISSIONS.EXCEPTIONS_RESOLVE);
  const canAssign = hasPermission(currentUser, PERMISSIONS.EXCEPTIONS_ASSIGN);
  const canEscalate = hasPermission(currentUser, PERMISSIONS.EXCEPTIONS_ESCALATE);
  
  // Debug logging
  console.log('Exception Center - Current User:', currentUser);
  console.log('Exception Center - canAssign:', canAssign);
  console.log('Exception Center - canResolve:', canResolve);

  useEffect(() => {
    fetchStats();
    fetchExceptions();
    fetchAssignableUsers();
    // Run detection on mount
    detectExceptions();
  }, []);

  useEffect(() => {
    fetchExceptions();
  }, [filters]);

  // Reset to page 1 when filters change
  useEffect(() => {
    setCurrentPage(1);
  }, [filters]);

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/exceptions/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchExceptions = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (filters.status) params.append('status', filters.status);
      if (filters.severity) params.append('severity', filters.severity);
      if (filters.type) params.append('exception_type', filters.type);

      const response = await fetch(`http://localhost:8000/api/v1/exceptions?${params}`);
      const data = await response.json();
      setExceptions(data.exceptions || []);
    } catch (error) {
      console.error('Error fetching exceptions:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchAssignableUsers = async () => {
    try {
      const token = localStorage.getItem('token');
      if (!token) return;

      const response = await fetch('http://localhost:8000/api/v1/users/assignable', {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      const data = await response.json();
      setAssignableUsers(data.users || []);
    } catch (error) {
      console.error('Error fetching assignable users:', error);
    }
  };

  const detectExceptions = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/exceptions/detect', {
        method: 'POST'
      });
      const data = await response.json();
      console.log('Exception detection:', data);
      fetchStats();
      fetchExceptions();
    } catch (error) {
      console.error('Error detecting exceptions:', error);
    }
  };

  const updateStatus = async (exceptionId, newStatus) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/exceptions/${exceptionId}/status?status=${newStatus}&user=admin`,
        { method: 'PUT' }
      );
      const data = await response.json();
      console.log('Status updated:', data);
      fetchStats();
      fetchExceptions();
      if (selectedExc && selectedExc.exception_id === exceptionId) {
        setSelectedExc(data);
      }
    } catch (error) {
      console.error('Error updating status:', error);
    }
  };

  const assignException = async (exceptionId, assignee) => {
    console.log('Assigning exception:', exceptionId, 'to:', assignee);
    try {
      const currentUserData = getCurrentUser();
      const assignedBy = currentUserData?.username || 'system';
      
      console.log('Making API call to assign exception...');
      const response = await fetch(
        `http://localhost:8000/api/v1/exceptions/${exceptionId}/assign?assigned_to=${assignee}&assigned_by=${assignedBy}`,
        { method: 'PUT' }
      );
      const data = await response.json();
      console.log('Exception assigned:', data);
      fetchExceptions();
      setShowAssignModal(false);
      setAssigningException(null);
    } catch (error) {
      console.error('Error assigning exception:', error);
      alert('Failed to assign exception: ' + error.message);
    }
  };

  const openAssignModal = (exc) => {
    console.log('Opening assign modal for exception:', exc);
    console.log('Assignable users:', assignableUsers);
    setAssigningException(exc);
    setShowAssignModal(true);
  };

  const viewDetails = async (exceptionId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/exceptions/${exceptionId}`);
      const data = await response.json();
      setSelectedExc(data.exception);
      setDetailView(true);
    } catch (error) {
      console.error('Error fetching exception details:', error);
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical': return '🔴';
      case 'warning': return '🟡';
      case 'info': return '🔵';
      default: return '⚪';
    }
  };

  const getSeverityClass = (severity) => {
    return `severity-${severity}`;
  };

  const getTypeLabel = (type) => {
    const labels = {
      delay: 'Shipment Delay',
      inventory: 'Low Inventory',
      processing_delay: 'Order Stuck',
      returns_delay: 'Returns Backlog',
      quality: 'Quality Issue',
      billing: 'Billing Issue',
      capacity: 'Capacity Issue'
    };
    return labels[type] || type;
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Pagination logic
  const totalPages = Math.ceil(exceptions.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedExceptions = exceptions.slice(startIndex, endIndex);

  const handlePageChange = (page) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const handleItemsPerPageChange = (e) => {
    setItemsPerPage(Number(e.target.value));
    setCurrentPage(1);
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

  return (
    <div className="exception-center">
      <div className="exception-header">
        <h1>🚨 Exception Management Center</h1>
        <button type="button" className="detect-btn" onClick={detectExceptions}>
          🔍 Scan for Exceptions
        </button>
      </div>

      {/* Stats Cards */}
      <div className="exception-stats">
        <div className="stat-card critical">
          <div className="stat-icon">🔴</div>
          <div className="stat-content">
            <h3>{stats.critical || 0}</h3>
            <p>Critical</p>
          </div>
        </div>
        <div className="stat-card warning">
          <div className="stat-icon">🟡</div>
          <div className="stat-content">
            <h3>{stats.warning || 0}</h3>
            <p>Warning</p>
          </div>
        </div>
        <div className="stat-card open">
          <div className="stat-icon">📋</div>
          <div className="stat-content">
            <h3>{stats.open || 0}</h3>
            <p>Open</p>
          </div>
        </div>
        <div className="stat-card in-progress">
          <div className="stat-icon">⚙️</div>
          <div className="stat-content">
            <h3>{stats.in_progress || 0}</h3>
            <p>In Progress</p>
          </div>
        </div>
        <div className="stat-card resolved">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <h3>{stats.resolved || 0}</h3>
            <p>Resolved</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="exception-filters">
        <div className="filter-row">
          <select 
            value={filters.severity} 
            onChange={(e) => setFilters({...filters, severity: e.target.value})}
          >
            <option value="">All Severities</option>
            <option value="critical">Critical</option>
            <option value="warning">Warning</option>
            <option value="info">Info</option>
          </select>

          <select 
            value={filters.status} 
            onChange={(e) => setFilters({...filters, status: e.target.value})}
          >
            <option value="">All Statuses</option>
            <option value="open">Open</option>
            <option value="in_progress">In Progress</option>
            <option value="resolved">Resolved</option>
            <option value="dismissed">Dismissed</option>
          </select>

          <select 
            value={filters.type} 
            onChange={(e) => setFilters({...filters, type: e.target.value})}
          >
            <option value="">All Types</option>
            <option value="delay">Shipment Delay</option>
            <option value="inventory">Inventory</option>
            <option value="processing_delay">Processing Delay</option>
            <option value="returns_delay">Returns Delay</option>
            <option value="quality">Quality</option>
            <option value="billing">Billing</option>
          </select>

          <button 
            type="button"
            className="clear-filters-btn"
            onClick={() => setFilters({ status: '', severity: '', type: '' })}
          >
            Clear Filters
          </button>
        </div>

        <div className="pagination-controls">
          <label>
            Show:
            <select value={itemsPerPage} onChange={handleItemsPerPageChange} className="items-per-page-select">
              <option value="5">5</option>
              <option value="10">10</option>
              <option value="25">25</option>
              <option value="50">50</option>
              <option value="100">100</option>
            </select>
            per page
          </label>
          {exceptions.length > 0 && (
            <span className="result-count">
              Showing {startIndex + 1}-{Math.min(endIndex, exceptions.length)} of {exceptions.length}
            </span>
          )}
        </div>
      </div>

      {/* Exceptions List */}
      <div className="exceptions-container">
        {loading ? (
          <div className="loading">Loading exceptions...</div>
        ) : exceptions.length === 0 ? (
          <div className="no-exceptions">
            <p>✨ No exceptions found matching your filters</p>
          </div>
        ) : (
          <div className="exceptions-list">
            {paginatedExceptions.map((exc) => (
              <div 
                key={exc.exception_id} 
                className={`exception-card ${getSeverityClass(exc.severity)} ${exc.status}`}
              >
                <div className="exception-card-header">
                  <div className="exception-title-row">
                    <span className="severity-badge">
                      {getSeverityIcon(exc.severity)} {exc.severity.toUpperCase()}
                    </span>
                    <span className="type-badge">{getTypeLabel(exc.exception_type)}</span>
                    <span className={`status-badge status-${exc.status}`}>
                      {exc.status.replace('_', ' ').toUpperCase()}
                    </span>
                  </div>
                  <h3>{exc.title}</h3>
                </div>

                <div className="exception-details">
                  <p className="description">{exc.description}</p>
                  
                  <div className="exception-meta">
                    <div className="meta-item">
                      <span className="label">Source:</span>
                      <span className="value">{exc.source_system}</span>
                    </div>
                    <div className="meta-item">
                      <span className="label">Entity:</span>
                      <span className="value">{exc.entity_id}</span>
                    </div>
                    {exc.customer && (
                      <div className="meta-item">
                        <span className="label">Customer:</span>
                        <span className="value">{exc.customer}</span>
                      </div>
                    )}
                    {exc.location && (
                      <div className="meta-item">
                        <span className="label">Location:</span>
                        <span className="value">{exc.location}</span>
                      </div>
                    )}
                    {exc.cost_impact && (
                      <div className="meta-item">
                        <span className="label">Cost Impact:</span>
                        <span className="value cost">${exc.cost_impact.toFixed(2)}</span>
                      </div>
                    )}
                  </div>

                  <div className="exception-times">
                    <div className="time-item">
                      <span className="label">Detected:</span>
                      <span className="value">{formatDateTime(exc.detected_at)}</span>
                    </div>
                    {exc.assigned_to && (
                      <div className="time-item">
                        <span className="label">Assigned to:</span>
                        <span className="value assigned">{exc.assigned_to}</span>
                      </div>
                    )}
                  </div>
                </div>

                <div className="exception-actions">
                  <button 
                    type="button"
                    className="action-btn view-btn"
                    onClick={() => viewDetails(exc.exception_id)}
                  >
                    👁️ View
                  </button>
                  
                  {exc.status === 'open' && (
                    <>
                      {canAssign && (
                        <button 
                          type="button"
                          className="action-btn assign-btn"
                          onClick={() => openAssignModal(exc)}
                        >
                          👤 Assign
                        </button>
                      )}
                      {canResolve && (
                        <button 
                          type="button"
                          className="action-btn progress-btn"
                          onClick={() => updateStatus(exc.exception_id, 'in_progress')}
                        >
                          ⚙️ Start Work
                        </button>
                      )}
                    </>
                  )}
                  
                  {exc.status === 'in_progress' && canResolve && (
                    <button 
                      type="button"
                      className="action-btn resolve-btn"
                      onClick={() => updateStatus(exc.exception_id, 'resolved')}
                    >
                      ✅ Resolve
                    </button>
                  )}
                  
                  {canResolve && (
                    <button 
                      type="button"
                      className="action-btn dismiss-btn"
                      onClick={() => updateStatus(exc.exception_id, 'dismissed')}
                    >
                      ✖️ Dismiss
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Pagination */}
      {!loading && exceptions.length > 0 && totalPages > 1 && (
        <div className="pagination">
          <button 
            type="button"
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
                  type="button"
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
            type="button"
            className="pagination-btn"
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
          >
            Next →
          </button>
        </div>
      )}

      {/* Assignment Modal */}
      {showAssignModal && assigningException && (
        <div className="modal-overlay" onClick={() => setShowAssignModal(false)}>
          <div className="modal-content assign-modal" onClick={(e) => e.stopPropagation()}>
            <button type="button" className="modal-close" onClick={() => setShowAssignModal(false)}>✖️</button>
            
            <div className="modal-header">
              <h2>Assign Exception</h2>
            </div>

            <div className="modal-body">
              <div className="assign-info">
                <h3>{assigningException.title}</h3>
                <p className="exception-id">ID: {assigningException.exception_id}</p>
                <span className={`severity-badge ${getSeverityClass(assigningException.severity)}`}>
                  {getSeverityIcon(assigningException.severity)} {assigningException.severity.toUpperCase()}
                </span>
              </div>

              <div className="user-list">
                <h4>Select User to Assign:</h4>
                {assignableUsers.length === 0 ? (
                  <p className="no-users">No assignable users found</p>
                ) : (
                  <div className="user-options">
                    {assignableUsers.map((user) => (
                      <div 
                        key={user.user_id}
                        className="user-option"
                        onClick={() => assignException(assigningException.exception_id, user.username)}
                      >
                        <div className="user-info">
                          <div className="user-name">{user.full_name}</div>
                          <div className="user-meta">
                            <span className="username">@{user.username}</span>
                            {user.email && <span className="email">{user.email}</span>}
                          </div>
                          {user.roles && user.roles.length > 0 && (
                            <div className="user-roles">
                              {user.roles.map((role, idx) => (
                                <span key={idx} className="role-badge">{role.display_name || role.name || role}</span>
                              ))}
                            </div>
                          )}
                        </div>
                        <button type="button" className="assign-user-btn">Assign →</button>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Detail Modal */}
      {detailView && selectedExc && (
        <div className="modal-overlay" onClick={() => setDetailView(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <button type="button" className="modal-close" onClick={() => setDetailView(false)}>✖️</button>
            
            <div className="modal-header">
              <h2>{selectedExc.title}</h2>
              <span className={`severity-badge ${getSeverityClass(selectedExc.severity)}`}>
                {getSeverityIcon(selectedExc.severity)} {selectedExc.severity.toUpperCase()}
              </span>
            </div>

            <div className="modal-body">
              <div className="detail-section">
                <h3>Details</h3>
                <p>{selectedExc.description}</p>
                {selectedExc.impact && (
                  <div className="impact-box">
                    <strong>Business Impact:</strong> {selectedExc.impact}
                  </div>
                )}
              </div>

              <div className="detail-grid">
                <div className="detail-item">
                  <strong>Exception ID:</strong>
                  <span>{selectedExc.exception_id}</span>
                </div>
                <div className="detail-item">
                  <strong>Type:</strong>
                  <span>{getTypeLabel(selectedExc.exception_type)}</span>
                </div>
                <div className="detail-item">
                  <strong>Status:</strong>
                  <span className={`status-badge status-${selectedExc.status}`}>
                    {selectedExc.status.replace('_', ' ')}
                  </span>
                </div>
                <div className="detail-item">
                  <strong>Source System:</strong>
                  <span>{selectedExc.source_system}</span>
                </div>
                <div className="detail-item">
                  <strong>Entity:</strong>
                  <span>{selectedExc.entity_type}: {selectedExc.entity_id}</span>
                </div>
                {selectedExc.customer && (
                  <div className="detail-item">
                    <strong>Customer:</strong>
                    <span>{selectedExc.customer}</span>
                  </div>
                )}
                {selectedExc.carrier && (
                  <div className="detail-item">
                    <strong>Carrier:</strong>
                    <span>{selectedExc.carrier}</span>
                  </div>
                )}
                {selectedExc.cost_impact && (
                  <div className="detail-item">
                    <strong>Cost Impact:</strong>
                    <span className="cost">${selectedExc.cost_impact.toFixed(2)}</span>
                  </div>
                )}
                {selectedExc.days_delayed && (
                  <div className="detail-item">
                    <strong>Days Delayed:</strong>
                    <span>{selectedExc.days_delayed}</span>
                  </div>
                )}
              </div>

              {selectedExc.resolution_notes && (
                <div className="detail-section">
                  <h3>Resolution Notes</h3>
                  <p>{selectedExc.resolution_notes}</p>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ExceptionCenter;
