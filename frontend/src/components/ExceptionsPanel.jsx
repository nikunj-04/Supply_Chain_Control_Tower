import React, { useState } from 'react';
import './ExceptionsPanel.css';

function ExceptionsPanel({ data }) {
  const [filter, setFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 4;

  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'critical':
        return '#ef4444';
      case 'high':
        return '#f59e0b';
      case 'medium':
        return '#3b82f6';
      case 'low':
        return '#10b981';
      default:
        return '#6b7280';
    }
  };

  const getSeverityIcon = (severity) => {
    switch (severity) {
      case 'critical':
        return '🔴';
      case 'high':
        return '🟠';
      case 'medium':
        return '🟡';
      case 'low':
        return '🟢';
      default:
        return '⚪';
    }
  };

  const formatDateTime = (dateString) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const filteredExceptions = filter === 'all'
    ? data.exceptions
    : data.exceptions.filter(exc => exc.severity === filter);

  // Pagination logic
  const totalPages = Math.ceil(filteredExceptions.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentExceptions = filteredExceptions.slice(startIndex, endIndex);

  // Reset to page 1 when filter changes
  const handleFilterChange = (newFilter) => {
    setFilter(newFilter);
    setCurrentPage(1);
  };

  const handlePageChange = (page) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="exceptions-container">
      <div className="exceptions-header">
        <h2>Exceptions & Early Warnings</h2>
        <div className="summary-stats">
          <div className="stat-item">
            <span className="stat-label">Total</span>
            <span className="stat-value">{data.summary.total}</span>
          </div>
          <div className="stat-item critical">
            <span className="stat-label">Critical</span>
            <span className="stat-value">{data.summary.critical}</span>
          </div>
          <div className="stat-item high">
            <span className="stat-label">High</span>
            <span className="stat-value">{data.summary.high}</span>
          </div>
          <div className="stat-item medium">
            <span className="stat-label">Medium</span>
            <span className="stat-value">{data.summary.medium}</span>
          </div>
          <div className="stat-item low">
            <span className="stat-label">Low</span>
            <span className="stat-value">{data.summary.low}</span>
          </div>
        </div>
      </div>

      <div className="filter-bar">
        <div className="filter-buttons">
          <button
            className={`filter-button ${filter === 'all' ? 'active' : ''}`}
            onClick={() => handleFilterChange('all')}
          >
            All ({data.summary.total})
          </button>
          <button
            className={`filter-button ${filter === 'critical' ? 'active' : ''}`}
            onClick={() => handleFilterChange('critical')}
          >
            Critical ({data.summary.critical})
          </button>
          <button
            className={`filter-button ${filter === 'high' ? 'active' : ''}`}
            onClick={() => handleFilterChange('high')}
          >
            High ({data.summary.high})
          </button>
          <button
            className={`filter-button ${filter === 'medium' ? 'active' : ''}`}
            onClick={() => handleFilterChange('medium')}
          >
            Medium ({data.summary.medium})
          </button>
          <button
            className={`filter-button ${filter === 'low' ? 'active' : ''}`}
            onClick={() => handleFilterChange('low')}
          >
            Low ({data.summary.low})
          </button>
        </div>
      </div>

      <div className="exceptions-list">
        {filteredExceptions.length === 0 ? (
          <div className="no-exceptions">
            <p>✅ No exceptions found for this filter</p>
          </div>
        ) : (
          currentExceptions.map((exception, index) => (
            <div
              key={index}
              className="exception-card"
              style={{ borderLeftColor: getSeverityColor(exception.severity) }}
            >
              <div className="exception-header">
                <div className="exception-title-row">
                  <span className="exception-icon">
                    {getSeverityIcon(exception.severity)}
                  </span>
                  <h3 className="exception-title">{exception.title}</h3>
                </div>
                <div className="exception-meta">
                  <span
                    className="severity-badge"
                    style={{ backgroundColor: getSeverityColor(exception.severity) }}
                  >
                    {exception.severity}
                  </span>
                  <span className="system-badge">{exception.system}</span>
                  <span className="category-badge">{exception.category}</span>
                </div>
              </div>

              <p className="exception-description">{exception.description}</p>

              {exception.recommended_action && (
                <div className="recommended-action">
                  <strong>Recommended Action:</strong>
                  <p>{exception.recommended_action}</p>
                </div>
              )}

              <div className="exception-footer">
                <span className="exception-entity">
                  Entity: <strong>{exception.affected_entity}</strong>
                </span>
                <span className="exception-time">
                  {formatDateTime(exception.created_at)}
                </span>
              </div>
            </div>
          ))
        )}
      </div>

      {filteredExceptions.length > 0 && totalPages > 1 && (
        <div className="pagination">
          <button
            className="pagination-button"
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
          >
            ← Previous
          </button>
          
          <div className="pagination-numbers">
            {Array.from({ length: totalPages }, (_, i) => i + 1).map((page) => (
              <button
                key={page}
                className={`pagination-number ${currentPage === page ? 'active' : ''}`}
                onClick={() => handlePageChange(page)}
              >
                {page}
              </button>
            ))}
          </div>

          <button
            className="pagination-button"
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
          >
            Next →
          </button>
        </div>
      )}

      {filteredExceptions.length > 0 && (
        <div className="pagination-info">
          Showing {startIndex + 1}-{Math.min(endIndex, filteredExceptions.length)} of {filteredExceptions.length} exceptions
        </div>
      )}
    </div>
  );
}

export default ExceptionsPanel;
