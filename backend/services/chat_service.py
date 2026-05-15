"""8NAPAI Chat Service - AI Assistant for Supply Chain Questions."""
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func

from config import settings
from models.oms_models import Order, get_oms_session
from models.tms_models import Shipment, get_tms_session
from models.wms_models import Inventory, PickingTask, get_wms_session
from models.billing_models import Invoice, get_billing_session
from models.returns_models import Return, get_returns_session
from models.yard_models import DockAppointment, get_yard_session
from services.exception_service import ExceptionService
from services.dashboard_service import dashboard_service


class SNAPaiChatService:
    """Chat service for 8NAPAI assistant."""
    
    def __init__(self, api_url: str, model_name: str = "blank"):
        """
        Initialize chat service.
        
        Args:
            api_url: LLM API endpoint URL
            model_name: Model name to use
        """
        self.api_url = api_url
        self.model_name = model_name
        self.exception_service = ExceptionService()
        
        # Debug: Print configuration
        print(f"🤖 8NAPAI Chat Service initialized:")
        print(f"   API URL: {self.api_url}")
        print(f"   Model: '{self.model_name}'")
    
    def get_shipment_details(self, shipment_id: Optional[str] = None) -> Dict[str, Any]:
        """Get shipment details for context."""
        session = get_tms_session(settings.tms_db_path)
        try:
            query = session.query(Shipment)
            
            if shipment_id:
                shipments = query.filter(Shipment.shipment_id == shipment_id).all()
            else:
                # Get recent shipments with issues (limit to 5 for faster response)
                shipments = query.filter(
                    Shipment.status.in_(['delayed', 'exception', 'in_transit'])
                ).limit(5).all()
            
            shipment_data = []
            for s in shipments:
                shipment_data.append({
                    'shipment_id': s.shipment_id,
                    'status': s.status,
                    'origin': s.origin,
                    'destination': s.destination,
                    'scheduled_pickup': s.scheduled_pickup.isoformat() if s.scheduled_pickup else None,
                    'estimated_delivery': s.estimated_delivery.isoformat() if s.estimated_delivery else None,
                    'actual_delivery': s.actual_delivery.isoformat() if s.actual_delivery else None,
                    'carrier': s.carrier,
                    'tracking_number': s.tracking_number
                })
            
            return {'shipments': shipment_data}
        finally:
            session.close()
    
    def get_order_details(self, order_id: Optional[str] = None) -> Dict[str, Any]:
        """Get order details for context."""
        session = get_oms_session(settings.oms_db_path)
        try:
            query = session.query(Order)
            
            if order_id:
                orders = query.filter(Order.order_id == order_id).all()
            else:
                # Get recent orders (limit to 5)
                orders = query.order_by(Order.order_date.desc()).limit(5).all()
            
            order_data = []
            for o in orders:
                order_data.append({
                    'order_id': o.order_id,
                    'customer_name': o.customer_name,
                    'status': o.status,
                    'order_date': o.order_date.isoformat() if o.order_date else None,
                    'total_value': float(o.total_value) if o.total_value else 0,
                    'priority': o.priority
                })
            
            return {'orders': order_data}
        finally:
            session.close()
    
    def get_inventory_status(self) -> Dict[str, Any]:
        """Get inventory status for context."""
        session = get_wms_session(settings.wms_db_path)
        try:
            # Get low stock items (limit to 5)
            low_stock = session.query(Inventory).filter(
                Inventory.quantity_on_hand < Inventory.reorder_point
            ).limit(5).all()
            
            inventory_data = []
            for item in low_stock:
                inventory_data.append({
                    'sku': item.sku,
                    'product_name': item.product_name,
                    'quantity_on_hand': item.quantity_on_hand,
                    'reorder_point': item.reorder_point,
                    'warehouse_location': item.warehouse_location
                })
            
            return {'low_stock_items': inventory_data}
        finally:
            session.close()
    
    def get_exceptions(self) -> Dict[str, Any]:
        """Get current exceptions."""
        try:
            exceptions_data = self.exception_service.detect_exceptions()
            
            exception_list = []
            for exc in exceptions_data.get('exceptions', [])[:5]:  # Limit to 5
                exception_list.append({
                    'exception_id': exc.get('id', 'N/A'),
                    'type': exc.get('type', 'Unknown'),
                    'severity': exc.get('severity', 'medium'),
                    'description': exc.get('message', 'No description'),
                    'status': 'open',
                    'created_at': exc.get('timestamp', datetime.utcnow().isoformat())
                })
            
            return {'exceptions': exception_list}
        except Exception as e:
            return {'exceptions': []}
    
    def get_billing_summary(self) -> Dict[str, Any]:
        """Get billing and invoice summary."""
        session = get_billing_session(settings.billing_db_path)
        try:
            # Get recent invoices (limit to 5)
            invoices = session.query(Invoice).order_by(
                Invoice.invoice_date.desc()
            ).limit(5).all()
            
            # Calculate totals
            total_outstanding = sum(inv.balance for inv in invoices)
            overdue_invoices = [inv for inv in invoices if inv.status == 'overdue']
            
            invoice_data = []
            for inv in invoices:
                invoice_data.append({
                    'invoice_id': inv.invoice_id,
                    'customer_name': inv.customer_name,
                    'total': inv.total,
                    'balance': inv.balance,
                    'status': inv.status,
                    'due_date': inv.due_date.isoformat() if inv.due_date else None
                })
            
            return {
                'invoices': invoice_data,
                'total_outstanding': total_outstanding,
                'overdue_count': len(overdue_invoices)
            }
        finally:
            session.close()
    
    def get_accessorial_charges(self) -> Dict[str, Any]:
        """Get accessorial charges recovery opportunities."""
        try:
            charges_data = dashboard_service.get_accessorial_charges()
            summary = charges_data.get('summary', {})
            opportunities = charges_data.get('opportunities', [])
            
            print(f"📊 Accessorial charges: {len(opportunities)} opportunities, ${summary.get('total_recoverable', 0):.2f} recoverable")
            
            # Get top opportunities by amount (limit to 5)
            top_opportunities = sorted(
                opportunities,
                key=lambda x: x.get('amount', 0),
                reverse=True
            )[:5]
            
            opp_data = []
            for opp in top_opportunities:
                opp_data.append({
                    'charge_id': opp.get('charge_id'),
                    'charge_type': opp.get('charge_type'),
                    'amount': opp.get('amount'),
                    'status': opp.get('status'),
                    'carrier': opp.get('carrier'),
                    'age_days': opp.get('age_days')
                })
            
            result = {
                'total_recoverable': summary.get('total_recoverable', 0),
                'pending_amount': summary.get('pending_review', 0) * 100,  # Approximate pending amount
                'billed_amount': summary.get('billed_mtd', 0) * 100,  # Approximate billed amount
                'opportunity_count': summary.get('total_opportunities', 0),
                'top_opportunities': opp_data
            }
            print(f"   Returning: {result}")
            return result
        except Exception as e:
            print(f"❌ Error getting accessorial charges: {e}")
            import traceback
            traceback.print_exc()
            return {
                'total_recoverable': 0,
                'pending_amount': 0,
                'billed_amount': 0,
                'opportunity_count': 0,
                'top_opportunities': []
            }
    
    def chat(self, user_message: str, include_context: bool = True) -> str:
        """
        Send message to LLM and get response.
        
        Args:
            user_message: User's question
            include_context: Whether to include operational context
            
        Returns:
            AI response
        """
        try:
            # Build context if needed
            context = ""
            if include_context:
                # Gather operational data
                shipments = self.get_shipment_details()
                orders = self.get_order_details()
                inventory = self.get_inventory_status()
                exceptions = self.get_exceptions()
                billing = self.get_billing_summary()
                accessorial = self.get_accessorial_charges()
                
                # Build concise context with actual data
                context = "You are 8NAPAI, a 3PL supply chain AI assistant. Answer based ONLY on the data provided below.\n\n"
                
                # Accessorial Charges Recovery (HIGHEST PRIORITY - put first)
                if accessorial['total_recoverable'] > 0:
                    context += f"💰 REVENUE RECOVERY OPPORTUNITIES:\n"
                    context += f"Accessorial Charges: ${accessorial['total_recoverable']:,.2f} CAN BE RECOVERED\n"
                    context += f"  - {accessorial['opportunity_count']} recovery opportunities identified\n"
                    context += f"  - ${accessorial['pending_amount']:,.2f} pending | ${accessorial['billed_amount']:,.2f} already billed\n"
                    if accessorial['top_opportunities']:
                        context += "  Top 3 charges:\n"
                        for opp in accessorial['top_opportunities'][:3]:
                            context += f"    • {opp['charge_id']}: ${opp['amount']:.2f} - {opp['charge_type']} - {opp['carrier']} ({opp['status']})\n"
                    context += "\n"
                
                # Billing Summary
                if billing['total_outstanding'] > 0:
                    context += f"💵 ACCOUNTS RECEIVABLE:\n"
                    context += f"  - Outstanding invoices: ${billing['total_outstanding']:,.2f}\n"
                    context += f"  - Overdue invoices: {billing['overdue_count']}\n\n"
                
                # Delayed Shipments
                delayed = [s for s in shipments['shipments'] if s['status'] in ['delayed', 'exception']]
                if delayed:
                    context += f"🚚 DELAYED SHIPMENTS ({len(delayed)}):\n"
                    for s in delayed[:3]:
                        context += f"  - {s['shipment_id']}: {s['origin']}→{s['destination']} ({s['carrier']})\n"
                    context += "\n"
                
                # Recent Orders
                if orders['orders']:
                    context += f"📦 RECENT ORDERS ({len(orders['orders'])}):\n"
                    for o in orders['orders'][:2]:
                        context += f"  - {o['order_id']}: ${o['total_value']:.0f} - {o['customer_name']}\n"
                    context += "\n"
                
                # Low Stock
                if inventory['low_stock_items']:
                    context += f"📉 LOW STOCK ITEMS ({len(inventory['low_stock_items'])}):\n"
                    for i in inventory['low_stock_items'][:2]:
                        context += f"  - {i['sku']}: {i['quantity_on_hand']} units (reorder at {i['reorder_point']})\n"
                    context += "\n"
                
                context += "Answer the user's question using ONLY the information above. Be specific with dollar amounts when they are provided."
                
                # Debug: Print context being sent
                print(f"\n📤 Context being sent to LLM ({len(context)} chars):")
                print(context)
                print("=" * 60)
            
            # Prepare messages for LLM (Ollama format with streaming disabled)
            messages = [
                {
                    "role": "system",
                    "content": context if context else "You are 8NAPAI, an AI assistant for supply chain operations."
                },
                {
                    "role": "user",
                    "content": user_message
                }
            ]
            
            # Call LLM API (Ollama format)
            headers = {"Content-Type": "application/json"}
            data = {
                "model": self.model_name,
                "messages": messages,
                "stream": False  # Disable streaming for simpler response
            }
            
            # Debug: Log the request
            print(f"📡 Calling LLM at: {self.api_url}")
            print(f"   Model: '{self.model_name}'")
            print(f"   Message: {user_message[:50]}...")
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=(10, 180)  # (connect timeout, read timeout) in seconds
            )
            response.raise_for_status()
            
            result = response.json()
            
            # Handle both OpenAI and Ollama response formats
            if 'choices' in result:
                # OpenAI format
                ai_response = result['choices'][0]['message']['content']
            elif 'message' in result:
                # Ollama format
                ai_response = result['message']['content']
            else:
                ai_response = str(result)
            
            return ai_response
            
        except requests.exceptions.RequestException as e:
            return f"Error connecting to AI service: {str(e)}"
        except Exception as e:
            return f"Error processing request: {str(e)}"
    
    def _format_shipments(self, shipments: list) -> str:
        """Format shipments for context."""
        if not shipments:
            return "No recent shipments found."
        
        lines = []
        for s in shipments:
            status_icon = "⚠️" if s['status'] in ['delayed', 'exception'] else "🚚"
            lines.append(
                f"{status_icon} {s['shipment_id']}: {s['status'].upper()} - "
                f"{s['origin']} → {s['destination']} (Carrier: {s['carrier']})"
            )
            if s['estimated_delivery'] and s['status'] == 'delayed':
                lines.append(f"   Expected: {s['estimated_delivery']}")
        
        return "\n".join(lines)
    
    def _format_orders(self, orders: list) -> str:
        """Format orders for context."""
        if not orders:
            return "No recent orders found."
        
        lines = []
        for o in orders:
            priority_icon = "🔴" if o['priority'] == 'high' else "🟢"
            lines.append(
                f"{priority_icon} {o['order_id']}: {o['status'].upper()} - "
                f"{o['customer_name']} (${o['total_value']:.2f})"
            )
        
        return "\n".join(lines)
    
    def _format_inventory(self, items: list) -> str:
        """Format inventory for context."""
        if not items:
            return "All inventory levels are healthy."
        
        lines = []
        for item in items:
            lines.append(
                f"📦 {item['sku']} ({item['product_name']}): "
                f"{item['quantity_on_hand']} units (Reorder at: {item['reorder_point']})"
            )
        
        return "\n".join(lines)
    
    def _format_exceptions(self, exceptions: list) -> str:
        """Format exceptions for context."""
        if not exceptions:
            return "No active exceptions."
        
        lines = []
        for exc in exceptions:
            severity_icon = "🔴" if exc['severity'] == 'high' else "🟡"
            lines.append(
                f"{severity_icon} {exc['exception_id']}: {exc['type']} - "
                f"{exc['description'][:60]}..."
            )
        
        return "\n".join(lines)
    
    def get_suggested_questions(self) -> list:
        """Get suggested questions for users."""
        return [
            "How much can we recover from accessorial charges?",
            "Why is my shipment delayed?",
            "Show me delayed shipments",
            "What items are low in inventory?",
            "How much is outstanding in billing?",
            "Show me overdue invoices",
            "What are the top recovery opportunities?",
            "Which carriers have the most delays?",
            "Are there any critical exceptions?",
            "Show me high-priority orders"
        ]
