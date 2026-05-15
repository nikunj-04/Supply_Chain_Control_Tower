# SNAPai Chatbot Integration

## Overview
SNAPai is an AI-powered chatbot that answers supply chain questions using real-time operational data from your E-commerce Fulfillment Control Tower.

## How It Works

1. **Data Gathering**: When you ask a question, SNAPai gathers current data from all systems:
   - Recent shipments (status, delays, carriers)
   - Current orders (pending, processing, shipped)
   - Inventory levels (low stock alerts)
   - Active exceptions (issues needing attention)

2. **LLM Integration**: SNAPai sends your question + operational context to your custom LLM

3. **Response**: The LLM analyzes the data and provides intelligent answers

## Configuration

### 1. Set Up Your LLM API URL

Edit `backend/.env` and add your LLM API endpoint:

```env
CHAT_API_URL=https://your-actual-ngrok-url.ngrok-free.app/v1/chat/completions
CHAT_MODEL_NAME=blank
```

### 2. Restart the Backend

```bash
cd backend
.\venv\Scripts\python.exe main.py
```

## API Endpoints

### POST /api/v1/chat/message
Send a message to SNAPai and get a response.

**Request:**
```json
{
  "message": "Why is my shipment delayed?",
  "include_context": true
}
```

**Response:**
```json
{
  "response": "Based on the current data, I can see that shipment SHIP-20002 is delayed...",
  "timestamp": "2026-01-16T15:45:00.000Z"
}
```

### GET /api/v1/chat/suggestions
Get suggested questions users can ask.

**Response:**
```json
{
  "questions": [
    "Why is my shipment delayed?",
    "Show me recent orders",
    "What items are low in inventory?",
    ...
  ]
}
```

## Example Questions

SNAPai can answer questions like:

- **Shipment Tracking**: 
  - "Why is my shipment delayed?"
  - "What's the status of shipment SH12345?"
  - "Which carriers have the most delays?"

- **Order Management**:
  - "Show me recent orders"
  - "Are there any high-priority orders?"
  - "How many orders were placed today?"

- **Inventory**:
  - "What items are low in inventory?"
  - "Do we have any stockout risks?"
  - "Show me warehouse capacity"

- **Exceptions**:
  - "Are there any exceptions I should know about?"
  - "What's causing the most issues?"
  - "Show me critical problems"

## Technical Details

### LLM API Format
The service uses your LLM's API with this format (reusing your existing pattern):

```python
headers = {"Content-Type": "application/json"}
data = {
    "model": "blank",  # or your model name
    "messages": [
        {
            "role": "system",
            "content": "<operational context with live data>"
        },
        {
            "role": "user",
            "content": "<user's question>"
        }
    ]
}
response = requests.post(CHAT_API_URL, headers=headers, json=data)
ai_response = response.json()['choices'][0]['message']['content']
```

### Context Provided to LLM

SNAPai automatically gathers and formats:
- **Shipments**: ID, status, origin, destination, carrier, delivery dates
- **Orders**: ID, customer, status, value, priority
- **Inventory**: SKU, product name, stock levels, reorder points
- **Exceptions**: Type, severity, description, affected systems

Example context:
```
RECENT SHIPMENTS:
⚠️ SHIP-20002: DELAYED - Los Angeles → New York (Carrier: USPS)
   Expected: 2026-01-05
🚚 SHIP-20003: IN_TRANSIT - Chicago → Miami (Carrier: FedEx)

RECENT ORDERS:
🔴 ORD-25220: PENDING - Acme Corp ($1,234.56)
🟢 ORD-25221: SHIPPED - Widget Inc ($567.89)

LOW INVENTORY ITEMS:
📦 SKU-1049 (Widget Pro): 134 units (Reorder at: 198)
📦 SKU-1063 (Gadget Plus): 54 units (Reorder at: 107)
```

## Testing

Run the test script to verify data gathering:

```bash
cd backend
.\venv\Scripts\python.exe test_chat_service.py
```

This will:
✅ Test suggested questions
✅ Gather shipment data
✅ Gather order data
✅ Check inventory status
✅ Retrieve exceptions
✅ Test context formatting

## Next Steps

Once your LLM API URL is configured:

1. Test the API endpoint with Postman or curl:
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "What shipments are delayed?", "include_context": true}'
```

2. Build the frontend chat component

3. Add chat UI to the dashboard

## Frontend Integration (Coming Next)

The frontend will have:
- Chat icon in the header
- Floating chat window
- Message history
- Suggested questions as quick buttons
- Loading states while AI responds
- Error handling for connection issues

---

**Note**: Make sure your LLM server is running and accessible at the configured URL before using the chat feature.
