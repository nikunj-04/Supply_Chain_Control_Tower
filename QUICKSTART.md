# 🚀 Quick Start Guide

## What You Have

A complete E-commerce Fulfillment Operations Control Tower MVP with:
- ✅ FastAPI backend with 6 simulated enterprise systems
- ✅ React frontend with 2 dashboards
- ✅ Realistic sample data
- ✅ Production-ready code patterns
- ✅ Complete documentation

## One-Command Setup (Windows)

```bash
setup.bat
```

This will:
1. Create Python virtual environment
2. Install all backend dependencies
3. Generate sample databases with realistic data
4. Install all frontend dependencies

## Starting the Application

### Option 1: Use Batch Scripts

**Terminal 1 - Backend:**
```bash
start-backend.bat
```

**Terminal 2 - Frontend:**
```bash
start-frontend.bat
```

### Option 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
venv\Scripts\activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

## Access the Application

- **Control Tower Dashboard**: http://localhost:3000
- **API Documentation**: http://localhost:8000/api/docs
- **Health Check**: http://localhost:8000/api/v1/health

## Project Structure

```
supplychain-controltower/
│
├── backend/                    # FastAPI Backend
│   ├── main.py                # API server
│   ├── config.py              # Settings
│   ├── schemas.py             # API models
│   ├── models/                # Database models (6 systems)
│   ├── services/              # Business logic
│   ├── scripts/
│   │   └── seed_data.py      # Data generator
│   └── data/                  # SQLite databases (auto-generated)
│
├── frontend/                   # React Frontend
│   ├── src/
│   │   ├── App.jsx           # Main app
│   │   ├── api/              # API client
│   │   └── components/       # Dashboard components
│   └── package.json
│
├── setup.bat                  # One-command setup
├── start-backend.bat          # Start backend
├── start-frontend.bat         # Start frontend
└── README.md                  # Full documentation
```

## The 6 Integrated Systems

Each system has its own SQLite database:

1. **WMS** (Warehouse Management)
   - Inventory levels
   - Picking tasks
   - Warehouse metrics

2. **OMS** (Order Management)
   - Customer orders
   - Order fulfillment
   - Delivery tracking

3. **TMS** (Transportation Management)
   - Shipments
   - Routes
   - Carrier performance

4. **Billing**
   - Invoices
   - Payment tracking
   - Revenue metrics

5. **Returns Management**
   - Return requests
   - Processing status
   - Refund tracking

6. **Yard/Dock Management**
   - Dock appointments
   - Yard locations
   - Equipment tracking

## The 2 Dashboards

### 1. Operational Scorecard
- Real-time KPIs from all 6 systems
- Color-coded health indicators
- Trend arrows (up/down/stable)
- System status overview

### 2. Exceptions & Early Warnings
- Critical alerts and warnings
- Severity filtering (Critical/High/Medium/Low)
- Recommended actions
- Real-time monitoring

## Sample Data Included

- 100 inventory items
- 150 orders with line items
- 150 shipments
- 100 invoices
- 50 returns
- 80 dock appointments
- 60 yard locations
- 30 days of historical metrics

## Key Features

✅ **Production-Minded Code**
- Pydantic models for validation
- Environment configuration
- Structured logging
- Error handling
- CORS configuration

✅ **Clean Architecture**
- Separation of concerns
- Service layer pattern
- API/UI separation
- Modular design

✅ **Developer Experience**
- Auto-reload in development
- API documentation (Swagger/ReDoc)
- Clear error messages
- Type hints

✅ **Realistic Simulation**
- Faker for realistic data
- Multiple carriers, warehouses, customers
- Various status types
- Time-based metrics

## API Endpoints

### Health Check
```
GET /api/v1/health
```
Returns database connectivity status

### Operational Scorecard
```
GET /api/v1/dashboard/scorecard
```
Returns metrics from all systems

### Exceptions & Warnings
```
GET /api/v1/dashboard/exceptions
```
Returns alerts and exceptions

## Customization

### Modify Sample Data
Edit `backend/scripts/seed_data.py` and run:
```bash
cd backend
python scripts/seed_data.py
```

### Add New Metrics
1. Update `dashboard_service.py`
2. Update `schemas.py`
3. Frontend will auto-display new data

### Change Styling
Edit CSS files in `frontend/src/components/`

## Troubleshooting

### Backend won't start
- Ensure Python 3.9+ is installed
- Activate virtual environment
- Check port 8000 is available

### Frontend won't start
- Ensure Node.js 18+ is installed
- Run `npm install` in frontend folder
- Check port 3000 is available

### No data showing
- Run `python scripts/seed_data.py` in backend
- Check backend is running
- Verify API URL in frontend

### Database errors
- Delete `backend/data/` folder
- Run seed script again

## Next Steps

1. **Explore the Dashboards**: Click between tabs to see different views
2. **Check the API Docs**: Visit http://localhost:8000/api/docs
3. **Review the Code**: Start with `backend/main.py` and `frontend/src/App.jsx`
4. **Customize**: Add your own metrics and alerts
5. **Deploy**: See README.md for deployment options

## Tech Stack

**Backend:**
- FastAPI (API framework)
- SQLAlchemy (ORM)
- Pydantic (validation)
- SQLite (databases)

**Frontend:**
- React 18
- Vite (build tool)
- Axios (HTTP client)
- CSS3 (styling)

## Performance

- Auto-refresh every 30 seconds
- Optimized queries
- Efficient data aggregation
- Responsive UI

## Security Notes (Production)

For production deployment, add:
- User authentication
- API key validation
- Rate limiting
- HTTPS
- Database encryption
- Backup strategy

## Support

- Main README: `/README.md`
- Backend README: `/backend/README.md`
- Frontend README: `/frontend/README.md`

## What Makes This Production-Minded?

1. **Configuration Management**: Environment variables, not hardcoded values
2. **Logging**: Structured logging throughout
3. **Error Handling**: Proper exception handling with user-friendly messages
4. **Validation**: Pydantic models validate all data
5. **Separation of Concerns**: Models, services, and routes are separated
6. **Documentation**: Comprehensive READMEs and inline documentation
7. **Type Hints**: Python type hints for better IDE support
8. **Scalable Structure**: Easy to add new systems and metrics

Enjoy your E-commerce Fulfillment Control Tower! 🚀
