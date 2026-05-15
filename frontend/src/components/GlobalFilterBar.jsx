import React from 'react';
import { useGlobalFilters, GLOBAL_FILTER_LABELS } from '../context/GlobalFiltersContext';
import './GlobalFilterBar.css';

const ORDER_SOURCE_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'd2c_shopify', label: 'D2C – Shopify' },
  { value: 'd2c_woocommerce', label: 'D2C – WooCommerce' },
  { value: 'marketplace', label: 'Marketplace' },
  { value: 'b2b', label: 'B2B' },
];

const PROMISE_STATUS_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'on_track', label: 'On Track' },
  { value: 'at_risk', label: 'At Risk' },
  { value: 'breached', label: 'Breached' },
];

const CUSTOMER_TYPE_OPTIONS = [
  { value: 'all', label: 'All' },
  { value: 'retail', label: 'Retail' },
  { value: 'marketplace', label: 'Marketplace' },
  { value: 'enterprise_b2b', label: 'Enterprise B2B' },
];

export default function GlobalFilterBar() {
  const { state, setOrderSource, setPromiseStatus, setCustomerType, clearFilters, selectors } = useGlobalFilters();

  return (
    <div className="global-filter-bar" role="region" aria-label="Global filters">
      <div className="global-filter-card">
        <div className="global-filter-row">
          <div className="global-filter-field">
            <label className="global-filter-label" htmlFor="global-order-source">
              Order Source
            </label>
            <select
              id="global-order-source"
              className="global-filter-select"
              value={state.orderSource}
              onChange={(e) => setOrderSource(e.target.value)}
            >
              {ORDER_SOURCE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div className="global-filter-field">
            <label className="global-filter-label" htmlFor="global-promise-status">
              Promise Status
            </label>
            <select
              id="global-promise-status"
              className="global-filter-select"
              value={state.promiseStatus}
              onChange={(e) => setPromiseStatus(e.target.value)}
            >
              {PROMISE_STATUS_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div className="global-filter-field">
            <label className="global-filter-label" htmlFor="global-customer-type">
              Customer Type
            </label>
            <select
              id="global-customer-type"
              className="global-filter-select"
              value={state.customerType}
              onChange={(e) => setCustomerType(e.target.value)}
            >
              {CUSTOMER_TYPE_OPTIONS.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
          </div>

          <div className="global-filter-actions">
            <button type="button" className="global-filter-clear" onClick={clearFilters}>
              Clear
            </button>
          </div>
        </div>

        <div className="global-filter-active" aria-live="polite">
          <span className="global-filter-active-label">Active Filters:</span>{' '}
          <span className="global-filter-active-text">{selectors.activeFiltersText}</span>
        </div>
      </div>
    </div>
  );
}

