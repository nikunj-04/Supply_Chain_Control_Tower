"""Test script to show what context is sent to LLM"""
from services.chat_service import SNAPaiChatService
from config import settings

# Create service
svc = SNAPaiChatService(settings.chat_api_url, settings.chat_model_name)

# Gather data
print("Gathering data from databases...")
shipments = svc.get_shipment_details()
orders = svc.get_order_details()
inventory = svc.get_inventory_status()
exceptions = svc.get_exceptions()

print(f"\n✅ Data Gathered:")
print(f"  - Shipments: {len(shipments['shipments'])} total")
delayed = [s for s in shipments['shipments'] if s['status'] in ['delayed', 'exception']]
print(f"  - Delayed/Exception: {len(delayed)}")
print(f"  - Orders: {len(orders['orders'])}")
print(f"  - Low Stock: {len(inventory['low_stock_items'])}")
print(f"  - Exceptions: {len(exceptions['exceptions'])}")

print("\n" + "="*60)
print("CONTEXT SENT TO LLM:")
print("="*60)

# Build context (same as in chat method)
context = "You are SNAPai, a 3PL supply chain AI assistant.\n\n"

if delayed:
    context += f"DELAYED SHIPMENTS ({len(delayed)}):\n"
    for s in delayed[:3]:
        context += f"- {s['shipment_id']}: {s['status']} | {s['origin']}→{s['destination']} | Carrier: {s['carrier']}\n"

if orders['orders']:
    context += f"\nRECENT ORDERS ({len(orders['orders'])}):\n"
    for o in orders['orders'][:3]:
        context += f"- {o['order_id']}: {o['status']} | {o['customer_name']} | ${o['total_value']:.0f}\n"

if inventory['low_stock_items']:
    context += f"\nLOW STOCK ({len(inventory['low_stock_items'])}):\n"
    for i in inventory['low_stock_items'][:3]:
        context += f"- {i['sku']}: {i['quantity_on_hand']} units (need {i['reorder_point']})\n"

if exceptions['exceptions']:
    context += f"\nEXCEPTIONS ({len(exceptions['exceptions'])}):\n"
    for e in exceptions['exceptions'][:2]:
        context += f"- {e['type']}: {e['description'][:50]}...\n"

context += "\nAnswer concisely based on this data."

print(context)
print("="*60)
print(f"Context Length: {len(context)} characters")
print("="*60)
