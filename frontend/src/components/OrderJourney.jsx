import { useState, useEffect } from 'react';
import './OrderJourney.css';
import { useGlobalFilters } from '../context/GlobalFiltersContext';

const OrderJourney = () => {
  const [journeys, setJourneys] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [detailView, setDetailView] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);

  const { selectors } = useGlobalFilters();

  useEffect(() => {
    fetchStats();
    fetchJourneys();
  }, []);

  useEffect(() => {
    fetchJourneys();
  }, [statusFilter]);

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/journey/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchJourneys = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);

      const response = await fetch(`http://localhost:8000/api/v1/journey/orders?${params}`);
      const data = await response.json();
      setJourneys(data.journeys || []);
    } catch (error) {
      console.error('Error fetching journeys:', error);
    } finally {
      setLoading(false);
    }
  };

  const viewJourneyDetails = async (orderId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/journey/orders/${orderId}`);
      const data = await response.json();
      setSelectedOrder(data);
      setDetailView(true);
    } catch (error) {
      console.error('Error fetching journey details:', error);
    }
  };

  const getStageIcon = (stage) => {
    const icons = {
      'order_placed': '📝',
      'warehouse_processing': '📦',
      'in_transit': '🚚',
      'out_for_delivery': '📍',
      'delivered': '✅',
      'billing': '💰',
      'returns': '↩️'
    };
    return icons[stage] || '⚪';
  };

  const getStageColor = (status) => {
    const colors = {
      'completed': '#10b981',
      'in_progress': '#3b82f6',
      'pending': '#9ca3af'
    };
    return colors[status] || '#9ca3af';
  };

  const getSystemBadgeClass = (system) => {
    const classes = {
      'OMS': 'system-oms',
      'WMS': 'system-wms',
      'TMS': 'system-tms',
      'Tracking': 'system-tracking',
      'Billing': 'system-billing',
      'Returns': 'system-returns'
    };
    return classes[system] || 'system-default';
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const filteredJourneys = journeys.filter(j =>
    j.order_id.toLowerCase().includes(searchTerm.toLowerCase()) ||
    j.customer.toLowerCase().includes(searchTerm.toLowerCase())
  );

  // Pagination calculations
  const totalPages = Math.ceil(filteredJourneys.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedJourneys = filteredJourneys.slice(startIndex, endIndex);

  // Reset to page 1 when search or filter changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, statusFilter]);

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
    <div className="journey-container">
      <div className="journey-header">
        <div>
          <h1>🔄 End-to-End Order Journey</h1>
          <div style={{ fontSize: '12px', opacity: 0.85, marginTop: '6px' }}>
            <strong>Active Filters:</strong> {selectors.activeFiltersText}
          </div>
        </div>
        <input
          type="text"
          className="search-input"
          placeholder="Search by Order ID or Customer..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </div>

      {/* Stats Cards */}
      <div className="journey-stats">
        <div className="stat-card total">
          <div className="stat-icon">📋</div>
          <div className="stat-content">
            <h3>{stats.total_orders || 0}</h3>
            <p>Total Orders</p>
          </div>
        </div>
        <div className="stat-card pending">
          <div className="stat-icon">⏳</div>
          <div className="stat-content">
            <h3>{stats.pending || 0}</h3>
            <p>Pending</p>
          </div>
        </div>
        <div className="stat-card processing">
          <div className="stat-icon">⚙️</div>
          <div className="stat-content">
            <h3>{stats.processing || 0}</h3>
            <p>Processing</p>
          </div>
        </div>
        <div className="stat-card shipped">
          <div className="stat-icon">🚚</div>
          <div className="stat-content">
            <h3>{stats.shipped || 0}</h3>
            <p>Shipped</p>
          </div>
        </div>
        <div className="stat-card delivered">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <h3>{stats.delivered || 0}</h3>
            <p>Delivered</p>
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="journey-filters">
        <select 
          value={statusFilter} 
          onChange={(e) => setStatusFilter(e.target.value)}
          className="status-filter"
        >
          <option value="">All Statuses</option>
          <option value="pending">Pending</option>
          <option value="processing">Processing</option>
          <option value="shipped">Shipped</option>
          <option value="delivered">Delivered</option>
        </select>
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
          <span className="result-count">
            Showing {startIndex + 1}-{Math.min(endIndex, filteredJourneys.length)} of {filteredJourneys.length}
          </span>
        </div>
      </div>

      {/* Journeys List */}
      <div className="journeys-list">
        {loading ? (
          <div className="loading">Loading journeys...</div>
        ) : filteredJourneys.length === 0 ? (
          <div className="no-data">No orders found</div>
        ) : (
          paginatedJourneys.map((journey) => (
            <div key={journey.order_id} className="journey-card">
              <div className="journey-card-header">
                <div className="order-info">
                  <h3>{journey.order_id}</h3>
                  <p className="customer-name">{journey.customer}</p>
                </div>
                <div className="order-meta">
                  <span className={`status-badge status-${journey.status}`}>
                    {journey.status.toUpperCase()}
                  </span>
                  <span className="amount">${journey.total_amount.toFixed(2)}</span>
                </div>
              </div>

              <div className="journey-stages">
                {['order_placed', 'warehouse_processing', 'in_transit', 'delivered'].map((stage) => {
                  const isActive = journey.current_stage === stage;
                  const isPast = ['order_placed', 'warehouse_processing', 'in_transit', 'delivered'].indexOf(stage) <
                                 ['order_placed', 'warehouse_processing', 'in_transit', 'delivered'].indexOf(journey.current_stage);
                  const status = isPast ? 'completed' : (isActive ? 'in_progress' : 'pending');
                  
                  return (
                    <div key={stage} className={`stage-indicator ${status}`}>
                      <div 
                        className="stage-dot" 
                        style={{ backgroundColor: getStageColor(status) }}
                      >
                        {getStageIcon(stage)}
                      </div>
                      <span className="stage-label">{stage.replace('_', ' ')}</span>
                    </div>
                  );
                })}
              </div>

              {journey.delivery_progress > 0 && journey.current_stage === 'in_transit' && (
                <div className="progress-section">
                  <div className="progress-header">
                    <span>Delivery Progress</span>
                    <span>{journey.delivery_progress.toFixed(0)}%</span>
                  </div>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill" 
                      style={{ width: `${journey.delivery_progress}%` }}
                    ></div>
                  </div>
                </div>
              )}

              <div className="journey-footer">
                <span className="order-date">Ordered: {formatDateTime(journey.order_date)}</span>
                {journey.is_delayed && <span className="delayed-badge">⚠️ Delayed</span>}
                <button 
                  className="view-journey-btn"
                  onClick={() => viewJourneyDetails(journey.order_id)}
                >
                  View Full Journey
                </button>
              </div>
            </div>
          ))
        )}
      </div>

      {/* Pagination */}
      {!loading && filteredJourneys.length > 0 && totalPages > 1 && (
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

      {/* Detail Modal */}
      {detailView && selectedOrder && (
        <div className="modal-overlay" onClick={() => setDetailView(false)}>
          <div className="modal-content journey-modal" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setDetailView(false)}>✖️</button>
            
            <div className="modal-header">
              <div className="modal-title-section">
                <h2>{selectedOrder.order_id}</h2>
                <p className="modal-customer">{selectedOrder.customer}</p>
              </div>
              <span className={`status-badge status-${selectedOrder.status}`}>
                {selectedOrder.status.toUpperCase()}
              </span>
            </div>

            <div className="modal-body">
              {/* Metrics */}
              <div className="metrics-section">
                <div className="metric-item">
                  <span className="metric-label">Order Age</span>
                  <span className="metric-value">{selectedOrder.metrics.order_age_hours.toFixed(1)} hours</span>
                </div>
                {selectedOrder.metrics.transit_time_hours && (
                  <div className="metric-item">
                    <span className="metric-label">Transit Time</span>
                    <span className="metric-value">{selectedOrder.metrics.transit_time_hours.toFixed(1)} hours</span>
                  </div>
                )}
                <div className="metric-item">
                  <span className="metric-label">Total Events</span>
                  <span className="metric-value">{selectedOrder.metrics.total_events}</span>
                </div>
                <div className="metric-item">
                  <span className="metric-label">Systems</span>
                  <span className="metric-value">{selectedOrder.metrics.systems_touched}</span>
                </div>
              </div>

              {/* Stages */}
              <div className="detail-section">
                <h3>Journey Stages</h3>
                <div className="stages-grid">
                  {selectedOrder.stages.map((stage, index) => (
                    <div key={index} className={`stage-card stage-${stage.status}`}>
                      <div className="stage-card-header">
                        <span className="stage-icon">{getStageIcon(stage.stage)}</span>
                        <h4>{stage.name}</h4>
                        <span className={`stage-status-badge status-${stage.status}`}>
                          {stage.status.replace('_', ' ')}
                        </span>
                      </div>
                      {stage.timestamp && (
                        <p className="stage-timestamp">{formatDateTime(stage.timestamp)}</p>
                      )}
                      {stage.details && Object.keys(stage.details).length > 0 && (
                        <div className="stage-details">
                          {Object.entries(stage.details).map(([key, value]) => {
                            if (typeof value === 'object') return null;
                            return (
                              <div key={key} className="detail-row">
                                <span className="detail-label">{key.replace('_', ' ')}:</span>
                                <span className="detail-value">{String(value)}</span>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>

              {/* Timeline */}
              <div className="detail-section">
                <h3>Event Timeline</h3>
                <div className="timeline">
                  {selectedOrder.timeline.map((event, index) => (
                    <div key={index} className="timeline-item">
                      <div className="timeline-dot">
                        <span className={`system-badge ${getSystemBadgeClass(event.system)}`}>
                          {event.system}
                        </span>
                      </div>
                      <div className="timeline-content">
                        <div className="timeline-header">
                          <strong>{event.event}</strong>
                          <span className="timeline-time">{formatDateTime(event.timestamp)}</span>
                        </div>
                        <p className="timeline-description">{event.description}</p>
                        {event.details && (
                          <span className="timeline-details">{event.details}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default OrderJourney;
