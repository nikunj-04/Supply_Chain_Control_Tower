"""Test SNAPai chat service."""
import sys
sys.path.append('.')

from services.chat_service import SNAPaiChatService

# Create chat service with dummy URL (will fail to connect, but we can test the data gathering)
chat_service = SNAPaiChatService(
    api_url="http://dummy-url/v1/chat/completions",
    model_name="blank"
)

print("=" * 60)
print("SNAPai Chat Service Test")
print("=" * 60)

print("\n1. Testing suggested questions...")
questions = chat_service.get_suggested_questions()
print(f"✅ Got {len(questions)} suggested questions:")
for i, q in enumerate(questions[:5], 1):
    print(f"   {i}. {q}")

print("\n2. Testing shipment details gathering...")
shipments = chat_service.get_shipment_details()
print(f"✅ Found {len(shipments.get('shipments', []))} shipments")
if shipments['shipments']:
    print(f"   Sample: {shipments['shipments'][0]['shipment_id']} - {shipments['shipments'][0]['status']}")

print("\n3. Testing order details gathering...")
orders = chat_service.get_order_details()
print(f"✅ Found {len(orders.get('orders', []))} orders")
if orders['orders']:
    print(f"   Sample: {orders['orders'][0]['order_id']} - {orders['orders'][0]['status']}")

print("\n4. Testing inventory status...")
inventory = chat_service.get_inventory_status()
print(f"✅ Found {len(inventory.get('low_stock_items', []))} low stock items")

print("\n5. Testing exceptions gathering...")
exceptions = chat_service.get_exceptions()
print(f"✅ Found {len(exceptions.get('exceptions', []))} exceptions")

print("\n6. Testing context formatting...")
context_parts = []
if shipments['shipments']:
    formatted = chat_service._format_shipments(shipments['shipments'][:2])
    print(f"✅ Shipment formatting works:")
    print(f"   {formatted[:100]}...")

print("\n" + "=" * 60)
print("✅ All data gathering tests passed!")
print("=" * 60)
print("\n📝 Note: LLM API connection will work once you configure:")
print("   CHAT_API_URL in .env file with your actual ngrok URL")
print("=" * 60)
