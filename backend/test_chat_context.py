"""Test chat service context building."""
import sys
sys.path.insert(0, '.')

from services.chat_service import SNAPaiChatService
from config import settings

print("🧪 Testing Chat Service Context\n")
print("=" * 60)

# Initialize chat service
chat_service = SNAPaiChatService(
    api_url=settings.chat_api_url,
    model_name=settings.chat_model_name
)

# Test accessorial charges
print("\n📊 Accessorial Charges:")
accessorial = chat_service.get_accessorial_charges()
print(f"  Total Recoverable: ${accessorial['total_recoverable']:,.2f}")
print(f"  Opportunities: {accessorial['opportunity_count']}")
print(f"  Top 3 charges:")
for opp in accessorial['top_opportunities'][:3]:
    print(f"    • {opp['charge_id']}: {opp['charge_type']} | ${opp['amount']:.2f} | {opp['carrier']}")

# Test billing
print("\n💰 Billing Summary:")
billing = chat_service.get_billing_summary()
print(f"  Outstanding: ${billing['total_outstanding']:,.2f}")
print(f"  Overdue: {billing['overdue_count']} invoices")

# Test shipments
print("\n🚚 Shipments:")
shipments = chat_service.get_shipment_details()
delayed = [s for s in shipments['shipments'] if s['status'] in ['delayed', 'exception']]
print(f"  Delayed: {len(delayed)}")
for s in delayed[:2]:
    print(f"    • {s['shipment_id']}: {s['origin']} → {s['destination']}")

print("\n" + "=" * 60)
print("✅ Context data is available!")
