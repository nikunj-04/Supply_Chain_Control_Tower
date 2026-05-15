import React, { useState, useEffect } from 'react';
import { dashboardAPI } from './api/dashboard';
import Login from './components/Login';
import Header from './components/Header';
import Sidebar from './components/Sidebar';
import OperationalScorecard from './components/OperationalScorecard';
import ExceptionsPanel from './components/ExceptionsPanel';
import ExceptionCenter from './components/ExceptionCenter';
import ShipmentTracking from './components/ShipmentTracking';
import OrderJourney from './components/OrderJourney';
import KPIDashboard from './components/KPIDashboard';
import AccessorialCharges from './components/AccessorialCharges';
import ClientProfitability from './components/ClientProfitability';
import BillingAnalytics from './components/BillingAnalytics';
import WarehousePerformance from './components/WarehousePerformance';
import CarrierScorecards from './components/CarrierScorecards';
// import LaborEfficiency from './components/LaborEfficiency';
import InventoryOptimization from './components/InventoryOptimization';
import StandardReports from './components/StandardReports';
import CustomReports from './components/CustomReports';
import ScheduledExports from './components/ScheduledExports';
import UserManagement from './components/UserManagement';
import AuditLogViewer from './components/AuditLogViewer';
// import Chat from './components/Chat';
import { GlobalFiltersProvider } from './context/GlobalFiltersContext';
import './App.css';

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [activeView, setActiveView] = useState('kpis');
  const [scorecardData, setScorecardData] = useState(null);
  const [exceptionsData, setExceptionsData] = useState(null);
  const [kpiData, setKPIData] = useState(null);
  const [accessorialChargesData, setAccessorialChargesData] = useState(null);
  const [clientProfitabilityData, setClientProfitabilityData] = useState(null);
  const [billingAnalyticsData, setBillingAnalyticsData] = useState(null);
  const [warehousePerformanceData, setWarehousePerformanceData] = useState(null);
  const [carrierScorecardData, setCarrierScorecardData] = useState(null);
  const [laborEfficiencyData, setLaborEfficiencyData] = useState(null);
  const [inventoryOptimizationData, setInventoryOptimizationData] = useState(null);
  const [standardReportsData, setStandardReportsData] = useState(null);
  const [customReportsData, setCustomReportsData] = useState(null);
  const [scheduledExportsData, setScheduledExportsData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastRefresh, setLastRefresh] = useState(null);

  // Check for existing session on mount
  useEffect(() => {
    const token = localStorage.getItem('token');
    const user = localStorage.getItem('user');
    
    if (token && user) {
      try {
        const parsedUser = JSON.parse(user);
        setCurrentUser(parsedUser);
        setIsAuthenticated(true);
      } catch (e) {
        // Invalid stored data, clear it
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('refresh_token');
      }
    }
  }, []);

  const handleLogin = (user) => {
    setCurrentUser(user);
    setIsAuthenticated(true);
  };

  const handleLogout = async () => {
    try {
      const token = localStorage.getItem('token');
      if (token) {
        await fetch('http://localhost:8000/api/v1/auth/logout', {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`
          }
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('token');
      localStorage.removeItem('refresh_token');
      localStorage.removeItem('user');
      setIsAuthenticated(false);
      setCurrentUser(null);
    }
  };

  // Load data when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      // Only load data for views that have backend APIs
      const viewsWithData = ['scorecard', 'exceptions', 'kpis', 'accessorial-charges', 'client-profitability', 'billing-analytics', 'warehouse-performance', 'carrier-scorecards', /* 'labor-efficiency', */ 'inventory-optimization', 'standard-reports', 'custom-reports', 'scheduled-exports'];
      if (viewsWithData.includes(activeView)) {
        loadData();
        // Auto-refresh every 30 seconds
        const interval = setInterval(loadData, 30000);
        return () => clearInterval(interval);
      }
    }
  }, [activeView, isAuthenticated]);

  // If not authenticated, show login page
  if (!isAuthenticated) {
    return <Login onLogin={handleLogin} />;
  }

  const loadData = async () => {
    setLoading(true);
    setError(null);
    
    try {
      if (activeView === 'scorecard') {
        const response = await dashboardAPI.getScorecard();
        setScorecardData(response.data);
      } else if (activeView === 'exceptions') {
        const response = await dashboardAPI.getExceptions();
        setExceptionsData(response.data);
      } else if (activeView === 'kpis') {
        const response = await dashboardAPI.getKPIDashboard();
        setKPIData(response.data);
      } else if (activeView === 'accessorial-charges') {
        const response = await dashboardAPI.getAccessorialCharges();
        setAccessorialChargesData(response.data);
      } else if (activeView === 'client-profitability') {
        const response = await dashboardAPI.getClientProfitability();
        setClientProfitabilityData(response.data);
      } else if (activeView === 'billing-analytics') {
        const response = await dashboardAPI.getBillingAnalytics();
        setBillingAnalyticsData(response.data);
      } else if (activeView === 'warehouse-performance') {
        const response = await dashboardAPI.getWarehousePerformance();
        setWarehousePerformanceData(response.data);
      } else if (activeView === 'carrier-scorecards') {
        const response = await dashboardAPI.getCarrierScorecard();
        setCarrierScorecardData(response.data);
      } else if (activeView === 'inventory-optimization') {
        const response = await dashboardAPI.getInventoryOptimization();
        setInventoryOptimizationData(response.data);
      } else if (activeView === 'standard-reports') {
        const response = await dashboardAPI.getStandardReports();
        setStandardReportsData(response.data);
      } else if (activeView === 'custom-reports') {
        const response = await dashboardAPI.getCustomReports();
        setCustomReportsData(response.data);
      } else if (activeView === 'scheduled-exports') {
        const response = await dashboardAPI.getScheduledExports();
        setScheduledExportsData(response.data);
      }
      setLastRefresh(new Date());
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to load data. Make sure the backend is running.');
      console.error('Error loading data:', err);
    } finally {
      setLoading(false);
    }
  };

  const renderView = () => {
    switch (activeView) {
      // Dashboards
      case 'kpis':
        return kpiData ? <KPIDashboard data={kpiData} /> : null;
      case 'scorecard':
        return scorecardData ? <OperationalScorecard data={scorecardData} /> : null;
      case 'exceptions':
        return exceptionsData ? <ExceptionsPanel data={exceptionsData} /> : null;
      case 'exception-center':
        return <ExceptionCenter />;
      case 'shipment-tracking':
        return <ShipmentTracking />;
      case 'order-journey':
        return <OrderJourney />;
      
      // Revenue Intelligence
      case 'accessorial-charges':
        return accessorialChargesData ? <AccessorialCharges data={accessorialChargesData} /> : null;
      case 'client-profitability':
        return clientProfitabilityData ? <ClientProfitability data={clientProfitabilityData} /> : null;
      case 'billing-analytics':
        return billingAnalyticsData ? <BillingAnalytics data={billingAnalyticsData} /> : null;
      
      // Operations Deep Dive
      case 'warehouse-performance':
        return warehousePerformanceData ? <WarehousePerformance data={warehousePerformanceData} /> : null;
      case 'carrier-scorecards':
        return carrierScorecardData ? <CarrierScorecards data={carrierScorecardData} /> : null;
      // case 'labor-efficiency':
      //   return laborEfficiencyData ? <LaborEfficiency data={laborEfficiencyData} /> : null;
      case 'inventory-optimization':
        return inventoryOptimizationData ? <InventoryOptimization data={inventoryOptimizationData} /> : null;
      
      // Reports
      case 'standard-reports':
        return standardReportsData ? <StandardReports data={standardReportsData} /> : null;
      case 'custom-reports':
        return customReportsData ? <CustomReports data={customReportsData} /> : null;
      case 'scheduled-exports':
        return scheduledExportsData ? <ScheduledExports data={scheduledExportsData} /> : null;
      case 'user-management':
        return <UserManagement />;
      case 'audit-logs':
        return <AuditLogViewer />;
      
      default:
        return kpiData ? <KPIDashboard data={kpiData} /> : null;
    }
  };

  return (
    <GlobalFiltersProvider>
      <div className="app">
        <Sidebar 
          activeView={activeView}
          setActiveView={setActiveView}
          currentUser={currentUser}
        />
        
        <div className="app-main">
          <Header 
            onRefresh={loadData}
            lastRefresh={lastRefresh}
            currentUser={currentUser}
            onLogout={handleLogout}
          />
          
          <main className="main-content">
            {loading && <div className="loading">Loading dashboard data...</div>}
            
            {error && (
              <div className="error-banner">
                <strong>Error:</strong> {error}
              </div>
            )}
            
            {!loading && !error && renderView()}
          </main>
        </div>

        {/* Floating Chat Bot (temporarily disabled) */}
        {/* <Chat /> */}
      </div>
    </GlobalFiltersProvider>
  );
}

export default App;
