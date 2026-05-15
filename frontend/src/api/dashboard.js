import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const dashboardAPI = {
  getHealthCheck: () => api.get('/api/v1/health'),
  getScorecard: () => api.get('/api/v1/dashboard/scorecard'),
  getExceptions: () => api.get('/api/v1/dashboard/exceptions'),
  getKPIDashboard: () => api.get('/api/v1/dashboard/kpis'),
  getAccessorialCharges: () => api.get('/api/v1/dashboard/accessorial-charges'),
  getClientProfitability: () => api.get('/api/v1/dashboard/client-profitability'),
  getBillingAnalytics: () => api.get('/api/v1/dashboard/billing-analytics'),
  getWarehousePerformance: () => api.get('/api/v1/dashboard/warehouse-performance'),
  getCarrierScorecard: () => api.get('/api/v1/dashboard/carrier-scorecard'),
  getLaborEfficiency: () => api.get('/api/v1/dashboard/labor-efficiency'),
  getInventoryOptimization: () => api.get('/api/v1/dashboard/inventory-optimization'),
  getStandardReports: () => api.get('/api/v1/dashboard/standard-reports'),
  getCustomReports: () => api.get('/api/v1/dashboard/custom-reports'),
  getScheduledExports: () => api.get('/api/v1/dashboard/scheduled-exports'),
};

export default api;
