import React from 'react';
import './KPIDashboard.css';

function KPIDashboard({ data }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'on_target':
        return '#10b981';
      case 'attention':
        return '#f59e0b';
      case 'critical':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'on_target':
        return '●';
      case 'attention':
        return '●';
      case 'critical':
        return '●';
      default:
        return '●';
    }
  };

  return (
    <div className="kpi-dashboard-container">
      <div className="kpi-dashboard-header">
        <h2>KPI Dashboard</h2>
        <div className="kpi-status-bar">
          <div className="kpi-legend">
            <span className="legend-item">
              <span className="legend-dot on-target">●</span> On Target
            </span>
            <span className="legend-item">
              <span className="legend-dot attention">●</span> Attention Needed
            </span>
            <span className="legend-item">
              <span className="legend-dot critical">●</span> Critical
            </span>
          </div>
        </div>
      </div>

      <div className="kpi-cards-grid">
        {data.categories.map((category, index) => (
          <div key={index} className="kpi-card">
            <div className="kpi-card-header">
              <div className="kpi-icon" style={{ backgroundColor: category.icon_color }}>
                {category.icon}
              </div>
              <h3 className="kpi-category-title">{category.title}</h3>
            </div>
            
            <div className="kpi-metrics-list">
              {category.metrics.map((metric, mIndex) => (
                <div key={mIndex} className="kpi-metric-row">
                  <div className="kpi-metric-label">
                    <span 
                      className="kpi-status-dot"
                      style={{ color: getStatusColor(metric.status) }}
                    >
                      {getStatusIcon(metric.status)}
                    </span>
                    <span className="kpi-metric-name">{metric.label}</span>
                  </div>
                  <div 
                    className="kpi-metric-value"
                    style={{ 
                      backgroundColor: metric.status === 'on_target' ? '#d1fae5' : 
                                     metric.status === 'attention' ? '#fef3c7' : 
                                     metric.status === 'critical' ? '#fee2e2' : '#f3f4f6',
                      color: metric.status === 'on_target' ? '#065f46' : 
                             metric.status === 'attention' ? '#92400e' : 
                             metric.status === 'critical' ? '#991b1b' : '#374151'
                    }}
                  >
                    {metric.value}
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default KPIDashboard;
