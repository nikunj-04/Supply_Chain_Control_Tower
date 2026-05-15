# E-commerce Fulfillment Control Tower - System Integration Guide

## Current Architecture Overview

### Database Structure (Current State)

The application currently uses **6 SQLite databases** as simulated legacy systems:

```
backend/data/
├── wms.db       # Warehouse Management System
├── oms.db       # Order Management System
├── tms.db       # Transportation Management System
├── billing.db   # Billing & Finance System
├── returns.db   # Returns Management System
└── yard.db      # Yard Management System
```

### Current Data Models

#### 1. **WMS (Warehouse Management System)**
- **Tables:**
  - `inventory` - SKU, product names, quantities, locations, reorder points
  - `picking_tasks` - Order picking tasks with status tracking
  - `warehouse_metrics` - Daily operational KPIs

#### 2. **OMS (Order Management System)**
- **Tables:**
  - `orders` - Customer orders with delivery dates and status
  - `order_lines` - Order line items with SKU and pricing
  - `order_metrics` - Order fulfillment KPIs

#### 3. **TMS (Transportation Management System)**
- **Tables:**
  - `shipments` - Shipment tracking with carrier info
  - `routes` - Delivery routes with driver and vehicle data
  - `transport_metrics` - Transportation performance KPIs

#### 4. **Billing System**
- **Tables:**
  - `invoices` - Customer invoices with payment status
  - `billing_line_items` - Invoice line items by service type
  - `billing_metrics` - Revenue and collection metrics

#### 5. **Returns Management**
- **Tables:**
  - `returns` - RMA tracking with disposition status
  - `return_line_items` - Return items with reason codes
  - `return_metrics` - Returns processing KPIs

#### 6. **Yard Management**
- **Tables:**
  - `dock_appointments` - Dock scheduling and slot management
  - `yard_locations` - Trailer parking and tracking
  - `yard_metrics` - Dock utilization metrics

### Current Data Generation

The system uses **Faker library** to generate realistic test data:
- 100 inventory SKUs across 3 warehouses
- 200 picking tasks with various statuses
- 150 orders with line items
- 120 shipments with carrier tracking
- 80 invoices with payment data
- 60 returns with RMA numbers
- 50 dock appointments
- 30 days of historical metrics for each system

---

## Moving to Real System Integration

### Integration Approach Options

#### **Option 1: Direct Database Integration** (Current - Not Recommended for Production)
**Pros:**
- Fast read access
- Low latency for dashboards
- Simple queries

**Cons:**
- ❌ Tight coupling to legacy database schemas
- ❌ No authentication/authorization from source systems
- ❌ Schema changes break integration
- ❌ Limited to read-only operations
- ❌ Scalability issues
- ❌ Security concerns

#### **Option 2: REST API Integration** (✅ Recommended)
Connect to existing WMS/OMS/TMS/Billing system APIs:

**Architecture:**
```
E-commerce Fulfillment Control Tower
    ↓ (API Client)
    ├── WMS API (e.g., Manhattan, HighJump, SAP EWM)
    ├── OMS API (e.g., Salesforce, Oracle, NetSuite)
    ├── TMS API (e.g., Oracle TMS, JDA, BluJay)
    └── Billing API (e.g., NetSuite, QuickBooks, SAP)
```

**Implementation:**
```python
# backend/integrations/wms_connector.py
import httpx
from typing import List, Dict

class WMSConnector:
    """Connector for WMS REST API."""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
    
    async def get_inventory(self) -> List[Dict]:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/inventory",
                headers=self.headers
            )
            return response.json()
    
    async def get_picking_tasks(self, status: str = None) -> List[Dict]:
        params = {"status": status} if status else {}
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/api/v1/picking-tasks",
                headers=self.headers,
                params=params
            )
            return response.json()
```

**Pros:**
- ✅ Loose coupling - systems are independent
- ✅ Authentication/authorization built-in
- ✅ Vendor-supported endpoints
- ✅ Can trigger actions (not just read)
- ✅ Standard HTTP protocols

**Cons:**
- Network latency
- Requires API credentials
- Rate limiting considerations
- Need error handling/retries

#### **Option 3: Data Warehouse / ETL Approach** (✅ Best for Large Scale)
Create a centralized data warehouse with scheduled ETL jobs:

**Architecture:**
```
Legacy Systems → ETL Pipeline → Data Warehouse → Control Tower
   (WMS, OMS,      (Airflow,       (PostgreSQL,     (Dashboard
    TMS, etc.)      Talend)         Snowflake)        Queries)
```

