import React, { useState } from 'react';
import './LaborEfficiency.css';

function LaborEfficiency({ data }) {
  const [sortField, setSortField] = useState('productivity_score');
  const [sortDirection, setSortDirection] = useState('desc');
  const [filterStatus, setFilterStatus] = useState('all');

  if (!data) {
    return <div className="loading">Loading labor efficiency...</div>;
  }

  const { summary, workers, hourly_trends, task_breakdown, timestamp } = data;

  // Filter workers by status
  const filteredWorkers = workers.filter(worker => 
    filterStatus === 'all' || worker.status === filterStatus
  );

  // Sort workers
  const sortedWorkers = [...filteredWorkers].sort((a, b) => {
    let aVal = a[sortField];
    let bVal = b[sortField];
    
    if (sortField === 'worker_name') {
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
      'average': 'status-average',
      'needs_improvement': 'status-poor'
    };
    return statusMap[status] || 'status-average';
  };

  const getStatusLabel = (status) => {
    return status === 'needs_improvement' ? 'Needs Support' : 
           status.charAt(0).toUpperCase() + status.slice(1);
  };

  return (
    <div className="labor-efficiency">
      <div className="efficiency-header">
        <div>
          <h2>Labor Efficiency & Productivity</h2>
          <p className="last-updated">
            Last updated: {new Date(timestamp).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <div className="card-icon">👷</div>
          <div className="card-content">
            <div className="card-label">Active Workers</div>
            <div className="card-value">{summary.total_workers}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">📋</div>
          <div className="card-content">
            <div className="card-label">Tasks Completed</div>
            <div className="card-value">{summary.tasks_completed_today}/{summary.total_tasks_today}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">✅</div>
          <div className="card-content">
            <div className="card-label">Completion Rate</div>
            <div className="card-value">{summary.overall_completion_rate}%</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">📊</div>
          <div className="card-content">
            <div className="card-label">Avg Productivity</div>
            <div className="card-value">{summary.avg_productivity_score}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">⚙️</div>
          <div className="card-content">
            <div className="card-label">Utilization</div>
            <div className="card-value">{summary.labor_utilization_pct}%</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">🏆</div>
          <div className="card-content">
            <div className="card-label">Top Performer</div>
            <div className="card-value worker-name">{summary.top_performer}</div>
          </div>
        </div>
      </div>

      {/* Main Grid */}
      <div className="efficiency-grid">
        {/* Hourly Productivity Trends */}
        <div className="productivity-chart-card">
          <h3>Hourly Productivity Trend</h3>
          <div className="hourly-chart">
            {hourly_trends.map((trend, index) => {
              const maxTasks = Math.max(...hourly_trends.map(t => t.tasks_completed));
              const height = maxTasks > 0 ? (trend.tasks_completed / maxTasks * 100) : 0;
              
              return (
                <div key={index} className="hour-bar-container">
                  <div 
                    className="hour-bar" 
                    style={{ height: `${Math.max(5, height)}%` }}
                    title={`${trend.hour}: ${trend.tasks_completed} tasks, ${trend.avg_time_minutes}min avg, ${trend.worker_count} workers`}
                  >
                    <span className="hour-tooltip">
                      {trend.tasks_completed}
                    </span>
                  </div>
                  <div className="hour-label">{trend.hour}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Task Breakdown */}
        <div className="task-breakdown-card">
          <h3>Task Status Breakdown</h3>
          <div className="task-breakdown">
            {task_breakdown.map((item, index) => {
              const statusColors = {
                'completed': '#4caf50',
                'in_progress': '#2196f3',
                'pending': '#ff9800',
                'delayed': '#f44336'
              };
              
              const statusLabels = {
                'completed': 'Completed',
                'in_progress': 'In Progress',
                'pending': 'Pending',
                'delayed': 'Delayed'
              };
              
              return (
                <div key={index} className="breakdown-item">
                  <div className="breakdown-header">
                    <span className="breakdown-label">{statusLabels[item.status]}</span>
                    <span className="breakdown-count">{item.count} ({item.percentage}%)</span>
                  </div>
                  <div className="breakdown-bar-container">
                    <div 
                      className="breakdown-bar" 
                      style={{ 
                        width: `${item.percentage}%`, 
                        backgroundColor: statusColors[item.status] 
                      }}
                    ></div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* Worker Performance Table */}
      <div className="workers-table-section">
        <div className="table-controls">
          <h3>Worker Performance Rankings</h3>
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
              className={filterStatus === 'average' ? 'active' : ''} 
              onClick={() => setFilterStatus('average')}
            >
              Average
            </button>
            <button 
              className={filterStatus === 'needs_improvement' ? 'active' : ''} 
              onClick={() => setFilterStatus('needs_improvement')}
            >
              Needs Support
            </button>
          </div>
        </div>

        <div className="table-wrapper">
          <table className="workers-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('worker_name')} className="sortable">
                  Worker {sortField === 'worker_name' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('productivity_score')} className="sortable">
                  Score {sortField === 'productivity_score' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('tasks_completed')} className="sortable">
                  Completed {sortField === 'tasks_completed' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('completion_rate_pct')} className="sortable">
                  Rate % {sortField === 'completion_rate_pct' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('avg_time_per_task_minutes')} className="sortable">
                  Avg Time {sortField === 'avg_time_per_task_minutes' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('total_hours_worked')} className="sortable">
                  Hours {sortField === 'total_hours_worked' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('tasks_delayed')} className="sortable">
                  Delayed {sortField === 'tasks_delayed' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {sortedWorkers.map((worker, index) => (
                <tr key={index}>
                  <td className="worker-name-cell">
                    <strong>{worker.worker_name}</strong>
                  </td>
                  <td>
                    <div className="score-cell">
                      <div className="score-bar-mini">
                        <div 
                          className={`score-fill ${getStatusBadgeClass(worker.status)}`}
                          style={{ width: `${worker.productivity_score}%` }}
                        ></div>
                      </div>
                      <span className="score-value">{worker.productivity_score}</span>
                    </div>
                  </td>
                  <td>{worker.tasks_completed}/{worker.tasks_assigned}</td>
                  <td>
                    <span className={worker.completion_rate_pct >= 90 ? 'rate-excellent' : 
                                   worker.completion_rate_pct >= 75 ? 'rate-good' : 'rate-poor'}>
                      {worker.completion_rate_pct}%
                    </span>
                  </td>
                  <td>{worker.avg_time_per_task_minutes.toFixed(1)}m</td>
                  <td>{worker.total_hours_worked.toFixed(1)}h</td>
                  <td>
                    <span className={worker.tasks_delayed > 3 ? 'delayed-high' : ''}>
                      {worker.tasks_delayed}
                    </span>
                  </td>
                  <td>
                    <span className={`status-badge ${getStatusBadgeClass(worker.status)}`}>
                      {getStatusLabel(worker.status)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {sortedWorkers.length === 0 && (
          <div className="no-data">No workers match the selected filter.</div>
        )}
      </div>
    </div>
  );
}

export default LaborEfficiency;
