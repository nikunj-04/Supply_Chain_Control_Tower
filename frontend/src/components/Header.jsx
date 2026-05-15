import React from 'react';
import { getUserRoleDisplay } from '../utils/permissions';
import './Header.css';

function Header({ onRefresh, lastRefresh, currentUser, onLogout }) {
  const formatTime = (date) => {
    if (!date) return 'Never';
    return date.toLocaleTimeString();
  };

  return (
    <header className="header">
      <div className="header-content">
        <div className="header-left">
          <div className="header-text">
            <h1 className="header-title">
              <span className="header-icon">📊</span>
              E-commerce Fulfillment Control Tower
            </h1>
            <p className="header-subtitle">Operations Dashboard</p>
          </div>
        </div>
        
        <div className="header-right">
          {currentUser && (
            <div className="user-info">
              <span className="user-name">{currentUser.full_name}</span>
              <span className="user-role">
                {getUserRoleDisplay(currentUser)}
              </span>
            </div>
          )}
          <button className="refresh-button" onClick={onRefresh}>
            🔄 Refresh
          </button>
          <span className="last-refresh">
            Last updated: {formatTime(lastRefresh)}
          </span>
          {onLogout && (
            <button className="logout-button" onClick={onLogout}>
              🚪 Logout
            </button>
          )}
        </div>
      </div>
    </header>
  );
}

export default Header;