**Implementation:**
```python
# backend/etl/warehouse_loader.py
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

def extract_wms_data(**context):
    """Extract data from WMS."""
    # Connect to WMS API/DB
    # Extract inventory, tasks, metrics
    pass

def transform_data(**context):
    """Transform and normalize data."""
    # Apply business rules
    # Calculate KPIs
    # Data quality checks
    pass

def load_to_warehouse(**context):
    """Load to data warehouse."""
    # Bulk insert to PostgreSQL
    # Update materialized views
    pass

dag = DAG(
    'wms_etl',
    schedule_interval='@hourly',
    start_date=datetime(2026, 1, 1)
)
```

**Pros:**
- ✅ Optimized for analytics queries
- ✅ Historical data retention
- ✅ Data quality and governance
- ✅ Fast dashboard performance
- ✅ Scheduled refresh cycles

**Cons:**
- Infrastructure complexity
- Not real-time (scheduled updates)
- Requires data warehouse setup
- Higher operational cost

#### **Option 4: Event-Driven Integration** (✅ For Real-Time)
Use message queues/event streams for real-time updates:

**Architecture:**
```
Legacy Systems → Message Broker → Event Processors → Control Tower
   (WMS, OMS)    (Kafka, RabbitMQ)   (Consumers)      (WebSocket)
```

**Implementation:**
```python
# backend/events/consumer.py
from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'wms.inventory.updated',
    'oms.order.created',
    bootstrap_servers=['kafka:9092'],
    value_deserializer=lambda m: json.loads(m.decode('utf-8'))
)

for message in consumer:
    event = message.value
    if message.topic == 'wms.inventory.updated':
        # Update inventory cache
        update_inventory_cache(event)
    elif message.topic == 'oms.order.created':
        # Trigger workflow
        process_new_order(event)
```

**Pros:**
- ✅ Real-time updates
- ✅ Event-driven architecture
- ✅ Scalable and decoupled
- ✅ Supports complex workflows

**Cons:**
- Complex infrastructure
- Requires message broker
- Need to handle event ordering
- Monitoring complexity

---

## Recommended Integration Strategy

### **Hybrid Approach** (Best of All Worlds)

```
┌─────────────────────────────────────────────┐
│     E-commerce Fulfillment Control Tower    │
│                                             │
│  ┌───────────────────────────────────────┐ │
│  │     API Gateway / Integration Layer    │ │
│  └───────────────────────────────────────┘ │
│           │          │          │           │
└───────────┼──────────┼──────────┼───────────┘
            ↓          ↓          ↓
    ┌────────────┐ ┌────────────┐ ┌────────────┐
    │ Real-Time  │ │   Cached   │ │ Historical │
    │ APIs       │ │   Data     │ │ Data (DW)  │
    └────────────┘ └────────────┘ └────────────┘
         ↓              ↓              ↓
    WMS/OMS/TMS    Redis Cache    PostgreSQL
```

### Implementation Steps

#### **Phase 1: API Integration Layer** (Weeks 1-2)
```python
# backend/integrations/__init__.py
from .wms_connector import WMSConnector
from .oms_connector import OMSConnector
from .tms_connector import TMSConnector
from .billing_connector import BillingConnector

class IntegrationManager:
    """Central integration management."""
    
    def __init__(self, config: dict):
        self.wms = WMSConnector(
            base_url=config['wms_url'],
            api_key=config['wms_api_key']
        )
        self.oms = OMSConnector(
            base_url=config['oms_url'],
            api_key=config['oms_api_key']
        )
        # ... initialize other connectors
    
    async def get_inventory_snapshot(self):
        """Get current inventory from WMS."""
        return await self.wms.get_inventory()
```

#### **Phase 2: Caching Layer** (Weeks 3-4)
```python
# backend/cache/redis_cache.py
import redis
import json
from datetime import timedelta

class CacheManager:
    """Redis cache for frequently accessed data."""
    
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    def cache_inventory(self, data: list, ttl: int = 300):
        """Cache inventory data for 5 minutes."""
        self.redis.setex(
            'wms:inventory',
            timedelta(seconds=ttl),
            json.dumps(data)
        )
    
    def get_cached_inventory(self):
        """Get cached inventory."""
        data = self.redis.get('wms:inventory')
        return json.loads(data) if data else None
```

