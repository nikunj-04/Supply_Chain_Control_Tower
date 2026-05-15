import React, { useState } from 'react';
import './CustomReports.css';
import { hasPermission, PERMISSIONS } from '../utils/permissions';

function CustomReports({ data }) {
  const [selectedDataSource, setSelectedDataSource] = useState('all');
  const [selectedFields, setSelectedFields] = useState([]);
  const [filterTerm, setFilterTerm] = useState('');
  const [activeTab, setActiveTab] = useState('builder'); // builder, saved

  // Get current user for permission checks
  const getCurrentUser = () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  };

  const currentUser = getCurrentUser();
  const canCreateCustom = currentUser && hasPermission(currentUser, PERMISSIONS.REPORTS_CUSTOM);
  const canGenerate = currentUser && hasPermission(currentUser, PERMISSIONS.REPORTS_GENERATE);

  if (!data) {
    return <div className="loading">Loading custom reports...</div>;
  }

  const { summary, data_sources, available_fields, saved_reports, timestamp } = data;

  // Filter fields based on selected data source
  const filteredFields = available_fields.filter(field => {
    const matchesSource = selectedDataSource === 'all' || field.source === selectedDataSource;
    const matchesFilter = filterTerm === '' || 
      field.field_name.toLowerCase().includes(filterTerm.toLowerCase()) ||
      field.description.toLowerCase().includes(filterTerm.toLowerCase());
    return matchesSource && matchesFilter;
  });

  const toggleFieldSelection = (fieldId) => {
    setSelectedFields(prev => {
      if (prev.includes(fieldId)) {
        return prev.filter(id => id !== fieldId);
      } else {
        return [...prev, fieldId];
      }
    });
  };

  const getFormatBadgeClass = (format) => {
    const map = {
      'excel': 'format-excel',
      'csv': 'format-csv',
      'pdf': 'format-pdf'
    };
    return map[format] || 'format-excel';
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <div className="custom-reports">
      <div className="reports-header">
        <div>
          <h2>Custom Report Builder</h2>
          <p className="last-updated">
            Last updated: {new Date(timestamp).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <div className="card-icon">💾</div>
          <div className="card-content">
            <div className="card-label">Saved Reports</div>
            <div className="card-value">{summary.total_saved_reports}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">🗄️</div>
          <div className="card-content">
            <div className="card-label">Data Sources</div>
            <div className="card-value">{summary.total_data_sources}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">▶️</div>
          <div className="card-content">
            <div className="card-label">Run This Week</div>
            <div className="card-value">{summary.reports_run_this_week}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">📤</div>
          <div className="card-content">
            <div className="card-label">Records Exported</div>
            <div className="card-value">{summary.total_records_exported.toLocaleString()}</div>
          </div>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button 
          className={`tab-btn ${activeTab === 'builder' ? 'active' : ''}`}
          onClick={() => setActiveTab('builder')}
        >
          🔧 Report Builder
        </button>
        <button 
          className={`tab-btn ${activeTab === 'saved' ? 'active' : ''}`}
          onClick={() => setActiveTab('saved')}
        >
          💾 Saved Reports ({saved_reports.length})
        </button>
      </div>

      {/* Report Builder Tab */}
      {activeTab === 'builder' && (
        <div className="builder-section">
          <div className="builder-layout">
            {/* Left Panel: Data Sources */}
            <div className="builder-panel data-sources-panel">
              <h3>📂 Data Sources</h3>
              <div className="data-source-list">
                <div 
                  className={`data-source-item ${selectedDataSource === 'all' ? 'selected' : ''}`}
                  onClick={() => setSelectedDataSource('all')}
                >
                  <div className="source-name">All Sources</div>
                  <div className="source-count">
                    {data_sources.reduce((sum, ds) => sum + ds.available_fields, 0)} fields
                  </div>
                </div>
                {data_sources.map((source, index) => (
                  <div 
                    key={index}
                    className={`data-source-item ${selectedDataSource === source.source_name ? 'selected' : ''}`}
                    onClick={() => setSelectedDataSource(source.source_name)}
                  >
                    <div className="source-header">
                      <div className="source-name">{source.source_name}</div>
                      <span className="source-badge">{source.source_type}</span>
                    </div>
                    <div className="source-description">{source.description}</div>
                    <div className="source-stats">
                      <span>{source.available_fields} fields</span>
                      <span>{source.record_count.toLocaleString()} records</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Middle Panel: Available Fields */}
            <div className="builder-panel fields-panel">
              <div className="panel-header">
                <h3>📋 Available Fields</h3>
                <input
                  type="text"
                  className="field-search"
                  placeholder="Search fields..."
                  value={filterTerm}
                  onChange={(e) => setFilterTerm(e.target.value)}
                />
              </div>
              <div className="fields-list">
                {filteredFields.map((field, index) => (
                  <div 
                    key={index}
                    className={`field-item ${selectedFields.includes(field.field_id) ? 'selected' : ''}`}
                    onClick={() => toggleFieldSelection(field.field_id)}
                  >
                    <div className="field-checkbox">
                      <input 
                        type="checkbox" 
                        checked={selectedFields.includes(field.field_id)}
                        readOnly
                      />
                    </div>
                    <div className="field-details">
                      <div className="field-name">{field.field_name}</div>
                      <div className="field-meta">
                        <span className={`field-type type-${field.field_type}`}>
                          {field.field_type}
                        </span>
                        <span className="field-source">{field.source}</span>
                      </div>
                      <div className="field-description">{field.description}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right Panel: Report Configuration */}
            <div className="builder-panel config-panel">
              <h3>⚙️ Report Configuration</h3>
              
              <div className="config-section">
                <label>Report Name</label>
                <input type="text" placeholder="Enter report name..." />
              </div>

              <div className="config-section">
                <label>Selected Fields ({selectedFields.length})</label>
                <div className="selected-fields-list">
                  {selectedFields.length === 0 ? (
                    <div className="empty-state">No fields selected</div>
                  ) : (
                    selectedFields.map(fieldId => {
                      const field = available_fields.find(f => f.field_id === fieldId);
                      return field ? (
                        <div key={fieldId} className="selected-field-chip">
                          {field.field_name}
                          <button 
                            className="remove-field"
                            onClick={() => toggleFieldSelection(fieldId)}
                          >
                            ×
                          </button>
                        </div>
                      ) : null;
                    })
                  )}
                </div>
              </div>

              <div className="config-section">
                <label>Export Format</label>
                <select>
                  <option value="excel">Excel (.xlsx)</option>
                  <option value="csv">CSV (.csv)</option>
                  <option value="pdf">PDF (.pdf)</option>
                </select>
              </div>

              <div className="config-section">
                <label>Date Range</label>
                <select>
                  <option value="today">Today</option>
                  <option value="last_7_days">Last 7 Days</option>
                  <option value="last_30_days">Last 30 Days</option>
                  <option value="last_90_days">Last 90 Days</option>
                  <option value="custom">Custom Range</option>
                </select>
              </div>

              <div className="config-actions">
                {canCreateCustom && (
                  <>
                    <button className="btn-preview" disabled={selectedFields.length === 0}>
                      👁️ Preview
                    </button>
                    <button className="btn-save" disabled={selectedFields.length === 0}>
                      💾 Save Report
                    </button>
                  </>
                )}
                {canGenerate && (
                  <button className="btn-run" disabled={selectedFields.length === 0}>
                    ▶️ Run Now
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Saved Reports Tab */}
      {activeTab === 'saved' && (
        <div className="saved-reports-section">
          <div className="saved-reports-grid">
            {saved_reports.map((report, index) => (
              <div key={index} className="saved-report-card">
                <div className="report-card-header">
                  <h4>{report.report_name}</h4>
                  <span className={`format-badge ${getFormatBadgeClass(report.format)}`}>
                    {report.format.toUpperCase()}
                  </span>
                </div>

                <div className="report-card-meta">
                  <div className="meta-item">
                    <span className="meta-label">Created by:</span>
                    <span className="meta-value">{report.created_by}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Created:</span>
                    <span className="meta-value">{formatDate(report.created_date)}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Last Modified:</span>
                    <span className="meta-value">{formatDate(report.last_modified)}</span>
                  </div>
                  <div className="meta-item">
                    <span className="meta-label">Run Count:</span>
                    <span className="meta-value">{report.run_count} times</span>
                  </div>
                </div>

                <div className="report-card-details">
                  <div className="detail-section">
                    <strong>Data Sources ({report.data_sources.length}):</strong>
                    <div className="chip-list">
                      {report.data_sources.map((ds, i) => (
                        <span key={i} className="chip">{ds}</span>
                      ))}
                    </div>
                  </div>

                  <div className="detail-section">
                    <strong>Selected Fields ({report.selected_fields.length}):</strong>
                    <div className="chip-list">
                      {report.selected_fields.map((field, i) => (
                        <span key={i} className="chip">{field}</span>
                      ))}
                    </div>
                  </div>

                  {report.filters.length > 0 && (
                    <div className="detail-section">
                      <strong>Filters ({report.filters.length}):</strong>
                      <div className="filters-list">
                        {report.filters.map((filter, i) => (
                          <div key={i} className="filter-item">
                            {filter.field} {filter.operator} {filter.value}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <div className="report-card-footer">
                  {report.is_scheduled && (
                    <span className="scheduled-badge">📅 Scheduled</span>
                  )}
                  <div className="report-actions">
                    {canCreateCustom && (
                      <>
                        <button className="btn-edit">✏️ Edit</button>
                        <button className="btn-delete">🗑️ Delete</button>
                      </>
                    )}
                    {canGenerate && (
                      <button className="btn-run">▶️ Run</button>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default CustomReports;
