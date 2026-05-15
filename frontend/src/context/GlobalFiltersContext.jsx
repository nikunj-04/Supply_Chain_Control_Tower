import React, { createContext, useContext, useEffect, useMemo, useReducer } from 'react';

/**
 * @typedef {('all'|'d2c_shopify'|'d2c_woocommerce'|'marketplace'|'b2b')} OrderSource
 * @typedef {('all'|'on_track'|'at_risk'|'breached')} PromiseStatus
 * @typedef {('all'|'retail'|'marketplace'|'enterprise_b2b')} CustomerType
 *
 * @typedef {{
 *   orderSource: OrderSource,
 *   promiseStatus: PromiseStatus,
 *   customerType: CustomerType,
 * }} GlobalFiltersState
 */

/** @type {GlobalFiltersState} */
const DEFAULT_STATE = {
  orderSource: 'all',
  promiseStatus: 'all',
  customerType: 'all',
};

const QS_KEYS = {
  orderSource: 'os',
  promiseStatus: 'ps',
  customerType: 'ct',
};

/** @returns {URLSearchParams} */
function getSearchParams() {
  return new URLSearchParams(window.location.search);
}

/**
 * @param {URLSearchParams} params
 * @returns {GlobalFiltersState}
 */
function parseStateFromSearchParams(params) {
  /** @type {GlobalFiltersState} */
  const next = { ...DEFAULT_STATE };

  const os = params.get(QS_KEYS.orderSource);
  const ps = params.get(QS_KEYS.promiseStatus);
  const ct = params.get(QS_KEYS.customerType);

  if (os && ['all', 'd2c_shopify', 'd2c_woocommerce', 'marketplace', 'b2b'].includes(os)) next.orderSource = /** @type {any} */ (os);
  if (ps && ['all', 'on_track', 'at_risk', 'breached'].includes(ps)) next.promiseStatus = /** @type {any} */ (ps);
  if (ct && ['all', 'retail', 'marketplace', 'enterprise_b2b'].includes(ct)) next.customerType = /** @type {any} */ (ct);

  return next;
}

/**
 * @param {GlobalFiltersState} state
 */
function syncStateToUrl(state) {
  const params = getSearchParams();

  const setOrDelete = (key, value) => {
    if (!value || value === 'all') params.delete(key);
    else params.set(key, value);
  };

  setOrDelete(QS_KEYS.orderSource, state.orderSource);
  setOrDelete(QS_KEYS.promiseStatus, state.promiseStatus);
  setOrDelete(QS_KEYS.customerType, state.customerType);

  const nextQuery = params.toString();
  const nextUrl = `${window.location.pathname}${nextQuery ? `?${nextQuery}` : ''}${window.location.hash || ''}`;
  window.history.replaceState({}, '', nextUrl);
}

/**
 * @typedef {{
 *   state: GlobalFiltersState,
 *   setOrderSource: (value: OrderSource) => void,
 *   setPromiseStatus: (value: PromiseStatus) => void,
 *   setCustomerType: (value: CustomerType) => void,
 *   clearFilters: () => void,
 *   selectors: {
 *     orderSourceLabel: string,
 *     promiseStatusLabel: string,
 *     customerTypeLabel: string,
 *     activeFiltersText: string,
 *   }
 * }} GlobalFiltersContextValue
 */

/** @type {React.Context<GlobalFiltersContextValue | null>} */
const GlobalFiltersContext = createContext(null);

const LABELS = {
  orderSource: {
    all: 'All Order Sources',
    d2c_shopify: 'D2C – Shopify',
    d2c_woocommerce: 'D2C – WooCommerce',
    marketplace: 'Marketplace',
    b2b: 'B2B',
  },
  promiseStatus: {
    all: 'All Promise Status',
    on_track: 'On Track',
    at_risk: 'At Risk',
    breached: 'Breached',
  },
  customerType: {
    all: 'All Customer Types',
    retail: 'Retail',
    marketplace: 'Marketplace',
    enterprise_b2b: 'Enterprise B2B',
  },
};

/**
 * @typedef {{
 *   type: 'SET_ORDER_SOURCE'|'SET_PROMISE_STATUS'|'SET_CUSTOMER_TYPE'|'CLEAR'|'HYDRATE',
 *   payload?: any
 * }} Action
 */

/**
 * @param {GlobalFiltersState} state
 * @param {Action} action
 * @returns {GlobalFiltersState}
 */
function reducer(state, action) {
  switch (action.type) {
    case 'SET_ORDER_SOURCE':
      return { ...state, orderSource: action.payload };
    case 'SET_PROMISE_STATUS':
      return { ...state, promiseStatus: action.payload };
    case 'SET_CUSTOMER_TYPE':
      return { ...state, customerType: action.payload };
    case 'CLEAR':
      return { ...DEFAULT_STATE };
    case 'HYDRATE':
      return { ...state, ...(action.payload || {}) };
    default:
      return state;
  }
}

export function GlobalFiltersProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, DEFAULT_STATE);

  // Initial hydrate from URL
  useEffect(() => {
    const initial = parseStateFromSearchParams(getSearchParams());
    dispatch({ type: 'HYDRATE', payload: initial });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Keep state in sync if user navigates browser history.
  useEffect(() => {
    const onPop = () => {
      const next = parseStateFromSearchParams(getSearchParams());
      dispatch({ type: 'HYDRATE', payload: next });
    };
    window.addEventListener('popstate', onPop);
    return () => window.removeEventListener('popstate', onPop);
  }, []);

  // Persist to URL query params (shareable links)
  useEffect(() => {
    syncStateToUrl(state);
  }, [state]);

  const value = useMemo(() => {
    const orderSourceLabel = LABELS.orderSource[state.orderSource] || LABELS.orderSource.all;
    const promiseStatusLabel = LABELS.promiseStatus[state.promiseStatus] || LABELS.promiseStatus.all;
    const customerTypeLabel = LABELS.customerType[state.customerType] || LABELS.customerType.all;

    const activeParts = [
      state.orderSource !== 'all' ? `Order Source: ${orderSourceLabel}` : null,
      state.promiseStatus !== 'all' ? `Promise: ${promiseStatusLabel}` : null,
      state.customerType !== 'all' ? `Customer Type: ${customerTypeLabel}` : null,
    ].filter(Boolean);

    const activeFiltersText = activeParts.length > 0 ? activeParts.join(' | ') : 'All filters';

    /** @type {GlobalFiltersContextValue} */
    return {
      state,
      setOrderSource: (v) => dispatch({ type: 'SET_ORDER_SOURCE', payload: v }),
      setPromiseStatus: (v) => dispatch({ type: 'SET_PROMISE_STATUS', payload: v }),
      setCustomerType: (v) => dispatch({ type: 'SET_CUSTOMER_TYPE', payload: v }),
      clearFilters: () => dispatch({ type: 'CLEAR' }),
      selectors: {
        orderSourceLabel,
        promiseStatusLabel,
        customerTypeLabel,
        activeFiltersText,
      },
    };
  }, [state]);

  return <GlobalFiltersContext.Provider value={value}>{children}</GlobalFiltersContext.Provider>;
}

/**
 * Access global filters anywhere in the app.
 * @returns {GlobalFiltersContextValue}
 */
export function useGlobalFilters() {
  const ctx = useContext(GlobalFiltersContext);
  if (!ctx) throw new Error('useGlobalFilters must be used within a GlobalFiltersProvider');
  return ctx;
}

export const GLOBAL_FILTER_LABELS = LABELS;

