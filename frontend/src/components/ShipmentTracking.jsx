import { useState, useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import './ShipmentTracking.css';
import { useGlobalFilters } from '../context/GlobalFiltersContext';

// Fix for default marker icons in react-leaflet
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom marker icons
const createCustomIcon = (color, icon) => {
  return L.divIcon({
    html: `<div style="background-color: ${color}; width: 32px; height: 32px; border-radius: 50%; display: flex; align-items: center; justify-content: center; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3); font-size: 16px;">${icon}</div>`,
    className: 'custom-marker',
    iconSize: [32, 32],
    iconAnchor: [16, 16]
  });
};

const statusIcons = {
  'in_transit': createCustomIcon('#3b82f6', '🚚'),
  'out_for_delivery': createCustomIcon('#10b981', '📦'),
  'delayed': createCustomIcon('#ef4444', '⚠️'),
  'scheduled': createCustomIcon('#6b7280', '📅'),
};

// Component to auto-fit map bounds
function MapBounds({ shipments }) {
  const map = useMap();
  
  useEffect(() => {
    if (shipments && shipments.length > 0) {
      const bounds = shipments.map(s => [
        s.current_location.latitude,
        s.current_location.longitude
      ]);
      
      if (bounds.length > 0) {
        map.fitBounds(bounds, { padding: [50, 50] });
      }
    }
  }, [shipments, map]);
  
  return null;
}

const ShipmentTracking = () => {
  const [shipments, setShipments] = useState([]);
  const [stats, setStats] = useState({});
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState('map'); // 'map' or 'list'
  const [statusFilter, setStatusFilter] = useState('');
  const [selectedShipment, setSelectedShipment] = useState(null);
  const [detailView, setDetailView] = useState(false);
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(10);
  const mapRef = useRef();

  const { selectors } = useGlobalFilters();

  useEffect(() => {
    fetchStats();
    fetchShipments();
    initializeTracking();
  }, []);

  useEffect(() => {
    fetchShipments();
  }, [statusFilter]);

  useEffect(() => {
    // Reset to page 1 when filters change
    setCurrentPage(1);
  }, [statusFilter, viewMode]);

  useEffect(() => {
    if (autoRefresh) {
      const interval = setInterval(() => {
        updateLocations();
      }, 15000); // Update every 15 seconds
      return () => clearInterval(interval);
    }
  }, [autoRefresh]);

  const fetchStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/tracking/stats');
      const data = await response.json();
      setStats(data);
    } catch (error) {
      console.error('Error fetching stats:', error);
    }
  };

  const fetchShipments = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams();
      if (statusFilter) params.append('status', statusFilter);

      const response = await fetch(`http://localhost:8000/api/v1/tracking/shipments?${params}`);
      const data = await response.json();
      setShipments(data.shipments || []);
    } catch (error) {
      console.error('Error fetching shipments:', error);
    } finally {
      setLoading(false);
    }
  };

  const initializeTracking = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/tracking/initialize', {
        method: 'POST'
      });
      const data = await response.json();
      console.log('Tracking initialized:', data);
      fetchStats();
      fetchShipments();
    } catch (error) {
      console.error('Error initializing tracking:', error);
    }
  };

  const updateLocations = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/v1/tracking/update-locations', {
        method: 'POST'
      });
      const data = await response.json();
      console.log('Locations updated:', data);
      fetchShipments();
      fetchStats();
    } catch (error) {
      console.error('Error updating locations:', error);
    }
  };

  const viewShipmentDetails = async (shipmentId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/v1/tracking/shipments/${shipmentId}`);
      const data = await response.json();
      setSelectedShipment(data);
      setDetailView(true);
    } catch (error) {
      console.error('Error fetching shipment details:', error);
    }
  };

  const getStatusBadgeClass = (status) => {
    const classes = {
      'in_transit': 'status-transit',
      'out_for_delivery': 'status-delivery',
      'delayed': 'status-delayed',
      'scheduled': 'status-scheduled',
      'delivered': 'status-delivered'
    };
    return classes[status] || 'status-default';
  };

  const formatDateTime = (dateStr) => {
    if (!dateStr) return 'N/A';
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  // Pagination calculations
  const totalPages = Math.ceil(shipments.length / itemsPerPage);
  const indexOfLastItem = currentPage * itemsPerPage;
  const indexOfFirstItem = indexOfLastItem - itemsPerPage;
  const currentShipments = shipments.slice(indexOfFirstItem, indexOfLastItem);

  const handlePageChange = (pageNumber) => {
    setCurrentPage(pageNumber);
    // Scroll to top of list
    document.querySelector('.shipments-list')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  const handleItemsPerPageChange = (e) => {
    setItemsPerPage(Number(e.target.value));
    setCurrentPage(1); // Reset to first page
  };

  const renderPaginationButtons = () => {
    const buttons = [];
    const maxVisibleButtons = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxVisibleButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxVisibleButtons - 1);

    if (endPage - startPage < maxVisibleButtons - 1) {
      startPage = Math.max(1, endPage - maxVisibleButtons + 1);
    }

    // First page button
    if (startPage > 1) {
      buttons.push(
        <button key="first" onClick={() => handlePageChange(1)} className="page-btn">
          1
        </button>
      );
      if (startPage > 2) {
        buttons.push(<span key="dots1" className="page-dots">...</span>);
      }
    }

    // Page number buttons
    for (let i = startPage; i <= endPage; i++) {
      buttons.push(
        <button
          key={i}
          onClick={() => handlePageChange(i)}
          className={`page-btn ${currentPage === i ? 'active' : ''}`}
        >
          {i}
        </button>
      );
    }

    // Last page button
    if (endPage < totalPages) {
      if (endPage < totalPages - 1) {
        buttons.push(<span key="dots2" className="page-dots">...</span>);
      }
      buttons.push(
        <button key="last" onClick={() => handlePageChange(totalPages)} className="page-btn">
          {totalPages}
        </button>
      );
    }

    return buttons;
  };

  return (
    <div className="tracking-container">
      <div className="tracking-header">
        <div>
          <h1>📍 Real-Time Shipment Tracking</h1>
          <div style={{ fontSize: '12px', opacity: 0.85, marginTop: '6px' }}>
            <strong>Active Filters:</strong> {selectors.activeFiltersText}
          </div>
        </div>
        <div className="header-actions">
          <label className="auto-refresh-toggle">
            <input 
              type="checkbox" 
              checked={autoRefresh} 
              onChange={(e) => setAutoRefresh(e.target.checked)}
            />
            Auto-refresh
          </label>
          <button className="refresh-btn" onClick={updateLocations}>
            🔄 Update Locations
          </button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="tracking-stats">
        <div className="stat-card total">
          <div className="stat-icon">📦</div>
          <div className="stat-content">
            <h3>{stats.total_tracked || 0}</h3>
            <p>Total Tracked</p>
          </div>
        </div>
        <div className="stat-card transit">
          <div className="stat-icon">🚚</div>
          <div className="stat-content">
            <h3>{stats.in_transit || 0}</h3>
            <p>In Transit</p>
          </div>
        </div>
        <div className="stat-card delivery">
          <div className="stat-icon">📍</div>
          <div className="stat-content">
            <h3>{stats.out_for_delivery || 0}</h3>
            <p>Out for Delivery</p>
          </div>
        </div>
        <div className="stat-card delayed">
          <div className="stat-icon">⚠️</div>
          <div className="stat-content">
            <h3>{stats.delayed || 0}</h3>
            <p>Delayed</p>
          </div>
        </div>
        <div className="stat-card ontime">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <h3>{stats.on_time || 0}</h3>
            <p>On Time</p>
          </div>
        </div>
      </div>

      {/* View Toggle and Filters */}
      <div className="tracking-controls">
        <div className="view-toggle">
          <button 
            className={`toggle-btn ${viewMode === 'map' ? 'active' : ''}`}
            onClick={() => setViewMode('map')}
          >
            🗺️ Map View
          </button>
          <button 
            className={`toggle-btn ${viewMode === 'list' ? 'active' : ''}`}
            onClick={() => setViewMode('list')}
          >
            📋 List View
          </button>
        </div>

        <select 
          value={statusFilter} 
          onChange={(e) => setStatusFilter(e.target.value)}
          className="status-filter"
        >
          <option value="">All Statuses</option>
          <option value="in_transit">In Transit</option>
          <option value="out_for_delivery">Out for Delivery</option>
          <option value="scheduled">Scheduled</option>
        </select>
      </div>

      {/* Map View */}
      {viewMode === 'map' && (
        <div className="map-container">
          {loading ? (
            <div className="loading">Loading map...</div>
          ) : shipments.length === 0 ? (
            <div className="no-data">No shipments to display</div>
          ) : (
            <MapContainer
              center={[39.8283, -98.5795]} // Center of USA
              zoom={4}
              style={{ height: '600px', width: '100%' }}
              ref={mapRef}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              
              <MapBounds shipments={shipments} />
              
              {shipments.map((shipment) => (
                <Marker
                  key={shipment.shipment_id}
                  position={[
                    shipment.current_location.latitude,
                    shipment.current_location.longitude
                  ]}
                  icon={statusIcons[shipment.status] || statusIcons['in_transit']}
                >
                  <Popup>
                    <div className="map-popup">
                      <h4>{shipment.shipment_id}</h4>
                      <p><strong>Carrier:</strong> {shipment.carrier}</p>
                      <p><strong>Status:</strong> <span className={getStatusBadgeClass(shipment.status)}>{shipment.status.replace('_', ' ')}</span></p>
                      <p><strong>Location:</strong> {shipment.current_location.name}</p>
                      <p><strong>Progress:</strong> {shipment.progress.percentage}%</p>
                      <p><strong>ETA:</strong> {formatDateTime(shipment.timing.estimated_delivery)}</p>
                      <button 
                        className="popup-details-btn"
                        onClick={() => viewShipmentDetails(shipment.shipment_id)}
                      >
                        View Details
                      </button>
                    </div>
                  </Popup>
                </Marker>
              ))}
            </MapContainer>
          )}
        </div>
      )}

      {/* List View */}
      {viewMode === 'list' && (
        <div className="shipments-list">
          {loading ? (
            <div className="loading">Loading shipments...</div>
          ) : shipments.length === 0 ? (
            <div className="no-data">No shipments found</div>
          ) : (
            <>
              <div className="list-controls">
                <div className="list-info">
                  Showing {indexOfFirstItem + 1}-{Math.min(indexOfLastItem, shipments.length)} of {shipments.length} shipments
                </div>
                <div className="items-per-page">
                  <label>Items per page:</label>
                  <select value={itemsPerPage} onChange={handleItemsPerPageChange}>
                    <option value="5">5</option>
                    <option value="10">10</option>
                    <option value="20">20</option>
                    <option value="50">50</option>
                  </select>
                </div>
              </div>

              {currentShipments.map((shipment) => (
                <div key={shipment.shipment_id} className="shipment-card">
                  <div className="shipment-header">
                    <div className="shipment-id-row">
                      <h3>{shipment.shipment_id}</h3>
                      <span className={`status-badge ${getStatusBadgeClass(shipment.status)}`}>
                        {shipment.status.replace('_', ' ').toUpperCase()}
                      </span>
                    </div>
                    <p className="order-id">Order: {shipment.order_id}</p>
                  </div>

                  <div className="shipment-details">
                    <div className="detail-row">
                      <span className="label">Carrier:</span>
                      <span className="value">{shipment.carrier}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Origin:</span>
                      <span className="value">{shipment.origin}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Destination:</span>
                      <span className="value">{shipment.destination}</span>
                    </div>
                    <div className="detail-row">
                      <span className="label">Current Location:</span>
                      <span className="value location">{shipment.current_location.name}</span>
                    </div>
                  </div>

                  <div className="progress-section">
                    <div className="progress-header">
                      <span>Progress: {shipment.progress.percentage}%</span>
                      <span>{shipment.progress.distance_traveled.toFixed(0)} / {(shipment.progress.distance_traveled + shipment.progress.distance_remaining).toFixed(0)} miles</span>
                    </div>
                    <div className="progress-bar">
                      <div 
                        className="progress-fill" 
                        style={{ width: `${shipment.progress.percentage}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="shipment-timing">
                    <div className="timing-item">
                      <span className="label">ETA:</span>
                      <span className={`value ${shipment.timing.is_delayed ? 'delayed' : ''}`}>
                        {formatDateTime(shipment.timing.estimated_delivery)}
                        {shipment.timing.is_delayed && ' ⚠️'}
                      </span>
                    </div>
                    {shipment.speed_mph && (
                      <div className="timing-item">
                        <span className="label">Speed:</span>
                        <span className="value">{shipment.speed_mph.toFixed(0)} mph {shipment.heading}</span>
                      </div>
                    )}
                  </div>

                  <button 
                    className="details-btn"
                    onClick={() => viewShipmentDetails(shipment.shipment_id)}
                  >
                    View Full Details
                  </button>
                </div>
              ))}

              {/* Pagination Controls */}
              {totalPages > 1 && (
                <div className="pagination">
                  <button
                    className="pagination-btn"
                    onClick={() => handlePageChange(currentPage - 1)}
                    disabled={currentPage === 1}
                  >
                    ← Previous
                  </button>

                  <div className="pagination-pages">
                    {renderPaginationButtons()}
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
            </>
          )}
        </div>
      )}

      {/* Detail Modal */}
      {detailView && selectedShipment && (
        <div className="modal-overlay" onClick={() => setDetailView(false)}>
          <div className="modal-content detail-modal" onClick={(e) => e.stopPropagation()}>
            <button className="modal-close" onClick={() => setDetailView(false)}>✖️</button>
            
            <div className="modal-header">
              <h2>{selectedShipment.shipment.shipment_id}</h2>
              <span className={`status-badge ${getStatusBadgeClass(selectedShipment.current_location.status)}`}>
                {selectedShipment.current_location.status.replace('_', ' ').toUpperCase()}
              </span>
            </div>

            <div className="modal-body">
              <div className="detail-section">
                <h3>Shipment Information</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <strong>Order ID:</strong>
                    <span>{selectedShipment.shipment.order_id}</span>
                  </div>
                  <div className="detail-item">
                    <strong>Carrier:</strong>
                    <span>{selectedShipment.shipment.carrier}</span>
                  </div>
                  <div className="detail-item">
                    <strong>Tracking #:</strong>
                    <span>{selectedShipment.shipment.tracking_number}</span>
                  </div>
                  <div className="detail-item">
                    <strong>Weight:</strong>
                    <span>{selectedShipment.shipment.weight_lbs} lbs</span>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h3>Current Location</h3>
                <p className="location-name">{selectedShipment.current_location.name}</p>
                <p className="coordinates">
                  {selectedShipment.current_location.latitude.toFixed(4)}, {selectedShipment.current_location.longitude.toFixed(4)}
                </p>
              </div>

              <div className="detail-section">
                <h3>Progress</h3>
                <div className="progress-details">
                  <div className="progress-stat">
                    <span className="label">Completed</span>
                    <span className="value">{selectedShipment.progress.percentage}%</span>
                  </div>
                  <div className="progress-stat">
                    <span className="label">Distance Traveled</span>
                    <span className="value">{selectedShipment.progress.distance_traveled.toFixed(1)} miles</span>
                  </div>
                  <div className="progress-stat">
                    <span className="label">Distance Remaining</span>
                    <span className="value">{selectedShipment.progress.distance_remaining.toFixed(1)} miles</span>
                  </div>
                </div>
              </div>

              {selectedShipment.events && selectedShipment.events.length > 0 && (
                <div className="detail-section">
                  <h3>Tracking Events</h3>
                  <div className="events-timeline">
                    {selectedShipment.events.map((event, index) => (
                      <div key={index} className="event-item">
                        <div className="event-dot"></div>
                        <div className="event-content">
                          <div className="event-header">
                            <strong>{event.event_type.replace('_', ' ').toUpperCase()}</strong>
                            <span className="event-time">{formatDateTime(event.occurred_at)}</span>
                          </div>
                          <p>{event.description}</p>
                          <span className="event-location">{event.location}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default ShipmentTracking;
