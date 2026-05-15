import React, { useState } from 'react';
import './CarrierScorecards.css';

function CarrierScorecards({ data }) {
  const [sortField, setSortField] = useState('performance_score');
  const [sortDirection, setSortDirection] = useState('desc');
  const [filterStatus, setFilterStatus] = useState('all');

  if (!data) {
    return <div className="loading">Loading carrier scorecard...</div>;
  }

  const { summary, carriers, trends, timestamp } = data;

  // Filter carriers by status
  const filteredCarriers = carriers.filter(carrier => 
    filterStatus === 'all' || carrier.status === filterStatus
  );

  // Sort carriers
  const sortedCarriers = [...filteredCarriers].sort((a, b) => {
    let aVal = a[sortField];
    let bVal = b[sortField];
    
    if (sortField === 'carrier_name') {
      return sortDirection === 'asc' 
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal);
    }
    
    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
  });

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  const getStatusBadgeClass = (status) => {
    const statusMap = {
      'excellent': 'status-excellent',
      'good': 'status-good',
      'fair': 'status-fair',
      'poor': 'status-poor'
    };
    return statusMap[status] || 'status-fair';
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2
    }).format(value);
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric'
    });
  };

  // Calculate trend average for last 7 days
  const recentTrends = trends.slice(-7);
  const avgRecentOnTime = recentTrends.reduce((sum, t) => sum + t.on_time_rate, 0) / recentTrends.length;

  return (
    <div className="carrier-scorecards">
      <div className="scorecard-header">
        <div>
          <h2>Carrier Performance Scorecard</h2>
          <p className="last-updated">
            Last updated: {new Date(timestamp).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <div className="card-icon">🚚</div>
          <div className="card-content">
            <div className="card-label">Total Carriers</div>
            <div className="card-value">{summary.total_carriers}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">📦</div>
          <div className="card-content">
            <div className="card-label">Total Shipments</div>
            <div className="card-value">{summary.total_shipments.toLocaleString()}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">⏰</div>
          <div className="card-content">
            <div className="card-label">On-Time Rate</div>
            <div className="card-value">{summary.overall_on_time_rate}%</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">💰</div>
          <div className="card-content">
            <div className="card-label">Avg Cost/Shipment</div>
            <div className="card-value">{formatCurrency(summary.avg_cost_per_shipment)}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">🏆</div>
          <div className="card-content">
            <div className="card-label">Best Performer</div>
            <div className="card-value carrier-name">{summary.best_performer}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">⚠️</div>
          <div className="card-content">
            <div className="card-label">Total Exceptions</div>
            <div className="card-value">{summary.total_exceptions}</div>
          </div>
        </div>
      </div>

      {/* Performance Trend Chart */}
      <div className="trend-section">
        <div className="trend-header">
          <h3>30-Day On-Time Delivery Trend</h3>
          <div className="trend-stat">
            7-Day Average: <span className="trend-value">{avgRecentOnTime.toFixed(1)}%</span>
          </div>
        </div>
        <div className="trend-chart">
          {trends.map((trend, index) => {
            const height = Math.max(5, (trend.on_time_rate / 100) * 100);
            const color = trend.on_time_rate >= 95 ? '#4caf50' : 
                         trend.on_time_rate >= 90 ? '#ff9800' : '#f44336';
            
            return (
              <div key={index} className="trend-bar-container">
                <div 
                  className="trend-bar" 
                  style={{ height: `${height}%`, backgroundColor: color }}
                  title={`${formatDate(trend.date)}: ${trend.on_time_rate}% (${trend.shipment_count} shipments)`}
                >
                  <span className="trend-tooltip">
                    {trend.on_time_rate}%
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Carrier Performance Table */}
      <div className="carriers-table-section">
        <div className="table-controls">
          <h3>Carrier Rankings</h3>
          <div className="filter-buttons">
            <button 
              className={filterStatus === 'all' ? 'active' : ''} 
              onClick={() => setFilterStatus('all')}
            >
              All
            </button>
            <button 
              className={filterStatus === 'excellent' ? 'active' : ''} 
              onClick={() => setFilterStatus('excellent')}
            >
              Excellent
            </button>
            <button 
              className={filterStatus === 'good' ? 'active' : ''} 
              onClick={() => setFilterStatus('good')}
            >
              Good
            </button>
            <button 
              className={filterStatus === 'fair' ? 'active' : ''} 
              onClick={() => setFilterStatus('fair')}
            >
              Fair
            </button>
            <button 
              className={filterStatus === 'poor' ? 'active' : ''} 
              onClick={() => setFilterStatus('poor')}
            >
              Poor
            </button>
          </div>
        </div>

        <div className="table-wrapper">
          <table className="carriers-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('carrier_name')} className="sortable">
                  Carrier {sortField === 'carrier_name' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('performance_score')} className="sortable">
                  Score {sortField === 'performance_score' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('total_shipments')} className="sortable">
                  Shipments {sortField === 'total_shipments' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('on_time_rate_pct')} className="sortable">
                  On-Time % {sortField === 'on_time_rate_pct' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('avg_transit_time_hours')} className="sortable">
                  Avg Transit {sortField === 'avg_transit_time_hours' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('cost_per_shipment')} className="sortable">
                  Cost/Ship {sortField === 'cost_per_shipment' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('active_shipments')} className="sortable">
                  Active {sortField === 'active_shipments' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('exceptions')} className="sortable">
                  Exceptions {sortField === 'exceptions' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {sortedCarriers.map((carrier, index) => (
                <tr key={index}>
                  <td className="carrier-name-cell">
                    <strong>{carrier.carrier_name}</strong>
                  </td>
                  <td>
                    <div className="score-cell">
                      <div className="score-bar-mini">
                        <div 
                          className={`score-fill ${getStatusBadgeClass(carrier.status)}`}
                          style={{ width: `${carrier.performance_score}%` }}
                        ></div>
                      </div>
                      <span className="score-value">{carrier.performance_score}</span>
                    </div>
                  </td>
                  <td>{carrier.total_shipments.toLocaleString()}</td>
                  <td>
                    <span className={carrier.on_time_rate_pct >= 95 ? 'rate-excellent' : 
                                   carrier.on_time_rate_pct >= 90 ? 'rate-good' : 'rate-poor'}>
                      {carrier.on_time_rate_pct}%
                    </span>
                  </td>
                  <td>{carrier.avg_transit_time_hours.toFixed(1)}h</td>
                  <td>{formatCurrency(carrier.cost_per_shipment)}</td>
                  <td>{carrier.active_shipments}</td>
                  <td>
                    <span className={carrier.exceptions > 5 ? 'exceptions-high' : ''}>
                      {carrier.exceptions}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${getStatusBadgeClass(carrier.status)}`}>
                      {carrier.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {sortedCarriers.length === 0 && (
          <div className="no-data">No carriers match the selected filter.</div>
        )}
      </div>
    </div>
  );
}

export default CarrierScorecards;
