import React from 'react';
import './BillingAnalytics.css';

function BillingAnalytics({ data }) {
  if (!data) {
    return <div className="loading">Loading billing analytics data...</div>;
  }

  const { summary, revenue_by_service, invoice_status, trends } = data;

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount);
  };

  const getStatusColor = (status) => {
    const colorMap = {
      paid: 'status-paid',
      pending: 'status-pending',
      overdue: 'status-overdue',
      disputed: 'status-disputed'
    };
    return colorMap[status] || 'status-default';
  };

  // Calculate max revenue for chart scaling
  const maxRevenue = Math.max(...trends.map(t => t.revenue));

  return (
    <div className="billing-analytics">
      <div className="analytics-header">
        <h2>Billing Analytics</h2>
        <p className="last-updated">Last Updated: {new Date(data.timestamp).toLocaleString()}</p>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card revenue">
          <div className="card-icon">💵</div>
          <div className="card-content">
            <div className="card-value">{formatCurrency(summary.total_revenue_mtd)}</div>
            <div className="card-label">Revenue MTD</div>
            <div className="card-sublabel">YTD: {formatCurrency(summary.total_revenue_ytd)}</div>
          </div>
        </div>

        <div className="summary-card collection">
          <div className="card-icon">📊</div>
          <div className="card-content">
            <div className="card-value">{summary.collection_rate_mtd.toFixed(1)}%</div>
            <div className="card-label">Collection Rate</div>
            <div className="card-sublabel">{summary.invoices_paid_mtd} of {summary.invoices_issued_mtd} paid</div>
          </div>
        </div>

        <div className="summary-card dso">
          <div className="card-icon">⏱️</div>
          <div className="card-content">
            <div className="card-value">{summary.days_sales_outstanding}</div>
            <div className="card-label">Days Sales Outstanding</div>
            <div className="card-sublabel">Average DSO</div>
          </div>
        </div>

        <div className="summary-card overdue">
          <div className="card-icon">⚠️</div>
          <div className="card-content">
            <div className="card-value">{formatCurrency(summary.overdue_amount)}</div>
            <div className="card-label">Overdue Amount</div>
            <div className="card-sublabel">{formatCurrency(summary.disputed_amount)} disputed</div>
          </div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="analytics-grid">
        {/* Revenue by Service */}
        <div className="analytics-card">
          <h3>Revenue by Service Type</h3>
          <div className="service-list">
            {revenue_by_service.map(service => (
              <div key={service.service_type} className="service-item">
                <div className="service-header">
                  <span className="service-name">{service.service_type}</span>
                  <span className="service-revenue">{formatCurrency(service.revenue)}</span>
                </div>
                <div className="service-bar-container">
                  <div 
                    className="service-bar"
                    style={{ width: `${service.pct_of_total}%` }}
                  ></div>
                </div>
                <div className="service-details">
                  <span>{service.pct_of_total.toFixed(1)}% of total</span>
                  <span>{service.invoice_count} line items</span>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Invoice Status */}
        <div className="analytics-card">
          <h3>Invoice Status (MTD)</h3>
          <div className="status-list">
            {invoice_status.map(status => (
              <div key={status.status} className="status-item">
                <div className="status-header">
                  <span className={`status-badge ${getStatusColor(status.status)}`}>
                    {status.status}
                  </span>
                  <span className="status-count">{status.count} invoices</span>
                </div>
                <div className="status-amount">{formatCurrency(status.total_amount)}</div>
                <div className="status-percentage">{status.pct_of_count.toFixed(1)}% of total</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Revenue Trend Chart */}
      <div className="analytics-card trend-card">
        <h3>Revenue Trend (Last 30 Days)</h3>
        <div className="trend-chart">
          {trends.map((trend, index) => (
            <div key={trend.date} className="trend-bar-container">
              <div 
                className="trend-bar"
                style={{ height: `${(trend.revenue / maxRevenue) * 100}%` }}
                title={`${trend.date}: ${formatCurrency(trend.revenue)}`}
              >
                <div className="trend-tooltip">
                  <div className="tooltip-date">{new Date(trend.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</div>
                  <div className="tooltip-revenue">{formatCurrency(trend.revenue)}</div>
                  <div className="tooltip-details">
                    {trend.invoices_issued} issued, {trend.invoices_paid} paid
                  </div>
                </div>
              </div>
              {index % 5 === 0 && (
                <div className="trend-label">
                  {new Date(trend.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Key Metrics Table */}
      <div className="analytics-card">
        <h3>Key Performance Indicators</h3>
        <table className="kpi-table">
          <tbody>
            <tr>
              <td className="kpi-label">Average Invoice Value</td>
              <td className="kpi-value">{formatCurrency(summary.avg_invoice_value)}</td>
            </tr>
            <tr>
              <td className="kpi-label">Invoices Issued (MTD)</td>
              <td className="kpi-value">{summary.invoices_issued_mtd}</td>
            </tr>
            <tr>
              <td className="kpi-label">Invoices Paid (MTD)</td>
              <td className="kpi-value">{summary.invoices_paid_mtd}</td>
            </tr>
            <tr>
              <td className="kpi-label">Collection Rate (MTD)</td>
              <td className="kpi-value">{summary.collection_rate_mtd.toFixed(1)}%</td>
            </tr>
            <tr>
              <td className="kpi-label">Days Sales Outstanding</td>
              <td className="kpi-value">{summary.days_sales_outstanding} days</td>
            </tr>
            <tr>
              <td className="kpi-label">Outstanding Overdue</td>
              <td className="kpi-value overdue">{formatCurrency(summary.overdue_amount)}</td>
            </tr>
            <tr>
              <td className="kpi-label">Disputed Invoices</td>
              <td className="kpi-value disputed">{formatCurrency(summary.disputed_amount)}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  );
}

export default BillingAnalytics;
