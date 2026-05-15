import React, { useState } from 'react';
import './InventoryOptimization.css';

function InventoryOptimization({ data }) {
  const [sortField, setSortField] = useState('status');
  const [sortDirection, setSortDirection] = useState('asc');
  const [filterStatus, setFilterStatus] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 15;

  if (!data) {
    return <div className="loading">Loading inventory optimization...</div>;
  }

  const { summary, items, turnover_categories, abc_analysis, timestamp } = data;

  // Filter items by status
  const filteredItems = items.filter(item => 
    filterStatus === 'all' || item.status === filterStatus
  );

  // Sort items
  const sortedItems = [...filteredItems].sort((a, b) => {
    let aVal = a[sortField];
    let bVal = b[sortField];
    
    if (typeof aVal === 'string') {
      return sortDirection === 'asc' 
        ? aVal.localeCompare(bVal)
        : bVal.localeCompare(aVal);
    }
    
    return sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
  });

  // Pagination
  const totalPages = Math.ceil(sortedItems.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedItems = sortedItems.slice(startIndex, startIndex + itemsPerPage);

  const handleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const getStatusBadgeClass = (status) => {
    const statusMap = {
      'optimal': 'status-optimal',
      'overstocked': 'status-overstocked',
      'understocked': 'status-understocked',
      'critical': 'status-critical'
    };
    return statusMap[status] || 'status-optimal';
  };

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(value);
  };

  return (
    <div className="inventory-optimization">
      <div className="optimization-header">
        <div>
          <h2>Inventory Optimization</h2>
          <p className="last-updated">
            Last updated: {new Date(timestamp).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card">
          <div className="card-icon">📦</div>
          <div className="card-content">
            <div className="card-label">Total SKUs</div>
            <div className="card-value">{summary.total_skus}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">💰</div>
          <div className="card-content">
            <div className="card-label">Total Value</div>
            <div className="card-value">{formatCurrency(summary.total_value)}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">🔄</div>
          <div className="card-content">
            <div className="card-label">Avg Turnover</div>
            <div className="card-value">{summary.avg_turnover_rate}x</div>
          </div>
        </div>

        <div className="summary-card optimal">
          <div className="card-icon">✅</div>
          <div className="card-content">
            <div className="card-label">Optimal</div>
            <div className="card-value">{summary.optimal_items}</div>
          </div>
        </div>

        <div className="summary-card overstocked">
          <div className="card-icon">📈</div>
          <div className="card-content">
            <div className="card-label">Overstocked</div>
            <div className="card-value">{summary.overstocked_items}</div>
          </div>
        </div>

        <div className="summary-card understocked">
          <div className="card-icon">📉</div>
          <div className="card-content">
            <div className="card-label">Understocked</div>
            <div className="card-value">{summary.understocked_items}</div>
          </div>
        </div>

        <div className="summary-card critical">
          <div className="card-icon">⚠️</div>
          <div className="card-content">
            <div className="card-label">Critical</div>
            <div className="card-value">{summary.critical_items}</div>
          </div>
        </div>

        <div className="summary-card">
          <div className="card-icon">💵</div>
          <div className="card-content">
            <div className="card-label">Holding Cost</div>
            <div className="card-value">{formatCurrency(summary.total_holding_cost)}/mo</div>
          </div>
        </div>

        <div className="summary-card savings">
          <div className="card-icon">💡</div>
          <div className="card-content">
            <div className="card-label">Potential Savings</div>
            <div className="card-value">{formatCurrency(summary.potential_savings)}/mo</div>
          </div>
        </div>
      </div>

      {/* Analysis Grid */}
      <div className="analysis-grid">
        {/* Turnover Categories */}
        <div className="analysis-card">
          <h3>Inventory Turnover Analysis</h3>
          <div className="turnover-breakdown">
            {turnover_categories.map((category, index) => (
              <div key={index} className="turnover-item">
                <div className="turnover-header">
                  <span className="turnover-label">{category.category}</span>
                  <span className="turnover-stats">
                    {category.count} items ({category.percentage}%) | Avg: {category.avg_turnover}x
                  </span>
                </div>
                <div className="turnover-bar-container">
                  <div 
                    className="turnover-bar" 
                    style={{ 
                      width: `${category.percentage}%`,
                      backgroundColor: index === 0 ? '#4caf50' : 
                                     index === 1 ? '#2196f3' : 
                                     index === 2 ? '#ff9800' : '#f44336'
                    }}
                  ></div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* ABC Analysis */}
        <div className="analysis-card">
          <h3>ABC Classification</h3>
          <div className="abc-breakdown">
            {abc_analysis.map((item, index) => (
              <div key={index} className="abc-item">
                <div className="abc-category">{item.category}</div>
                <div className="abc-details">
                  <div className="abc-info">
                    <div className="abc-count">{item.sku_count} SKUs</div>
                    <div className="abc-value">{item.value_percentage}% of value</div>
                  </div>
                  <div className="abc-description">{item.description}</div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Inventory Items Table */}
      <div className="items-table-section">
        <div className="table-controls">
          <h3>Inventory Items Analysis</h3>
          <div className="filter-buttons">
            <button 
              className={filterStatus === 'all' ? 'active' : ''} 
              onClick={() => { setFilterStatus('all'); setCurrentPage(1); }}
            >
              All
            </button>
            <button 
              className={filterStatus === 'critical' ? 'active' : ''} 
              onClick={() => { setFilterStatus('critical'); setCurrentPage(1); }}
            >
              Critical
            </button>
            <button 
              className={filterStatus === 'understocked' ? 'active' : ''} 
              onClick={() => { setFilterStatus('understocked'); setCurrentPage(1); }}
            >
              Understocked
            </button>
            <button 
              className={filterStatus === 'overstocked' ? 'active' : ''} 
              onClick={() => { setFilterStatus('overstocked'); setCurrentPage(1); }}
            >
              Overstocked
            </button>
            <button 
              className={filterStatus === 'optimal' ? 'active' : ''} 
              onClick={() => { setFilterStatus('optimal'); setCurrentPage(1); }}
            >
              Optimal
            </button>
          </div>
        </div>

        <div className="table-wrapper">
          <table className="items-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('sku')} className="sortable">
                  SKU {sortField === 'sku' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('product_name')} className="sortable">
                  Product {sortField === 'product_name' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('quantity_available')} className="sortable">
                  Available {sortField === 'quantity_available' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('days_of_supply')} className="sortable">
                  Days Supply {sortField === 'days_of_supply' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('turnover_rate')} className="sortable">
                  Turnover {sortField === 'turnover_rate' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('holding_cost_monthly')} className="sortable">
                  Holding Cost {sortField === 'holding_cost_monthly' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th onClick={() => handleSort('status')} className="sortable">
                  Status {sortField === 'status' && (sortDirection === 'asc' ? '↑' : '↓')}
                </th>
                <th>Recommendation</th>
              </tr>
            </thead>
            <tbody>
              {paginatedItems.map((item, index) => (
                <tr key={index}>
                  <td className="sku-cell">
                    <code>{item.sku}</code>
                  </td>
                  <td className="product-cell">{item.product_name}</td>
                  <td>{item.quantity_available}/{item.quantity_on_hand}</td>
                  <td>
                    <span className={item.days_of_supply < 30 ? 'days-low' : 
                                   item.days_of_supply > 90 ? 'days-high' : ''}>
                      {item.days_of_supply}
                    </span>
                  </td>
                  <td>{item.turnover_rate}x</td>
                  <td>{formatCurrency(item.holding_cost_monthly)}</td>
                  <td>
                    <span className={`status-badge ${getStatusBadgeClass(item.status)}`}>
                      {item.status}
                    </span>
                  </td>
                  <td className="recommendation-cell">{item.recommendation}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Pagination */}
        {totalPages > 1 && (
          <div className="pagination">
            <button 
              onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
              disabled={currentPage === 1}
            >
              Previous
            </button>
            <span className="page-info">
              Page {currentPage} of {totalPages} ({sortedItems.length} items)
            </span>
            <button 
              onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage === totalPages}
            >
              Next
            </button>
          </div>
        )}

        {sortedItems.length === 0 && (
          <div className="no-data">No items match the selected filter.</div>
        )}
      </div>
    </div>
  );
}

export default InventoryOptimization;
