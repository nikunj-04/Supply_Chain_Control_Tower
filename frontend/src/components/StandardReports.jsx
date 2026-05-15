import React, { useState } from 'react';
import './StandardReports.css';
import { hasPermission, PERMISSIONS } from '../utils/permissions';

function StandardReports({ data }) {
  const [filterCategory, setFilterCategory] = useState('all');
  const [filterFrequency, setFilterFrequency] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');
  const [runningReports, setRunningReports] = useState(new Set());
  const [reportModal, setReportModal] = useState(null);

  // Get current user for permission checks
  const getCurrentUser = () => {
    const userStr = localStorage.getItem('user');
    return userStr ? JSON.parse(userStr) : null;
  };

  const currentUser = getCurrentUser();
  const canGenerate = currentUser && hasPermission(currentUser, PERMISSIONS.REPORTS_GENERATE);
  const canExport = currentUser && hasPermission(currentUser, PERMISSIONS.REPORTS_EXPORT);
  const canView = currentUser && hasPermission(currentUser, PERMISSIONS.REPORTS_VIEW);

  const handleViewReport = async (report) => {
    if (report.status === 'available') {
      alert('Report not yet generated. Please run the report first.');
      return;
    }

    try {
      // Simulate viewing report data
      setReportModal({
        title: report.report_name,
        id: report.report_id,
        category: report.category,
        records: report.record_count,
        lastRun: report.last_run,
        format: report.format
      });
    } catch (error) {
      console.error('Error viewing report:', error);
      alert('Failed to load report preview');
    }
  };

  const handleDownloadReport = async (report) => {
    if (report.status === 'available') {
      alert('Report not yet generated. Please run the report first.');
      return;
    }

    try {
      // Create a mock file download
      const fileName = `${report.report_id}_${new Date().toISOString().split('T')[0]}.${report.format}`;
      const content = `Report: ${report.report_name}\nGenerated: ${new Date().toLocaleString()}\nRecords: ${report.record_count}\nCategory: ${report.category}`;
      
      const blob = new Blob([content], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = fileName;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Error downloading report:', error);
      alert('Failed to download report');
    }
  };

  const handleRunReport = async (report) => {
    const reportId = report.report_id;
    
    if (runningReports.has(reportId)) {
      return; // Already running
    }

    try {
      setRunningReports(prev => new Set(prev).add(reportId));
      
      // Simulate report generation (2-3 seconds)
      await new Promise(resolve => setTimeout(resolve, 2500));
      
      alert(`Report "${report.report_name}" has been generated successfully!\n\nYou can now view or download it.`);
      
      // In a real app, would refresh the data here
      // For now, just mark as complete
    } catch (error) {
      console.error('Error running report:', error);
      alert('Failed to generate report');
    } finally {
      setRunningReports(prev => {
        const newSet = new Set(prev);
        newSet.delete(reportId);
        return newSet;
      });
    }
  };

  const closeModal = () => {
    setReportModal(null);
  };

  if (!data) {
    return <div className="loading">Loading standard reports...</div>;
  }

  const { summary, reports, categories, timestamp } = data;

  // Filter reports
  const filteredReports = reports.filter(report => {
    const matchesCategory = filterCategory === 'all' || report.category === filterCategory;
    const matchesFrequency = filterFrequency === 'all' || report.frequency === filterFrequency;
    const matchesSearch = searchTerm === '' || 
      report.report_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      report.description.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesCategory && matchesFrequency && matchesSearch;
  });

  const getFrequencyBadgeClass = (frequency) => {
    const map = {
      'daily': 'freq-daily',
      'weekly': 'freq-weekly',
      'monthly': 'freq-monthly',
      'on_demand': 'freq-ondemand'
    };
    return map[frequency] || 'freq-ondemand';
  };

  const getFrequencyLabel = (frequency) => {
    const map = {
      'daily': 'Daily',
      'weekly': 'Weekly',
      'monthly': 'Monthly',
      'on_demand': 'On Demand'
    };
    return map[frequency] || frequency;
  };

  const getCategoryIcon = (category) => {
    const icons = {
      'operational': '⚙️',
      'financial': '💰',
      'inventory': '📦',
      'transportation': '🚚'
    };
    return icons[category] || '📊';
  };

  const formatFileSize = (kb) => {
    if (kb === 0) return 'N/A';
    if (kb < 1024) return `${kb} KB`;
    return `${(kb / 1024).toFixed(1)} MB`;
  };

  const getTimeAgo = (lastRun) => {
    if (!lastRun) return 'Never';
    
    const now = new Date();
    const runDate = new Date(lastRun);
    const diffMs = now - runDate;
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffDays = Math.floor(diffHours / 24);
    
    if (diffHours < 1) return 'Less than 1 hour ago';
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
  };

  return (
    <div className="standard-reports">
      <div className="reports-header">
        <div>
          <h2>Standard Reports</h2>
          <p className="last-updated">
            Last updated: {new Date(timestamp).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <div className="card-icon">📊</div>
          <div className="card-content">
            <div className="card-label">Total Reports</div>
            <div className="card-value">{summary.total_reports}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">✅</div>
          <div className="card-content">
            <div className="card-label">Available</div>
            <div className="card-value">{summary.available_reports}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">📅</div>
          <div className="card-content">
            <div className="card-label">Scheduled</div>
            <div className="card-value">{summary.scheduled_reports}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">🔄</div>
          <div className="card-content">
            <div className="card-label">Run Today</div>
            <div className="card-value">{summary.reports_run_today}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">📥</div>
          <div className="card-content">
            <div className="card-label">Total Records</div>
            <div className="card-value">{summary.total_downloads.toLocaleString()}</div>
          </div>
        </div>
      </div>

      {/* Categories Grid */}
      <div className="categories-section">
        <h3>Report Categories</h3>
        <div className="categories-grid">
          {categories.map((cat, index) => (
            <div key={index} className="category-card">
              <div className="category-icon">{getCategoryIcon(cat.category)}</div>
              <div className="category-details">
                <div className="category-name">{cat.category.charAt(0).toUpperCase() + cat.category.slice(1)}</div>
                <div className="category-count">{cat.count} reports</div>
                <div className="category-description">{cat.description}</div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Filters and Search */}
      <div className="reports-controls">
        <div className="search-box">
          <input
            type="text"
            placeholder="Search reports..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>

        <div className="filter-group">
          <label>Category:</label>
          <select value={filterCategory} onChange={(e) => setFilterCategory(e.target.value)}>
            <option value="all">All Categories</option>
            <option value="operational">Operational</option>
            <option value="financial">Financial</option>
            <option value="inventory">Inventory</option>
            <option value="transportation">Transportation</option>
          </select>
        </div>

        <div className="filter-group">
          <label>Frequency:</label>
          <select value={filterFrequency} onChange={(e) => setFilterFrequency(e.target.value)}>
            <option value="all">All Frequencies</option>
            <option value="daily">Daily</option>
            <option value="weekly">Weekly</option>
            <option value="monthly">Monthly</option>
            <option value="on_demand">On Demand</option>
          </select>
        </div>
      </div>

      {/* Reports Grid */}
      <div className="reports-grid">
        {filteredReports.map((report, index) => (
          <div key={index} className="report-card">
            <div className="report-header">
              <div className="report-icon">{getCategoryIcon(report.category)}</div>
              <div className="report-title-section">
                <div className="report-id">{report.report_id}</div>
                <h4>{report.report_name}</h4>
              </div>
              <span className={`frequency-badge ${getFrequencyBadgeClass(report.frequency)}`}>
                {getFrequencyLabel(report.frequency)}
              </span>
            </div>

            <p className="report-description">{report.description}</p>

            <div className="report-stats">
              <div className="stat-item">
                <span className="stat-label">Category:</span>
                <span className="stat-value">{report.category.charAt(0).toUpperCase() + report.category.slice(1)}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Format:</span>
                <span className="stat-value">{report.format.toUpperCase()}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Records:</span>
                <span className="stat-value">{report.record_count.toLocaleString()}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Size:</span>
                <span className="stat-value">{formatFileSize(report.file_size_kb)}</span>
              </div>
            </div>

            <div className="report-footer">
              <div className="last-run">
                <span className="last-run-label">Last Run:</span>
                <span className="last-run-time">{getTimeAgo(report.last_run)}</span>
              </div>
              <div className="report-actions">
                {canView && (
                  <button 
                    className="btn-view" 
                    disabled={report.status === 'available'}
                    title={report.status === 'available' ? 'Report not yet generated' : 'View report'}
                    onClick={() => handleViewReport(report)}
                  >
                    View
                  </button>
                )}
                {canExport && (
                  <button 
                    className="btn-download"
                    disabled={report.status === 'available'}
                    title={report.status === 'available' ? 'Report not yet generated' : 'Download report'}
                    onClick={() => handleDownloadReport(report)}
                  >
                    Download
                  </button>
                )}
                {canGenerate && (
                  <button 
                    className="btn-run"
                    title="Generate report now"
                    onClick={() => handleRunReport(report)}
                    disabled={runningReports.has(report.report_id)}
                  >
                    {runningReports.has(report.report_id) ? 'Generating...' : 'Run Now'}
                  </button>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {filteredReports.length === 0 && (
        <div className="no-data">No reports match your search criteria.</div>
      )}

      {/* Report Preview Modal */}
      {reportModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>Report Preview: {reportModal.title}</h3>
              <button className="modal-close" onClick={closeModal}>×</button>
            </div>
            <div className="modal-body">
              <div className="report-preview-info">
                <div className="preview-field">
                  <strong>Report ID:</strong> {reportModal.id}
                </div>
                <div className="preview-field">
                  <strong>Category:</strong> {reportModal.category.charAt(0).toUpperCase() + reportModal.category.slice(1)}
                </div>
                <div className="preview-field">
                  <strong>Format:</strong> {reportModal.format.toUpperCase()}
                </div>
                <div className="preview-field">
                  <strong>Total Records:</strong> {reportModal.records.toLocaleString()}
                </div>
                <div className="preview-field">
                  <strong>Last Generated:</strong> {new Date(reportModal.lastRun).toLocaleString()}
                </div>
              </div>
              <div className="preview-message">
                <p>📊 Report preview shows metadata only.</p>
                <p>Click Download to get the full report file.</p>
              </div>
            </div>
            <div className="modal-footer">
              <button className="btn-secondary" onClick={closeModal}>Close</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default StandardReports;
