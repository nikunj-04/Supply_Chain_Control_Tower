import React from 'react';
import './WarehousePerformance.css';

function WarehousePerformance({ data }) {
  if (!data) {
    return <div className="loading">Loading warehouse performance data...</div>;
  }

  const { summary, inventory_metrics, picking_metrics, top_performers, critical_inventory } = data;

  const getStatusBadge = (status) => {
    const statusMap = {
      ok: { label: 'OK', className: 'status-ok' },
      low: { label: 'Low Stock', className: 'status-low' },
      critical: { label: 'Critical', className: 'status-critical' },
      out_of_stock: { label: 'Out of Stock', className: 'status-out' }
    };
    const statusInfo = statusMap[status] || { label: status, className: 'status-default' };
    return <span className={`status-badge ${statusInfo.className}`}>{statusInfo.label}</span>;
  };

  const getPerformanceColor = (value, thresholds) => {
    if (value >= thresholds.good) return 'perf-good';
    if (value >= thresholds.medium) return 'perf-medium';
    return 'perf-poor';
  };

  return (
    <div className="warehouse-performance">
      <div className="performance-header">
        <h2>Warehouse Performance</h2>
        <p className="last-updated">Last Updated: {new Date(data.timestamp).toLocaleString()}</p>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card picks">
          <div className="card-icon">📦</div>
          <div className="card-content">
            <div className="card-value">{summary.picks_completed_today}</div>
            <div className="card-label">Picks Completed Today</div>
            <div className="card-sublabel">{summary.pick_completion_rate.toFixed(1)}% completion rate</div>
          </div>
        </div>

        <div className="summary-card efficiency">
          <div className="card-icon">⚡</div>
          <div className="card-content">
            <div className="card-value">{summary.avg_pick_time.toFixed(1)} min</div>
            <div className="card-label">Avg Pick Time</div>
            <div className="card-sublabel">Per task</div>
          </div>
        </div>

        <div className="summary-card accuracy">
          <div className="card-icon">🎯</div>
          <div className="card-content">
            <div className="card-value">{summary.inventory_accuracy.toFixed(1)}%</div>
            <div className="card-label">Inventory Accuracy</div>
            <div className="card-sublabel">{summary.capacity_utilization.toFixed(1)}% capacity</div>
          </div>
        </div>

        <div className="summary-card alerts">
          <div className="card-icon">⚠️</div>
          <div className="card-content">
            <div className="card-value">{summary.items_below_reorder}</div>
            <div className="card-label">Items Below Reorder</div>
            <div className="card-sublabel">Needs attention</div>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="performance-grid">
        {/* Inventory Metrics */}
        <div className="performance-card">
          <h3>Inventory Health</h3>
          <div className="metrics-grid">
            <div className="metric-item">
              <div className="metric-label">Total SKUs</div>
              <div className="metric-value">{inventory_metrics.total_skus.toLocaleString()}</div>
            </div>
            <div className="metric-item">
              <div className="metric-label">Total Quantity</div>
              <div className="metric-value">{inventory_metrics.total_quantity.toLocaleString()}</div>
            </div>
            <div className="metric-item">
              <div className="metric-label">Below Reorder Point</div>
              <div className="metric-value warning">{inventory_metrics.below_reorder_point}</div>
            </div>
            <div className="metric-item">
              <div className="metric-label">Out of Stock</div>
              <div className="metric-value critical">{inventory_metrics.out_of_stock}</div>
            </div>
            <div className="metric-item">
              <div className="metric-label">Inventory Accuracy</div>
              <div className={`metric-value ${getPerformanceColor(inventory_metrics.inventory_accuracy_pct, {good: 98, medium: 95})}`}>
                {inventory_metrics.inventory_accuracy_pct.toFixed(1)}%
              </div>
            </div>
            <div className="metric-item">
              <div className="metric-label">Capacity Utilization</div>
              <div className={`metric-value ${getPerformanceColor(inventory_metrics.capacity_utilization_pct, {good: 70, medium: 50})}`}>
                {inventory_metrics.capacity_utilization_pct.toFixed(1)}%
              </div>
            </div>
          </div>
        </div>

        {/* Picking Metrics */}
        <div className="performance-card">
          <h3>Picking Performance</h3>
          <div className="metrics-grid">
            <div className="metric-item">
              <div className="metric-label">Total Tasks Today</div>
              <div className="metric-value">{picking_metrics.total_tasks_today}</div>
            </div>
            <div className="metric-item">
              <div className="metric-label">Completed</div>
              <div className="metric-value success">{picking_metrics.completed_today}</div>
            </div>
            <div className="metric-item">
              <div className="metric-label">Pending</div>
              <div className="metric-value">{picking_metrics.pending}</div>
            </div>
            <div className="metric-item">
              <div className="metric-label">Delayed</div>
              <div className="metric-value warning">{picking_metrics.delayed}</div>
            </div>
            <div className="metric-item">
              <div className="metric-label">Completion Rate</div>
              <div className={`metric-value ${getPerformanceColor(picking_metrics.completion_rate_pct, {good: 95, medium: 85})}`}>
                {picking_metrics.completion_rate_pct.toFixed(1)}%
              </div>
            </div>
            <div className="metric-item">
              <div className="metric-label">Avg Pick Time</div>
              <div className="metric-value">{picking_metrics.avg_pick_time_minutes.toFixed(1)} min</div>
            </div>
          </div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="details-grid">
        {/* Top Performers */}
        <div className="performance-card">
          <h3>🏆 Top Performers</h3>
          {top_performers.length > 0 ? (
            <div className="performers-list">
              {top_performers.map((performer, index) => (
                <div key={performer.picker_name} className={`performer-item ${index === 0 ? 'top-performer' : ''}`}>
                  <div className="performer-rank">{index + 1}</div>
                  <div className="performer-details">
                    <div className="performer-name">{performer.picker_name}</div>
                    <div className="performer-stats">
                      {performer.picks_completed} picks • {performer.avg_time_minutes.toFixed(1)} min avg
                    </div>
                  </div>
                  {index === 0 && <div className="performer-badge">⭐ Best</div>}
                </div>
              ))}
            </div>
          ) : (
            <div className="no-data">No picker data available</div>
          )}
        </div>

        {/* Critical Inventory */}
        <div className="performance-card critical-card">
          <h3>⚠️ Critical Inventory</h3>
          {critical_inventory.length > 0 ? (
            <div className="critical-list">
              {critical_inventory.map(item => (
                <div key={item.sku} className="critical-item">
                  <div className="critical-header">
                    <div className="critical-sku">
                      <span className="sku-code">{item.sku}</span>
                      {getStatusBadge(item.status)}
                    </div>
                    <div className="critical-quantity">
                      {item.quantity_available} / {item.reorder_point}
                    </div>
                  </div>
                  <div className="critical-product">{item.product_name}</div>
                  <div className="critical-location">Location: {item.location}</div>
                </div>
              ))}
            </div>
          ) : (
            <div className="no-data">All inventory levels healthy</div>
          )}
        </div>
      </div>

      {/* Performance Indicator */}
      <div className="performance-card">
        <h3>Overall Performance Score</h3>
        <div className="performance-score">
          <div className="score-item">
            <div className="score-label">Picking Efficiency</div>
            <div className="score-bar-container">
              <div 
                className={`score-bar ${getPerformanceColor(summary.pick_completion_rate, {good: 95, medium: 85})}`}
                style={{ width: `${summary.pick_completion_rate}%` }}
              ></div>
            </div>
            <div className="score-value">{summary.pick_completion_rate.toFixed(1)}%</div>
          </div>
          <div className="score-item">
            <div className="score-label">Inventory Accuracy</div>
            <div className="score-bar-container">
              <div 
                className={`score-bar ${getPerformanceColor(summary.inventory_accuracy, {good: 98, medium: 95})}`}
                style={{ width: `${summary.inventory_accuracy}%` }}
              ></div>
            </div>
            <div className="score-value">{summary.inventory_accuracy.toFixed(1)}%</div>
          </div>
          <div className="score-item">
            <div className="score-label">Capacity Utilization</div>
            <div className="score-bar-container">
              <div 
                className={`score-bar ${getPerformanceColor(summary.capacity_utilization, {good: 70, medium: 50})}`}
                style={{ width: `${summary.capacity_utilization}%` }}
              ></div>
            </div>
            <div className="score-value">{summary.capacity_utilization.toFixed(1)}%</div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default WarehousePerformance;
