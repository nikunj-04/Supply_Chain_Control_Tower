# KPI Calculation from Raw Data - Implementation Guide

## Overview

This implementation enables the LLM to **compute KPI metrics dynamically** from raw transactional data stored in the vector database, rather than pre-indexing calculated metrics.

## What Changed

### 1. **Enhanced System Prompt** ([rag_chat_service.py](backend/services/rag_chat_service.py#L77-L129))

The LLM now receives detailed instructions on how to calculate various KPIs:

#### Service Level KPIs
- **On-time ship %**: `(delivered orders where actual_delivery <= scheduled_delivery) / total delivered orders`
- **Backlog aging**: Average days between order date and current date for pending orders

#### Fulfillment KPIs
- **Pick accuracy %**: `(completed picking tasks) / (total picking tasks)`
- **Lines per hour**: Total picking tasks / total hours worked
- **Order cycle time**: Average time from order creation to shipment

#### Inventory KPIs
- **Days of inventory**: `(current quantity_on_hand) / (average daily usage)`
- **Inventory turnover**: Total orders shipped / average inventory level

#### Transportation KPIs
- **On-time delivery %**: `(shipments delivered on time) / total shipments`
- **Carrier performance**: Group by carrier and calculate on-time %

#### Returns KPIs
- **Return rate %**: `(total returns) / (total orders) * 100`
- **Return processing time**: Average days from return creation to completion

#### Dock/Yard KPIs
- **Dock utilization %**: `(scheduled appointments) / (total dock capacity)`
- **Average dwell time**: Average time between check-in and check-out

### 2. **Intelligent Context Retrieval**

```python
# Detects KPI queries using keywords
is_kpi_query = self._is_kpi_query(user_message)

# Retrieves MORE data for KPI calculations
max_results = 30 if is_kpi_query else 15  # Double the records
max_chars = 6000 if is_kpi_query else 4000  # 50% more context
```

**KPI Detection Keywords:**
- kpi, metric, performance, percentage, %
- on-time, accuracy, rate, efficiency, utilization
- average, total orders, total shipments, how many
- dashboard, analytics, trends, statistics

### 3. **Increased Response Capacity**

```python
"max_tokens": 800  # Up from 500 for detailed calculations
```

## How It Works

### Example: "What's the on-time delivery percentage?"

1. **Query Detection**: System recognizes "percentage" and "on-time" as KPI keywords
2. **Enhanced Retrieval**: Fetches 30 shipment records instead of 15
3. **LLM Calculates**: 
   - Counts shipments with `actual_delivery <= estimated_delivery`
   - Divides by total shipments
   - Returns: "Based on 42 out of 50 shipments delivered on time = 84%"

### Example: "How many delayed shipments?"

1. **Query Detection**: "how many" triggers KPI mode
2. **Data Retrieval**: Fetches shipment records with status information
3. **LLM Counts**: Filters shipments with status 'delayed' or 'exception'
4. **Returns**: "There are 8 delayed shipments out of 50 total shipments (16%)"

## What Data Is Available

The LLM has access to ALL transactional records indexed in the vector database:

| Database | Data Type | Fields Available |
|----------|-----------|------------------|
| **Billing** | Invoices | invoice_id, customer, amount, status, date, balance |
| **OMS** | Orders | order_id, customer, status, total_value, date, priority |
| **TMS** | Shipments | shipment_id, carrier, status, cost, dates, tracking |
| **WMS** | Inventory | sku, product, warehouse, quantity, reserved, available |
| **WMS** | Picking Tasks | order_id, sku, status, assigned_to, priority, timestamps |
| **Returns** | Returns | return_id, reason, status, date, amount |
| **Yard** | Appointments | trailer, carrier, status, dock, appointment_time |

## Testing

### Test via Chat Interface

Ask these questions in the chat:

```
1. "What is the on-time delivery percentage?"
2. "How many orders do we have in total?"
3. "Calculate the pick accuracy rate"
4. "What's the return rate?"
5. "Show me the average order value"
```

### Test via Python Script

```bash
cd backend
python test_kpi_calculation.py
```

## Advantages of This Approach (Option B)

✅ **No Re-indexing Required**: KPI formulas can change without rebuilding the index

✅ **Always Current**: Calculations based on latest available data in context

✅ **Flexible**: LLM can compute custom metrics on-the-fly

✅ **Transparent**: LLM shows its calculations (e.g., "45 out of 50 = 90%")

✅ **Simple Maintenance**: No separate indexing pipeline for aggregated metrics

## Limitations

⚠️ **Sample-based**: Calculations based on retrieved records (30 max), not entire database

⚠️ **Approximations**: LLM states when estimates are based on limited samples

⚠️ **Context Window**: Large datasets may exceed context limits (6000 chars max)

## Best Practices

1. **Ask Specific Questions**: "What's the on-time delivery % for UPS?" vs "How are things?"

2. **Expect Calculations**: LLM will show work: "Based on 23 out of 30 orders = 76.7%"

3. **Understand Sampling**: Results based on most relevant records, not full database

4. **Compare Trends**: Ask "How many orders last month vs this month?"

## Alternative: Option A (Not Implemented)

If you need **exact** KPIs from the **entire** database:

1. Pre-compute metrics in `dashboard_service.py`
2. Index them in `rag/indexer.py`:
```python
def index_kpi_metrics(self):
    # Get KPIs from dashboard_service
    kpis = dashboard_service.get_kpi_dashboard()
    # Create searchable text documents
    # Index them in vector store
```
3. Rebuild index: `python build_index.py`

This would provide exact KPIs but requires re-indexing when data changes.

## Summary

Your system now enables the LLM to **compute KPIs from raw transaction data** dynamically. When you ask about metrics, performance, or percentages, the system:

1. Detects it's a KPI query
2. Retrieves more records (30 vs 15)
3. Provides calculation formulas to the LLM
4. LLM computes and explains the metric

This gives you KPI insights without maintaining a separate metrics index! 🚀
