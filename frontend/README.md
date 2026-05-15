# Frontend - E-commerce Fulfillment Control Tower UI

React frontend for the E-commerce Fulfillment Operations Control Tower.

## Structure

```
frontend/
├── src/
│   ├── api/
│   │   └── dashboard.js          # API client
│   ├── components/
│   │   ├── Header.jsx            # Navigation header
│   │   ├── OperationalScorecard.jsx  # Scorecard dashboard
│   │   └── ExceptionsPanel.jsx   # Exceptions dashboard
│   ├── App.jsx                   # Main application
│   ├── App.css                   # App styles
│   ├── main.jsx                  # Entry point
│   └── index.css                 # Global styles
├── index.html                    # HTML template
├── vite.config.js                # Vite configuration
└── package.json                  # Dependencies
```

## Installation

```bash
npm install
```

## Running the Application

### Development Server
```bash
npm run dev
```
Opens at `http://localhost:3000` with hot module replacement.

### Production Build
```bash
npm run build
```
Outputs to `dist/` folder.

### Preview Production Build
```bash
npm run preview
```

## Features

### Operational Scorecard Dashboard
- Real-time metrics from 6 systems
- Color-coded status indicators
- System health overview
- Trend indicators (up/down/stable)
- Auto-refresh every 30 seconds

**Metrics Displayed:**
- **WMS**: Pick completion rate, inventory accuracy, capacity utilization
- **OMS**: On-time delivery, order accuracy, processing time
- **TMS**: Transit performance, delivery metrics
- **Billing**: Collection rates, outstanding balances
- **Returns**: Return rates, processing efficiency
- **Yard**: Dock utilization, on-time arrivals

### Exceptions & Early Warnings Dashboard
- Critical alerts and warnings
- Severity-based filtering (Critical, High, Medium, Low)
- System-based categorization
- Recommended actions
- Real-time monitoring
- Auto-refresh every 30 seconds

**Exception Types:**
- Low inventory warnings
- Delayed orders
- Shipment exceptions
- Overdue invoices
- Pending returns
- Missed appointments
- Yard congestion alerts

## Components

### Header Component
Navigation and controls:
- Dashboard tab switching
- Manual refresh button
- Last update timestamp

### OperationalScorecard Component
Displays system metrics in a grid layout:
- System status cards
- Metric values with units
- Status indicators
- Trend arrows

### ExceptionsPanel Component
Shows alerts and warnings:
- Summary statistics
- Severity filters
- Exception cards with details
- Recommended actions

## API Integration

The frontend connects to the backend API:

```javascript
// src/api/dashboard.js
export const dashboardAPI = {
  getHealthCheck: () => api.get('/api/v1/health'),
  getScorecard: () => api.get('/api/v1/dashboard/scorecard'),
  getExceptions: () => api.get('/api/v1/dashboard/exceptions'),
};
```

Default API URL: `http://localhost:8000`

To change the API URL, set the environment variable:
```bash
VITE_API_URL=http://your-backend-url
```

## Styling

- Modern, clean design
- Responsive layout (desktop, tablet, mobile)
- Color-coded status system:
  - 🟢 Green: Good/Healthy
  - 🟡 Yellow: Warning
  - 🔴 Red: Critical
- Gradient header
- Card-based layout
- Hover effects

## Auto-Refresh

Dashboards automatically refresh every 30 seconds to ensure data is current. Users can also manually refresh using the button in the header.

## Error Handling

- Connection errors are displayed to the user
- Failed requests show helpful error messages
- Graceful degradation if backend is unavailable

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

## Development

### Hot Module Replacement
Vite provides instant feedback during development:
```bash
npm run dev
```

### Adding New Components
1. Create component in `src/components/`
2. Import and use in `App.jsx`
3. Add styling in component's CSS file

### Adding New API Endpoints
1. Add method to `src/api/dashboard.js`
2. Call from component using `useEffect` or event handler
3. Handle loading and error states

## Environment Variables

Create `.env` file:
```env
VITE_API_URL=http://localhost:8000
```

Access in code:
```javascript
const apiUrl = import.meta.env.VITE_API_URL;
```

## Build Optimization

The production build:
- Minifies JavaScript and CSS
- Tree-shakes unused code
- Optimizes assets
- Generates source maps

## Deployment

### Static Hosting (Netlify, Vercel, etc.)
```bash
npm run build
# Upload dist/ folder
```

### Docker
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build
# Serve with nginx or serve
```

### Environment-Specific Builds
```bash
# Development
npm run dev

# Production
VITE_API_URL=https://api.example.com npm run build
```

## Troubleshooting

### Cannot connect to backend
- Ensure backend is running on `http://localhost:8000`
- Check CORS configuration in backend
- Verify API_URL in environment variables

### Blank page after build
- Check browser console for errors
- Verify API endpoints are accessible
- Check that base URL is correct in `vite.config.js`

### Styles not loading
- Clear browser cache
- Rebuild the application
- Check CSS import paths

## Performance

- Code splitting by route
- Lazy loading of components
- Optimized re-renders with React hooks
- Debounced auto-refresh

## Accessibility

- Semantic HTML
- ARIA labels where appropriate
- Keyboard navigation support
- Color contrast compliance

## Future Enhancements

- User authentication
- Role-based access control
- Customizable dashboards
- Export to PDF/Excel
- Real-time WebSocket updates
- Dark mode
- Advanced filtering
- Historical data views
- Notifications center
- Mobile app version