#### **Phase 3: Data Warehouse** (Weeks 5-8)
```python
# backend/warehouse/schema.sql
CREATE TABLE fact_inventory (
    date_key INTEGER,
    sku_key INTEGER,
    warehouse_key INTEGER,
    quantity_on_hand INTEGER,
    quantity_available INTEGER,
    quantity_reserved INTEGER,
    reorder_point INTEGER,
    last_updated TIMESTAMP
);

CREATE TABLE dim_date (
    date_key INTEGER PRIMARY KEY,
    date DATE,
    day_of_week VARCHAR(10),
    month VARCHAR(10),
    quarter INTEGER,
    year INTEGER
);
```

#### **Phase 4: Real-Time Events** (Weeks 9-12)
```python
# backend/events/stream_processor.py
from kafka import KafkaConsumer
from websockets import WebSocketServerProtocol

async def stream_events_to_dashboard(websocket: WebSocketServerProtocol):
    """Stream real-time events to dashboard."""
    consumer = KafkaConsumer('wms.events')
    
    for message in consumer:
        event = json.loads(message.value)
        await websocket.send(json.dumps({
            'type': 'inventory_update',
            'data': event
        }))
```

---

## Popular 3PL System Integrations

### **Top WMS Systems**
1. **Manhattan Associates WMS**
   - REST API: `/api/v1/inventory`, `/api/v1/tasks`
   - Authentication: OAuth 2.0
   - Documentation: developer.manh.com

2. **SAP Extended Warehouse Management (EWM)**
   - OData API
   - Authentication: Basic Auth / API Key
   - Documentation: api.sap.com

3. **HighJump / Körber WMS**
   - SOAP/REST API
   - Authentication: Token-based
   - Documentation: korber-supplychain.com/api

### **Top OMS Systems**
1. **Salesforce Commerce Cloud OMS**
   - REST API
   - Authentication: OAuth 2.0
   - Documentation: developer.salesforce.com

2. **Oracle Order Management Cloud**
   - REST API
   - Authentication: Basic Auth
   - Documentation: docs.oracle.com

3. **NetSuite SuiteCommerce**
   - RESTlet API
   - Authentication: Token-based
   - Documentation: docs.oracle.com/en/cloud/saas/netsuite

### **Top TMS Systems**
1. **Oracle Transportation Management (OTM)**
   - SOAP/REST API
   - Authentication: Basic Auth
   - Documentation: docs.oracle.com/en/industries/transportation

2. **BluJay TMS**
   - REST API
   - Authentication: API Key
   - Documentation: www.blujaysolutions.com

3. **MercuryGate TMS**
   - REST API
   - Authentication: OAuth 2.0
   - Documentation: www.mercurygate.com

---

## Configuration Template

```python
# backend/config.py (Updated)
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Application
    app_name: str = "E-commerce Fulfillment Control Tower"
    app_version: str = "2.0.0"
    
    # Integration Mode
    integration_mode: str = "api"  # "database", "api", "warehouse", "hybrid"
    
    # WMS Integration
    wms_url: str = "https://wms.company.com"
    wms_api_key: str = ""
    wms_auth_type: str = "bearer"  # "bearer", "basic", "oauth"
    
    # OMS Integration
    oms_url: str = "https://oms.company.com"
    oms_api_key: str = ""
    
    # TMS Integration
    tms_url: str = "https://tms.company.com"
    tms_api_key: str = ""
    
    # Billing Integration
    billing_url: str = "https://billing.company.com"
    billing_api_key: str = ""
    
    # Cache
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl: int = 300  # 5 minutes
    
    # Data Warehouse
    warehouse_url: str = "postgresql://user:pass@localhost/warehouse"
    
    # Legacy SQLite (Fallback)
    wms_db_path: str = "./data/wms.db"
    oms_db_path: str = "./data/oms.db"
    # ... other db paths
    
    class Config:
        env_file = ".env"
```

---

## Next Steps

### Immediate Actions:
1. **Identify Target Systems** - Which WMS, OMS, TMS are you using?
2. **Get API Documentation** - Request API docs from vendors
3. **Obtain Credentials** - Get API keys, OAuth tokens
4. **Define Data Requirements** - What data fields are needed?
5. **Choose Integration Pattern** - API, ETL, or Hybrid?

### Questions to Answer:
- What WMS/OMS/TMS systems do you currently use?
- Do they provide REST APIs? SOAP? OData?
- What's the data refresh frequency requirement? (Real-time vs. hourly)
- Do you have a data warehouse already?
- What authentication methods are supported?
- Are there rate limits on API calls?

Let me know your specific systems and I can provide detailed integration code!
