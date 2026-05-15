import React from 'react';
import './PlaceholderView.css';

function PlaceholderView({ title, icon, description, features }) {
  return (
    <div className="placeholder-view">
      <div className="placeholder-header">
        <span className="placeholder-icon">{icon}</span>
        <h2 className="placeholder-title">{title}</h2>
      </div>
      
      <div className="placeholder-content">
        <p className="placeholder-description">{description}</p>
        
        {features && features.length > 0 && (
          <div className="placeholder-features">
            <h3>Planned Features:</h3>
            <ul>
              {features.map((feature, index) => (
                <li key={index}>{feature}</li>
              ))}
            </ul>
          </div>
        )}
        
        <div className="placeholder-status">
          <span className="status-badge">Coming Soon</span>
          <p>This feature is currently under development. Backend API integration pending.</p>
        </div>
      </div>
    </div>
  );
}

export default PlaceholderView;
