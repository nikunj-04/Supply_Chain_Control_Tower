# Backend - E-commerce Fulfillment Control Tower API

FastAPI backend for the E-commerce Fulfillment Operations Control Tower.

## Structure

```
backend/
├── config.py              # Application configuration
├── logger.py              # Logging setup
├── main.py                # FastAPI application entry point
├── schemas.py             # Pydantic response models
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
├── models/               # Database models
│   ├── wms_models.py     # Warehouse Management System
│   ├── oms_models.py     # Order Management System
│   ├── tms_models.py     # Transportation Management System
│   ├── billing_models.py # Billing System
│   ├── returns_models.py # Returns Management
│   └── yard_models.py    # Yard/Dock Management
├── services/             # Business logic
│   └── dashboard_service.py  # Dashboard data aggregation
└── scripts/              # Utility scripts
    └── seed_data.py      # Generate sample data
```

## Installation

1. Create and activate virtual environment:
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Unix/macOS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Setup environment:
```bash
copy .env.example .env
```

4. Generate sample data:
```bash
python scripts/seed_data.py
```

## Running the Server

### Development
```bash
python main.py
```
Server runs on `http://localhost:8000` with auto-reload enabled.

### Production
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once the server is running:
- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

## Endpoints

### Health Check
```
GET /api/v1/health
```
Returns system health status and database connectivity.

### Operational Scorecard
```
GET /api/v1/dashboard/scorecard
```
Returns metrics from all 6 systems:
- WMS: Inventory, picking tasks, warehouse metrics
- OMS: Orders, fulfillment, accuracy
- TMS: Shipments, routes, transit times
- Billing: Invoices, revenue, collections
- Returns: Return rates, processing times
- Yard: Appointments, utilization, dock times

### Exceptions & Warnings
```
GET /api/v1/dashboard/exceptions
```
Returns alerts and exceptions:
- Low inventory warnings
- Delayed orders
- Shipment exceptions
- Overdue invoices
- Pending returns
- Missed appointments

## Database Models

Each system has dedicated models:

### WMS (wms_models.py)
- `Inventory`: Stock levels and locations
- `PickingTask`: Warehouse picking operations
- `WarehouseMetrics`: Daily operational metrics

### OMS (oms_models.py)
- `Order`: Customer orders
- `OrderLine`: Order line items
- `OrderMetrics`: Fulfillment metrics

### TMS (tms_models.py)
- `Shipment`: Shipment tracking
- `Route`: Delivery routes
- `TransportMetrics`: Transportation KPIs

### Billing (billing_models.py)
- `Invoice`: Customer invoices
- `BillingLineItem`: Invoice line items
- `BillingMetrics`: Revenue and collections

### Returns (returns_models.py)
- `Return`: Product returns
- `ReturnLineItem`: Returned items
- `ReturnMetrics`: Returns processing KPIs

### Yard (yard_models.py)
- `DockAppointment`: Dock scheduling
- `YardLocation`: Trailer parking
- `YardMetrics`: Yard operations KPIs

## Configuration

Edit `.env` file:

```env
# Application
APP_NAME="E-commerce Fulfillment Control Tower"
APP_VERSION="1.0.0"
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
API_PREFIX=/api/v1
CORS_ORIGINS=http://localhost:3000,http://localhost:5173
```

## Seed Data

The seed script generates realistic sample data:

```bash
python scripts/seed_data.py
```

Generates:
- 100 inventory items
- 150 orders with line items
- 150 shipments
- 100 invoices
- 50 returns
- 80 dock appointments
- 60 yard locations
- 30 days of metrics for each system

## Error Handling

The API includes:
- Structured logging
- HTTP exception handling
- Database error handling
- Validation with Pydantic
- CORS configuration

## Logging

Logs are output to console with format:
```
YYYY-MM-DD HH:MM:SS - module - LEVEL - message
```

Configure log level in `.env`:
- DEBUG
- INFO
- WARNING
- ERROR
- CRITICAL

## Development Tips

1. **Auto-reload**: Run `python main.py` for automatic reloading on code changes

2. **API Testing**: Use the Swagger UI at `/api/docs` for interactive testing

3. **Database Reset**: Delete the `data/` folder and run `seed_data.py` to reset databases

4. **Custom Data**: Modify `scripts/seed_data.py` to customize sample data

5. **Add Endpoints**: Create new endpoints in `main.py` and use `dashboard_service` for data access

## Production Considerations

- Set `DEBUG=False` in production
- Use environment variables for sensitive data
- Implement authentication/authorization
- Add rate limiting
- Use connection pooling for databases
- Implement caching (Redis)
- Set up monitoring and alerting
- Use gunicorn or uvicorn with multiple workers
- Implement backup strategy for databases
