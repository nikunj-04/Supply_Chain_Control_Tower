import React, { useState } from 'react';
import './ClientProfitability.css';

function ClientProfitability({ data }) {
  const [sortBy, setSortBy] = useState('revenue_ytd');
  const [sortOrder, setSortOrder] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  if (!data) {
    return <div className="loading">Loading client profitability data...</div>;
  }

  const { summary = {}, clients = [] } = data;

  const toNumber = (value, fallback = 0) => {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : fallback;
  };

  const summaryRevenueYtd = toNumber(
    summary.total_revenue_ytd ?? summary.total_revenue_mtd,
    0
  );
  const summaryProfitYtd = toNumber(
    summary.total_profit_ytd ?? summary.total_profit_mtd,
    0
  );
  const summaryAvgMargin = toNumber(summary.avg_margin_pct, 0);

  // Sort clients
  const sortedClients = [...clients].sort((a, b) => {
    const aVal = a[sortBy];
    const bVal = b[sortBy];
    
    // Handle string sorting (for customer_name)
    if (sortBy === 'customer_name') {
      return sortOrder === 'asc' 
        ? (aVal || '').localeCompare(bVal || '')
        : (bVal || '').localeCompare(aVal || '');
    }
    
    // Handle numeric sorting
    const aNum = toNumber(aVal, 0);
    const bNum = toNumber(bVal, 0);
    return sortOrder === 'asc' ? aNum - bNum : bNum - aNum;
  });

  // Pagination
  const totalPages = Math.ceil(sortedClients.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const displayedClients = sortedClients.slice(startIndex, startIndex + itemsPerPage);

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortOrder('desc');
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(toNumber(amount, 0));
  };

  const getMarginColor = (margin) => {
    if (margin >= 35) return 'margin-high';
    if (margin >= 25) return 'margin-medium';
    return 'margin-low';
  };

  const getGrowthBadge = (growth) => {
    const growthValue = toNumber(growth, 0);
    if (growthValue > 0) {
      return <span className="growth-badge positive">↑ {growthValue.toFixed(1)}%</span>;
    } else if (growthValue < 0) {
      return <span className="growth-badge negative">↓ {Math.abs(growthValue).toFixed(1)}%</span>;
    }
    return <span className="growth-badge neutral">→ 0%</span>;
  };

  return (
    <div className="client-profitability">
      <div className="profitability-header">
        <h2>Client Profitability Analysis</h2>
        <p className="last-updated">Last Updated: {new Date(data.timestamp).toLocaleString()}</p>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card revenue">
          <div className="card-icon">💵</div>
          <div className="card-content">
            <div className="card-value">{formatCurrency(summaryRevenueYtd)}</div>
            <div className="card-label">Total Revenue YTD</div>
            <div className="card-count">{toNumber(summary.total_clients, 0)} active clients</div>
          </div>
        </div>

        <div className="summary-card profit">
          <div className="card-icon">📊</div>
          <div className="card-content">
            <div className="card-value">{formatCurrency(summaryProfitYtd)}</div>
            <div className="card-label">Total Profit YTD</div>
            <div className="card-sublabel">{summaryAvgMargin.toFixed(1)}% avg margin</div>
          </div>
        </div>

        <div className="summary-card top-client">
          <div className="card-icon">🏆</div>
          <div className="card-content">
            <div className="card-value-text">{summary.top_revenue_client || 'N/A'}</div>
            <div className="card-label">Top Revenue Client</div>
            <div className="card-sublabel">By YTD revenue</div>
          </div>
        </div>

        <div className="summary-card margin-leader">
          <div className="card-icon">⭐</div>
          <div className="card-content">
            <div className="card-value-text">{summary.top_margin_client || 'N/A'}</div>
            <div className="card-label">Highest Margin</div>
            <div className="card-sublabel">Best profitability</div>
          </div>
        </div>
      </div>

      {/* Client Table */}
      <div className="client-table-container">
        <table className="client-table">
          <thead>
            <tr>
              <th onClick={() => handleSort('customer_name')} className="sortable">
                Client {sortBy === 'customer_name' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('revenue_ytd')} className="sortable">
                Revenue YTD {sortBy === 'revenue_ytd' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('revenue_mtd')} className="sortable">
                Revenue (30D) {sortBy === 'revenue_mtd' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('profit_ytd')} className="sortable">
                Profit YTD {sortBy === 'profit_ytd' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('margin_pct')} className="sortable">
                Margin {sortBy === 'margin_pct' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('orders_ytd')} className="sortable">
                Orders YTD {sortBy === 'orders_ytd' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('avg_order_value')} className="sortable">
                Avg Order {sortBy === 'avg_order_value' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('growth_mom')} className="sortable">
                Growth vs Prior 30D {sortBy === 'growth_mom' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('service_level_pct')} className="sortable">
                Service Level {sortBy === 'service_level_pct' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
              <th onClick={() => handleSort('days_to_pay')} className="sortable">
                Days to Pay {sortBy === 'days_to_pay' && (sortOrder === 'asc' ? '↑' : '↓')}
              </th>
            </tr>
          </thead>
          <tbody>
            {displayedClients.map(client => (
              <tr key={client.customer_id}>
                <td className="client-name">
                  <div className="client-name-text">{client.customer_name}</div>
                  <div className="client-id">{client.customer_id}</div>
                </td>
                <td className="revenue">{formatCurrency(client.revenue_ytd)}</td>
                <td className="revenue">{formatCurrency(client.revenue_mtd)}</td>
                <td className="profit">{formatCurrency(client.profit_ytd)}</td>
                <td>
                  <span className={`margin-badge ${getMarginColor(toNumber(client.margin_pct, 0))}`}>
                    {toNumber(client.margin_pct, 0).toFixed(1)}%
                  </span>
                </td>
                <td>{toNumber(client.orders_ytd, 0)}</td>
                <td>{formatCurrency(client.avg_order_value)}</td>
                <td>{getGrowthBadge(client.growth_mom)}</td>
                <td>
                  <span className={toNumber(client.service_level_pct, 0) >= 95 ? 'service-good' : 'service-warning'}>
                    {toNumber(client.service_level_pct, 0).toFixed(1)}%
                  </span>
                </td>
                <td>
                  <span className={toNumber(client.days_to_pay, 30) <= 30 ? 'payment-good' : 'payment-slow'}>
                    {toNumber(client.days_to_pay, 30)} days
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button 
            onClick={() => setCurrentPage(currentPage - 1)} 
            disabled={currentPage === 1}
          >
            Previous
          </button>
          <span className="page-info">
            Page {currentPage} of {totalPages}
          </span>
          <button 
            onClick={() => setCurrentPage(currentPage + 1)} 
            disabled={currentPage === totalPages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

export default ClientProfitability;
