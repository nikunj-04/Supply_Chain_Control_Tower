import React, { useState } from 'react';
import './ScheduledExports.css';
import { hasPermission, PERMISSIONS } from '../utils/permissions';

function ScheduledExports({ data }) {
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [activeTab, setActiveTab] = useState('schedules'); // schedules, history

  // Get current user for permission checks
  const getCurrentUser = () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  };

  const currentUser = getCurrentUser();
  const canSchedule = currentUser && hasPermission(currentUser, PERMISSIONS.REPORTS_SCHEDULE);
  const canGenerate = currentUser && hasPermission(currentUser, PERMISSIONS.REPORTS_GENERATE);

  if (!data) {
    return <div className="loading">Loading scheduled exports...</div>;
  }

  const { summary, scheduled_exports, recent_history, timestamp } = data;

  // Filter scheduled exports
  const filteredExports = scheduled_exports.filter(exp => {
    const matchesStatus = filterStatus === 'all' || exp.status === filterStatus;
    const matchesType = filterType === 'all' || exp.report_type === filterType;
    return matchesStatus && matchesType;
  });

  const getStatusBadgeClass = (status) => {
    const map = {
      'active': 'status-active',
      'paused': 'status-paused',
      'failed': 'status-failed'
    };
    return map[status] || 'status-active';
  };

  const getStatusLabel = (status) => {
    const map = {
      'active': 'Active',
      'paused': 'Paused',
      'failed': 'Failed'
    };
    return map[status] || status;
  };

  const getScheduleIcon = (scheduleType) => {
    const icons = {
      'daily': '📅',
      'weekly': '📆',
      'monthly': '🗓️',
      'custom': '⚙️'
    };
    return icons[scheduleType] || '📅';
  };

  const getFormatBadgeClass = (format) => {
    const map = {
      'excel': 'format-excel',
      'csv': 'format-csv',
      'pdf': 'format-pdf'
    };
    return map[format] || 'format-excel';
  };

  const getHistoryStatusClass = (status) => {
    const map = {
      'success': 'history-success',
      'failed': 'history-failed',
      'partial': 'history-partial'
    };
    return map[status] || 'history-success';
  };

  const formatDateTime = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getTimeUntilNext = (nextRun) => {
    const now = new Date();
    const next = new Date(nextRun);
    const diffMs = next - now;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffMs < 0) return 'Overdue';
    if (diffHours < 1) return 'Less than 1 hour';
    if (diffHours < 24) return `In ${diffHours} hour${diffHours > 1 ? 's' : ''}`;
    return `In ${diffDays} day${diffDays > 1 ? 's' : ''}`;
  };

  return (
    <div className="scheduled-exports">
      <div className="exports-header">
        <div>
          <h2>Scheduled Exports</h2>
          <p className="last-updated">
            Last updated: {new Date(timestamp).toLocaleString()}
          </p>
        </div>
        {canSchedule && (
          <button className="btn-new-schedule">+ New Schedule</button>
        )}
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <div className="card-icon">📊</div>
          <div className="card-content">
            <div className="card-label">Total Scheduled</div>
            <div className="card-value">{summary.total_scheduled}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">✅</div>
          <div className="card-content">
            <div className="card-label">Active Schedules</div>
            <div className="card-value">{summary.active_schedules}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">⏸️</div>
          <div className="card-content">
            <div className="card-label">Paused</div>
            <div className="card-value">{summary.paused_schedules}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">📤</div>
          <div className="card-content">
            <div className="card-label">Exports This Week</div>
            <div className="card-value">{summary.exports_this_week}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">👥</div>
          <div className="card-content">
            <div className="card-label">Recipients</div>
            <div className="card-value">{summary.total_recipients}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">📈</div>
          <div className="card-content">
            <div className="card-label">Avg Success Rate</div>
            <div className="card-value">{summary.average_success_rate}%</div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button 
          className={`tab-btn ${activeTab === 'schedules' ? 'active' : ''}`}
          onClick={() => setActiveTab('schedules')}
        >
          📅 Scheduled Exports ({scheduled_exports.length})
        </button>
        <button 
          className={`tab-btn ${activeTab === 'history' ? 'active' : ''}`}
          onClick={() => setActiveTab('history')}
        >
          📜 Execution History ({recent_history.length})
        </button>
      </div>

      {/* Schedules Tab */}
      {activeTab === 'schedules' && (
        <div className="schedules-section">
          {/* Filters */}
          <div className="filters-bar">
            <div className="filter-group">
              <label>Status:</label>
              <select value={filterStatus} onChange={(e) => setFilterStatus(e.target.value)}>
                <option value="all">All Status</option>
                <option value="active">Active</option>
                <option value="paused">Paused</option>
                <option value="failed">Failed</option>
              </select>
            </div>

            <div className="filter-group">
              <label>Type:</label>
              <select value={filterType} onChange={(e) => setFilterType(e.target.value)}>
                <option value="all">All Types</option>
                <option value="standard">Standard Reports</option>
                <option value="custom">Custom Reports</option>
              </select>
            </div>
          </div>

          {/* Schedules Grid */}
          <div className="schedules-grid">
            {filteredExports.map((exp, index) => (
              <div key={index} className="schedule-card">
                <div className="schedule-header">
                  <div className="schedule-title-section">
                    <div className="schedule-icon">{getScheduleIcon(exp.schedule_type)}</div>
                    <div>
                      <h4>{exp.export_name}</h4>
                      <div className="schedule-id">{exp.export_id}</div>
                    </div>
                  </div>
                  <div className="schedule-badges">
                    <span className={`status-badge ${getStatusBadgeClass(exp.status)}`}>
                      {getStatusLabel(exp.status)}
                    </span>
                    <span className={`format-badge ${getFormatBadgeClass(exp.format)}`}>
                      {exp.format.toUpperCase()}
                    </span>
                  </div>
                </div>

                <div className="schedule-details">
                  <div className="detail-row">
                    <span className="detail-label">Report Type:</span>
                    <span className="detail-value">{exp.report_type === 'standard' ? 'Standard Report' : 'Custom Report'}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Schedule:</span>
                    <span className="detail-value">{exp.schedule_type.charAt(0).toUpperCase() + exp.schedule_type.slice(1)} - {exp.frequency}</span>
                  </div>
                  <div className="detail-row">
                    <span className="detail-label">Recipients:</span>
                    <span className="detail-value">{exp.recipients.length} recipient{exp.recipients.length > 1 ? 's' : ''}</span>
                  </div>
                </div>

                <div className="recipients-section">
                  <strong>Email Recipients:</strong>
                  <div className="recipients-list">
                    {exp.recipients.map((email, i) => (
                      <span key={i} className="recipient-chip">{email}</span>
                    ))}
                  </div>
                </div>

                <div className="schedule-stats">
                  <div className="stat-box">
                    <div className="stat-label">Last Run</div>
                    <div className="stat-value">{exp.last_run ? formatDateTime(exp.last_run) : 'Never'}</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-label">Next Run</div>
                    <div className="stat-value highlight">{getTimeUntilNext(exp.next_run)}</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-label">Run Count</div>
                    <div className="stat-value">{exp.run_count}</div>
                  </div>
                  <div className="stat-box">
                    <div className="stat-label">Success Rate</div>
                    <div className="stat-value">{exp.success_rate}%</div>
                  </div>
                </div>

                <div className="schedule-footer">
                  <div className="created-date">
                    Created: {formatDateTime(exp.created_date)}
                  </div>
                  <div className="schedule-actions">
                    {canSchedule && (
                      <>
                        {exp.status === 'active' ? (
                          <button className="btn-pause">⏸️ Pause</button>
                        ) : (
                          <button className="btn-resume">▶️ Resume</button>
                        )}
                      </>
                    )}
                    {canGenerate && (
                      <button className="btn-run-now">▶️ Run Now</button>
                    )}
                    {canSchedule && (
                      <>
                        <button className="btn-edit">✏️ Edit</button>
                        <button className="btn-delete">🗑️ Delete</button>
                      </>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* History Tab */}
      {activeTab === 'history' && (
        <div className="history-section">
          <div className="history-table">
            <table>
              <thead>
                <tr>
                  <th>Export Name</th>
                  <th>Execution Time</th>
                  <th>Status</th>
                  <th>Records</th>
                  <th>File Size</th>
                  <th>Duration</th>
                  <th>Recipients</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {recent_history.map((hist, index) => (
                  <tr key={index}>
                    <td className="export-name-col">{hist.export_name}</td>
                    <td>{formatDateTime(hist.execution_time)}</td>
                    <td>
                      <span className={`history-status ${getHistoryStatusClass(hist.status)}`}>
                        {hist.status.charAt(0).toUpperCase() + hist.status.slice(1)}
                      </span>
                    </td>
                    <td className="numeric-col">{hist.records_exported.toLocaleString()}</td>
                    <td className="numeric-col">{hist.file_size_kb} KB</td>
                    <td className="numeric-col">{hist.duration_seconds}s</td>
                    <td className="numeric-col">{hist.recipients_notified}</td>
                    <td>
                      {hist.error_message ? (
                        <span className="error-message" title={hist.error_message}>
                          ⚠️ Error
                        </span>
                      ) : (
                        <span className="success-message">✓ Success</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default ScheduledExports;
