import React, { useState, useEffect } from 'react';
import './AccessorialCharges.css';

function AccessorialCharges({ data }) {
  const [filter, setFilter] = useState('all');
  const [currentPage, setCurrentPage] = useState(1);
  const [billingStatus, setBillingStatus] = useState(() => {
    const saved = localStorage.getItem('accessorialBillingStatus');
    return saved ? JSON.parse(saved) : {};
  });
  const [loading, setLoading] = useState({});
  const itemsPerPage = 8;

  // Persist billing status to localStorage
  useEffect(() => {
    localStorage.setItem('accessorialBillingStatus', JSON.stringify(billingStatus));
  }, [billingStatus]);

  if (!data) {
    return <div className="loading">Loading accessorial charges data...</div>;
  }

  const { summary, opportunities } = data;

  // Filter opportunities
  const filteredOpportunities = filter === 'all' 
    ? opportunities 
    : opportunities.filter(opp => opp.charge_type === filter);

  // Pagination
  const totalPages = Math.ceil(filteredOpportunities.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const displayedOpportunities = filteredOpportunities.slice(startIndex, startIndex + itemsPerPage);

  const handlePageChange = (page) => {
    setCurrentPage(page);
  };

  const handleFilterChange = (newFilter) => {
    setFilter(newFilter);
    setCurrentPage(1);
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      pending: { label: 'Pending', className: 'status-pending' },
      under_review: { label: 'Under Review', className: 'status-review' },
      billed: { label: 'Billed', className: 'status-billed' },
      recovered: { label: 'Recovered', className: 'status-recovered' }
    };
    const statusInfo = statusMap[status] || { label: status, className: 'status-default' };
    return <span className={`status-badge ${statusInfo.className}`}>{statusInfo.label}</span>;
  };

  const getChargeTypeLabel = (type) => {
    const typeMap = {
      detention: 'Detention',
      redelivery: 'Redelivery',
      dock_detention: 'Dock Detention',
      address_correction: 'Address Correction',
      fuel_surcharge: 'Fuel Surcharge'
    };
    return typeMap[type] || type;
  };

  const handleBillNow = async (chargeId) => {
    setLoading(prev => ({ ...prev, [chargeId]: true }));
    
    try {
      const response = await fetch(
        `http://localhost:8000/api/v1/billing/process-accessorial-charge?charge_id=${chargeId}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
        }
      );

      if (!response.ok) {
        throw new Error('Failed to process charge');
      }

      const result = await response.json();
      
      // Update billing status with invoice details
      setBillingStatus(prev => ({
        ...prev,
        [chargeId]: {
          status: 'billed',
          invoiceNumber: result.invoice_number,
          downloadUrl: `http://localhost:8000${result.download_url}`,
          billedDate: new Date(result.invoice_date).toLocaleDateString(),
          amount: result.amount
        }
      }));

      // Show success message (could be replaced with toast notification)
      alert(`Invoice ${result.invoice_number} created successfully!\nAmount: ${formatCurrency(result.amount)}`);
      
    } catch (error) {
      console.error('Error processing charge:', error);
      alert('Failed to process charge. Please try again.');
    } finally {
      setLoading(prev => ({ ...prev, [chargeId]: false }));
    }
  };

  const handleDownloadInvoice = (downloadUrl) => {
    window.open(downloadUrl, '_blank');
  };

  return (
    <div className="accessorial-charges">
      <div className="charges-header">
        <h2>Accessorial Charges Recovery</h2>
        <p className="last-updated">Last Updated: {new Date(data.timestamp).toLocaleString()}</p>
      </div>

      {/* Summary Cards */}
      <div className="summary-cards">
        <div className="summary-card recoverable">
          <div className="card-icon">💰</div>
          <div className="card-content">
            <div className="card-value">{formatCurrency(summary.total_recoverable)}</div>
            <div className="card-label">Total Recoverable</div>
            <div className="card-count">{summary.total_opportunities} opportunities</div>
          </div>
        </div>

        <div className="summary-card review">
          <div className="card-icon">⏳</div>
          <div className="card-content">
            <div className="card-value">{summary.pending_review}</div>
            <div className="card-label">Pending Review</div>
            <div className="card-sublabel">Awaiting action</div>
          </div>
        </div>

        <div className="summary-card billed">
          <div className="card-icon">📤</div>
          <div className="card-content">
            <div className="card-value">{summary.billed_mtd}</div>
            <div className="card-label">Billed MTD</div>
            <div className="card-sublabel">This month</div>
          </div>
        </div>

        <div className="summary-card recovered">
          <div className="card-icon">✅</div>
          <div className="card-content">
            <div className="card-value">{formatCurrency(summary.recovered_mtd)}</div>
            <div className="card-label">Recovered MTD</div>
            <div className="card-sublabel">Collected</div>
          </div>
        </div>
      </div>

      {/* Charge Type Breakdown */}
      <div className="charge-breakdown">
        <h3>By Charge Type</h3>
        <div className="breakdown-grid">
          {Object.entries(summary.by_charge_type).map(([type, data]) => (
            <div key={type} className="breakdown-item">
              <div className="breakdown-type">{getChargeTypeLabel(type)}</div>
              <div className="breakdown-amount">{formatCurrency(data.amount)}</div>
              <div className="breakdown-count">{data.count} charges</div>
            </div>
          ))}
        </div>
      </div>

      {/* Filters */}
      <div className="charges-filters">
        <button 
          className={filter === 'all' ? 'active' : ''} 
          onClick={() => handleFilterChange('all')}
        >
          All ({opportunities.length})
        </button>
        <button 
          className={filter === 'detention' ? 'active' : ''} 
          onClick={() => handleFilterChange('detention')}
        >
          Detention
        </button>
        <button 
          className={filter === 'redelivery' ? 'active' : ''} 
          onClick={() => handleFilterChange('redelivery')}
        >
          Redelivery
        </button>
        <button 
          className={filter === 'dock_detention' ? 'active' : ''} 
          onClick={() => handleFilterChange('dock_detention')}
        >
          Dock Detention
        </button>
      </div>

      {/* Opportunities Table */}
      <div className="opportunities-table">
        <table>
          <thead>
            <tr>
              <th>Charge ID</th>
              <th>Type</th>
              <th>Amount</th>
              <th>Carrier</th>
              <th>Shipment</th>
              <th>Date</th>
              <th>Age</th>
              <th>Status</th>
              <th>Action</th>
            </tr>
          </thead>
          <tbody>
            {displayedOpportunities.map(opp => {
              const chargeId = opp.charge_id;
              const isLoading = loading[chargeId];
              
              // Check if we have invoice information (from backend or local state)
              const hasInvoiceBackend = opp.invoice_number && opp.download_url;
              const hasInvoiceLocal = billingStatus[chargeId]?.invoiceNumber && billingStatus[chargeId]?.downloadUrl;
              const hasInvoice = hasInvoiceBackend || hasInvoiceLocal;
              
              // Get download URL and invoice number
              const downloadUrl = hasInvoiceBackend 
                ? `http://localhost:8000${opp.download_url}`
                : billingStatus[chargeId]?.downloadUrl;
              
              const invoiceNumber = hasInvoiceBackend 
                ? opp.invoice_number 
                : billingStatus[chargeId]?.invoiceNumber;
              
              // Determine if charge is billed (has invoice OR status is billed)
              const isBilled = opp.status === 'billed' || hasInvoice;
              
              return (
                <tr key={chargeId}>
                  <td className="charge-id">{chargeId}</td>
                  <td>{getChargeTypeLabel(opp.charge_type)}</td>
                  <td className="amount">{formatCurrency(opp.amount)}</td>
                  <td>{opp.carrier || 'N/A'}</td>
                  <td>{opp.shipment_id || '-'}</td>
                  <td>{new Date(opp.occurrence_date).toLocaleDateString()}</td>
                  <td>{opp.age_days}d</td>
                  <td>
                    {isBilled ? (
                      <span className="status-badge status-billed">Billed</span>
                    ) : (
                      getStatusBadge(opp.status)
                    )}
                  </td>
                  <td>
                    {hasInvoice ? (
                      <button 
                        className="action-button download"
                        onClick={() => handleDownloadInvoice(downloadUrl)}
                        title={`Invoice: ${invoiceNumber}`}
                      >
                        📄 Download Invoice
                      </button>
                    ) : (opp.status === 'pending' || opp.status === 'under_review') && !isLoading ? (
                      <button 
                        className="action-button bill-now"
                        onClick={() => handleBillNow(chargeId)}
                      >
                        Bill Now
                      </button>
                    ) : isLoading ? (
                      <button className="action-button bill-now" disabled>
                        Processing...
                      </button>
                    ) : null}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="pagination">
          <button 
            onClick={() => handlePageChange(currentPage - 1)} 
            disabled={currentPage === 1}
          >
            Previous
          </button>
          <span className="page-info">
            Page {currentPage} of {totalPages}
          </span>
          <button 
            onClick={() => handlePageChange(currentPage + 1)} 
            disabled={currentPage === totalPages}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}

export default AccessorialCharges;

