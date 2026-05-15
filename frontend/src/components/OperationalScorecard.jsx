import React from 'react';
import './OperationalScorecard.css';

function OperationalScorecard({ data }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'good':
        return '#10b981';
      case 'warning':
        return '#f59e0b';
      case 'critical':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const getSystemStatusColor = (status) => {
    switch (status) {
      case 'healthy':
        return '#10b981';
      case 'warning':
        return '#f59e0b';
      case 'critical':
        return '#ef4444';
      default:
        return '#6b7280';
    }
  };

  const getTrendIcon = (trend) => {
    switch (trend) {
      case 'up':
        return '↑';
      case 'down':
        return '↓';
      case 'stable':
        return '→';
      default:
        return '→';
    }
  };

  return (
    <div className="scorecard-container">
      <div className="scorecard-header">
        <h2>Operational Scorecard</h2>
        <div className="summary-badges">
          <span className="badge badge-success">
            {data.summary.healthy} Healthy
          </span>
          <span className="badge badge-warning">
            {data.summary.warning} Warning
          </span>
          <span className="badge badge-critical">
            {data.summary.critical} Critical
          </span>
        </div>
      </div>

      <div className="systems-grid">
        {data.systems.map((system, index) => (
          <div key={index} className="system-card">
            <div className="system-header">
              <h3 className="system-name">{system.system_name}</h3>
              <span
                className="system-status"
                style={{ backgroundColor: getSystemStatusColor(system.overall_status) }}
              >
                {system.overall_status}
              </span>
            </div>

            <div className="metrics-list">
              {system.metrics.map((metric, mIndex) => (
                <div key={mIndex} className="metric-item">
                  <div className="metric-header">
                    <span className="metric-name">{metric.name}</span>
                    <span
                      className="metric-status-dot"
                      style={{ backgroundColor: getStatusColor(metric.status) }}
                    />
                  </div>
                  <div className="metric-value-row">
                    <span className="metric-value">
                      {metric.value}
                      <span className="metric-unit">{metric.unit}</span>
                    </span>
                    <span className="metric-trend">
                      {getTrendIcon(metric.trend)}
                    </span>
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

export default OperationalScorecard;
