"""Test what context is actually being built."""
import sys
sys.path.insert(0, '.')

from services.chat_service import SNAPaiChatService
from config import settings

# Initialize
chat_service = SNAPaiChatService(
    api_url=settings.chat_api_url,
    model_name=settings.chat_model_name
)

# Gather data
print("🔍 Gathering data...")
shipments = chat_service.get_shipment_details()
orders = chat_service.get_order_details()
inventory = chat_service.get_inventory_status()
exceptions = chat_service.get_exceptions()
billing = chat_service.get_billing_summary()
accessorial = chat_service.get_accessorial_charges()

# Build context manually (same as in chat method)
context = "You are SNAPai, a 3PL supply chain AI assistant.\n\n"

# Accessorial Charges
if accessorial['total_recoverable'] > 0:
    context += f"ACCESSORIAL CHARGES:\n"
    context += f"- Total Recoverable: ${accessorial['total_recoverable']:,.2f}\n"
    context += f"- Pending: ${accessorial['pending_amount']:,.2f} | Billed: ${accessorial['billed_amount']:,.2f}\n"
    context += f"- Opportunities: {accessorial['opportunity_count']}\n"
    if accessorial['top_opportunities']:
        context += "Top charges:\n"
        for opp in accessorial['top_opportunities'][:3]:
            context += f"  • {opp['charge_id']}: {opp['charge_type']} | ${opp['amount']:.2f} | {opp['carrier']} ({opp['status']})\n"

# Billing
if billing['total_outstanding'] > 0:
    context += f"\nBILLING:\n"
    context += f"- Outstanding: ${billing['total_outstanding']:,.2f} | Overdue: {billing['overdue_count']} invoices\n"

# Delayed Shipments
delayed = [s for s in shipments['shipments'] if s['status'] in ['delayed', 'exception']]
if delayed:
    context += f"\nDELAYED SHIPMENTS ({len(delayed)}):\n"
    for s in delayed[:3]:
        context += f"- {s['shipment_id']}: {s['status']} | {s['origin']}→{s['destination']} | Carrier: {s['carrier']}\n"

context += "\nAnswer concisely based on this data."

print("\n" + "=" * 60)
print("📤 CONTEXT THAT SHOULD BE SENT TO LLM:")
print("=" * 60)
print(context)
print("=" * 60)
print(f"\nContext length: {len(context)} characters")
print(f"\nAccessorial recoverable from data: ${accessorial['total_recoverable']:,.2f}")
