# E-commerce Fulfillment Control Tower MVP

A comprehensive E-commerce Fulfillment Operations Control Tower with FastAPI backend and React frontend. This MVP simulates integrations with enterprise systems (WMS, OMS, TMS, Billing, Returns, Yard/Dock) using separate SQLite databases.

## 🎯 Features

- **Operational Scorecard Dashboard**: Real-time metrics from all systems
- **Exceptions & Early Warnings Dashboard**: Critical alerts and notifications
- **6 Integrated Systems**:
  - Warehouse Management System (WMS)
  - Order Management System (OMS)
  - Transportation Management System (TMS)
  - Billing System
  - Returns Management
  - Yard/Dock Management

## 🏗️ Architecture

```
supplychain-controltower/
├── backend/              # FastAPI backend
│   ├── config.py         # Configuration management
│   ├── logger.py         # Logging setup
│   ├── main.py           # FastAPI application
│   ├── schemas.py        # Pydantic models
│   ├── models/           # Database models for each system
│   ├── services/         # Business logic layer
│   └── scripts/          # Data seeding scripts
└── frontend/             # React frontend
    ├── src/
    │   ├── api/          # API client
    │   ├── components/   # React components
    │   └── App.jsx       # Main application
    └── package.json
```

## 📋 Prerequisites

- Python 3.9 or higher
- Node.js 18 or higher
- npm or yarn

## 🚀 Quick Start

### 1. Clone or Navigate to the Project

```bash
cd d:\projects\supplychain-controltower
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Unix/macOS:
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
copy .env.example .env

# Run seed script to generate sample data
python scripts/seed_data.py

# Start the backend server
python main.py
```

The backend will be available at `http://localhost:8000`
- API Documentation: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

### 3. Frontend Setup

Open a new terminal:

```bash
cd frontend

# Install dependencies
npm install

# Start the development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

## 📊 Dashboards

### Operational Scorecard
- View real-time metrics from all 6 systems
- Color-coded status indicators (Good, Warning, Critical)
- Key performance indicators for each system
- Trend indicators

### Exceptions & Early Warnings
- Critical alerts and warnings across all systems
- Filterable by severity (Critical, High, Medium, Low)
- Recommended actions for each exception
- Real-time monitoring

## 🗄️ Database Structure

Each system has its own SQLite database in `backend/data/`:

- `wms.db` - Warehouse inventory, picking tasks, metrics
- `oms.db` - Orders, order lines, fulfillment metrics
- `tms.db` - Shipments, routes, transportation metrics
- `billing.db` - Invoices, line items, revenue metrics
- `returns.db` - Returns, return items, processing metrics
- `yard.db` - Dock appointments, yard locations, operational metrics

## 🔧 Configuration

Backend configuration is in `backend/.env`:

```env
# Application
APP_NAME="E-commerce Fulfillment Control Tower"
DEBUG=True
LOG_LEVEL=INFO

# Database paths (relative to backend directory)
WMS_DB_PATH=./data/wms.db
OMS_DB_PATH=./data/oms.db
TMS_DB_PATH=./data/tms.db
BILLING_DB_PATH=./data/billing.db
RETURNS_DB_PATH=./data/returns.db
YARD_DB_PATH=./data/yard.db

# API
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## 🔌 API Endpoints

### Health Check
```
GET /api/v1/health
```

### Operational Scorecard
```
GET /api/v1/dashboard/scorecard
```

### Exceptions & Warnings
```
GET /api/v1/dashboard/exceptions
```

## 🛠️ Development

### Backend Development

```bash
cd backend

# Activate virtual environment
venv\Scripts\activate

# Run with auto-reload
python main.py

# Or use uvicorn directly
uvicorn main:app --reload --port 8000
```

### Frontend Development

```bash
cd frontend

# Start dev server with hot reload
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

### Regenerate Sample Data

```bash
cd backend
python scripts/seed_data.py
```

## 📦 Production Build

### Backend

```bash
cd backend

# Install production dependencies
pip install -r requirements.txt

# Set DEBUG=False in .env
# Run with gunicorn or uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Frontend

```bash
cd frontend

# Build for production
npm run build

# The dist/ folder contains static files ready to deploy
```

## 🧪 Testing the Application

1. **Verify Backend**: Navigate to `http://localhost:8000/api/docs` to see the API documentation
2. **Check Health**: Visit `http://localhost:8000/api/v1/health` to verify all databases are connected
3. **View Dashboard**: Open `http://localhost:3000` to see the control tower
4. **Explore Data**: Switch between "Operational Scorecard" and "Exceptions & Warnings" tabs

## 🎨 Key Design Decisions

1. **Separate Databases**: Each system has its own SQLite database to simulate real-world enterprise integrations
2. **Pydantic Models**: Strong typing and validation for all API responses
3. **Production Patterns**: Environment configuration, structured logging, error handling
4. **Realistic Data**: Faker library generates realistic sample data
5. **Auto-refresh**: Dashboard automatically refreshes every 30 seconds
6. **Responsive UI**: Works on desktop, tablet, and mobile devices

## 📝 Sample Data

The seed script generates:
- 100 inventory items across 3 warehouses
- 150 orders with multiple line items
- 150 shipments with various carriers
- 100 invoices with payment status
- 50 returns with processing status
- 80 dock appointments and 60 yard locations
- 30 days of historical metrics for each system

## 🔍 Troubleshooting

### Backend Issues

**Database errors**: Delete the `backend/data/` folder and run `python scripts/seed_data.py` again

**Port already in use**: Change the port in `backend/main.py` or kill the process using port 8000

**Module not found**: Ensure virtual environment is activated and dependencies are installed

### Frontend Issues

**Cannot connect to backend**: Verify backend is running on `http://localhost:8000`

**npm install fails**: Try deleting `node_modules` and `package-lock.json`, then run `npm install` again

**Port 3000 in use**: Vite will automatically use the next available port (3001, 3002, etc.)

## 📈 Future Enhancements

- User authentication and role-based access
- Real-time WebSocket updates
- Advanced analytics and reporting
- Export functionality (PDF, Excel)
- System configuration UI
- Alert notifications (email, SMS)
- Historical trend analysis
- Predictive analytics using ML

## 📄 License

This is an MVP project for demonstration purposes.

## 👥 Support

For issues or questions, please review the troubleshooting section above or check the inline code documentation.
