"""
Live Data Population Script for E-commerce Fulfillment Control Tower
Generates realistic incremental data changes to simulate live operations
Can be run manually or scheduled for demo purposes
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import random
from faker import Faker

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models.oms_models import Order, OrderLine
from models.tms_models import Shipment, Route
from models.wms_models import Inventory, PickingTask
from models.billing_models import Invoice, BillingLineItem
from models.returns_models import Return, ReturnLineItem
from models.yard_models import DockAppointment, YardLocation
from models.exception_models import Exception as ExceptionModel
from config import settings

fake = Faker()

class LiveDataPopulator:
    """Populates live incremental data across all systems"""
    
    def __init__(self):
        self.engines = {
            'oms': create_engine(f'sqlite:///{settings.oms_db_path}'),
            'tms': create_engine(f'sqlite:///{settings.tms_db_path}'),
            'wms': create_engine(f'sqlite:///{settings.wms_db_path}'),
            'billing': create_engine(f'sqlite:///{settings.billing_db_path}'),
            'returns': create_engine(f'sqlite:///{settings.returns_db_path}'),
            'yard': create_engine(f'sqlite:///{settings.yard_db_path}'),
            'exceptions': create_engine(f'sqlite:///data/exceptions.db')
        }
        
        self.sessions = {
            name: sessionmaker(bind=engine)()
            for name, engine in self.engines.items()
        }
        
        self.customers = ["Amazon", "Walmart", "Target", "Costco", "Best Buy", 
                         "Home Depot", "Kroger", "CVS", "Walgreens", "Lowes"]
        self.carriers = ["FedEx", "UPS", "USPS", "DHL", "XPO Logistics", 
                        "J.B. Hunt", "Schneider", "Swift Transportation"]
        self.warehouses = ["Chicago-IL", "Dallas-TX", "Los Angeles-CA", 
                          "Atlanta-GA", "Newark-NJ"]
        
    def populate_new_orders(self, count=5):
        """Create new orders"""
        print(f"\n📦 Creating {count} new orders...")
        session = self.sessions['oms']
        
        order_ids = []
        for _ in range(count):
            order_id = f"ORD-{random.randint(20000, 29999)}"
            customer = random.choice(self.customers)
            
            total_items = random.randint(1, 5)
            order = Order(
                order_id=order_id,
                customer_id=f"CUST-{random.randint(1000, 9999)}",
                customer_name=customer,
                order_date=datetime.now(),
                promised_delivery_date=datetime.now() + timedelta(days=random.randint(2, 7)),
                status=random.choice(['pending', 'processing', 'shipped']),
                priority=random.choice(['normal', 'normal', 'express', 'urgent']),
                shipping_address=f"{fake.street_address()}, {fake.city()}, {fake.state_abbr()} {fake.zipcode()}",
                total_items=total_items,
                total_value=random.uniform(100, 5000)
            )
            session.add(order)
            
            # Add order lines
            for i in range(total_items):
                qty = random.randint(1, 20)
                unit_price = random.uniform(10, 500)
                line = OrderLine(
                    order_id=order_id,
                    sku=f"SKU-{random.randint(1000, 9999)}",
                    product_name=fake.catch_phrase(),
                    quantity=qty,
                    unit_price=unit_price,
                    line_total=qty * unit_price
                )
                session.add(line)
            
            order_ids.append(order_id)
        
        session.commit()
        print(f"✅ Created {count} new orders: {', '.join(order_ids[:3])}...")
        return order_ids
    
    def progress_shipments(self):
        """Progress existing shipments along their routes"""
        print("\n🚚 Progressing shipments...")
        session = self.sessions['tms']
        
        # Get in-transit shipments
        shipments = session.query(Shipment).filter(
            Shipment.status.in_(['in_transit', 'out_for_delivery'])
        ).limit(10).all()
        
        updated = 0
        for shipment in shipments:
            # Random chance to update status
            if random.random() < 0.3:
                if shipment.status == 'in_transit':
                    shipment.status = random.choice(['in_transit', 'out_for_delivery'])
                elif shipment.status == 'out_for_delivery':
                    shipment.status = random.choice(['out_for_delivery', 'delivered'])
                
                shipment.last_update = datetime.now()
                updated += 1
        
        session.commit()
        print(f"✅ Updated {updated} shipment statuses")
    
    def create_new_shipments(self, order_ids=None):
        """Create new shipments for orders"""
        print("\n📦 Creating new shipments...")
        session = self.sessions['tms']
        
        count = random.randint(3, 7)
        shipment_ids = []
        
        for _ in range(count):
            shipment_id = f"SHIP-{random.randint(20000, 29999)}"
            carrier = random.choice(self.carriers)
            
            shipment = Shipment(
                shipment_id=shipment_id,
                order_id=order_ids[0] if order_ids else f"ORD-{random.randint(10000, 19999)}",
                carrier=carrier,
                tracking_number=f"{carrier[:3].upper()}{random.randint(100000000, 999999999)}",
                status='scheduled',
                origin=random.choice(self.warehouses),
                destination=f"{fake.city()}, {fake.state_abbr()}",
                scheduled_pickup=datetime.now() + timedelta(days=1),
                estimated_delivery=datetime.now() + timedelta(days=random.randint(3, 7)),
                weight_lbs=random.uniform(5, 500),
                cost=random.uniform(50, 500)
            )
            session.add(shipment)
            shipment_ids.append(shipment_id)
        
        session.commit()
        print(f"✅ Created {count} new shipments: {', '.join(shipment_ids[:3])}...")
    
    def update_inventory(self):
        """Update inventory levels with realistic changes"""
        print("\n📊 Updating inventory levels...")
        session = self.sessions['wms']
        
        # Get random inventory items
        items = session.query(Inventory).order_by(Inventory.id).limit(20).all()
        
        updated = 0
        for item in items:
            change = random.randint(-10, 5)  # More outbound than inbound
            new_qty = max(0, item.quantity_on_hand + change)
            item.quantity_on_hand = new_qty
            item.quantity_available = max(0, new_qty - item.quantity_reserved)
            item.last_updated = datetime.now()
            updated += 1
        
        session.commit()
        print(f"✅ Updated {updated} inventory items")
    
    def create_picking_tasks(self, order_ids=None):
        """Create new picking tasks"""
        print("\n📋 Creating picking tasks...")
        session = self.sessions['wms']
        
        count = random.randint(5, 10)
        
        for _ in range(count):
            task = PickingTask(
                order_id=order_ids[0] if order_ids else f"ORD-{random.randint(10000, 19999)}",
                sku=f"SKU-{random.randint(1000, 9999)}",
                quantity=random.randint(1, 20),
                location=f"{random.choice(['A', 'B', 'C'])}-{random.randint(1, 20)}-{random.randint(1, 5)}",
                assigned_to=fake.name(),
                status=random.choice(['pending', 'in_progress']),
                priority=random.choice(['normal', 'normal', 'high', 'urgent']),
                created_at=datetime.now()
            )
            session.add(task)
        
        session.commit()
        print(f"✅ Created {count} picking tasks")
    
    def complete_picking_tasks(self):
        """Complete some pending picking tasks"""
        print("\n✅ Completing picking tasks...")
        session = self.sessions['wms']
        
        # Get pending tasks
        tasks = session.query(PickingTask).filter(
            PickingTask.status.in_(['pending', 'in_progress'])
        ).limit(5).all()
        
        completed = 0
        for task in tasks:
            if random.random() < 0.4:
                task.status = 'completed'
                task.completed_at = datetime.now()
                completed += 1
        
        session.commit()
        print(f"✅ Completed {completed} picking tasks")
    
    def create_invoices(self):
        """Generate new invoices"""
        print("\n💰 Creating new invoices...")
        session = self.sessions['billing']
        
        count = random.randint(2, 5)
        
        for _ in range(count):
            invoice_num = f"INV-{datetime.now().strftime('%Y%m')}-{random.randint(10000, 99999)}"
            customer = random.choice(self.customers)
            subtotal = random.uniform(500, 10000)
            tax = subtotal * 0.08
            total = subtotal + tax
            
            invoice = Invoice(
                invoice_id=invoice_num,
                customer_id=f"CUST-{random.randint(1000, 9999)}",
                customer_name=customer,
                order_id=f"ORD-{random.randint(10000, 19999)}",
                invoice_date=datetime.now(),
                due_date=datetime.now() + timedelta(days=30),
                status=random.choice(['pending', 'pending', 'paid']),
                subtotal=subtotal,
                tax=tax,
                total=total,
                amount_paid=0,
                balance=total
            )
            session.add(invoice)
            
            # Add line items
            num_lines = random.randint(2, 6)
            for i in range(num_lines):
                qty = random.randint(1, 100)
                unit_price = random.uniform(5, 200)
                line = BillingLineItem(
                    invoice_id=invoice_num,
                    service_type=random.choice(['storage', 'handling', 'transportation', 'accessorial']),
                    description=fake.sentence(nb_words=6),
                    quantity=qty,
                    unit_price=unit_price,
                    line_total=qty * unit_price
                )
                session.add(line)
        
        session.commit()
        print(f"✅ Created {count} new invoices")
    
    def process_payments(self):
        """Process payments for pending invoices"""
        print("\n💳 Processing invoice payments...")
        session = self.sessions['billing']
        
        invoices = session.query(Invoice).filter(
            Invoice.status.in_(['pending', 'sent', 'overdue'])
        ).limit(5).all()
        
        paid = 0
        for invoice in invoices:
            if random.random() < 0.3:
                invoice.amount_paid = invoice.total
                invoice.balance = 0
                invoice.status = 'paid'
                invoice.payment_date = datetime.now()
                paid += 1
        
        session.commit()
        print(f"✅ Processed {paid} invoice payments")
    
    def create_returns(self):
        """Create new return requests"""
        print("\n↩️ Creating return requests...")
        session = self.sessions['returns']
        
        count = random.randint(1, 3)
        
        for _ in range(count):
            rma = f"RMA-{random.randint(100000, 999999)}"
            
            return_obj = Return(
                return_id=rma,
                order_id=f"ORD-{random.randint(10000, 19999)}",
                customer_id=f"CUST-{random.randint(1000, 9999)}",
                customer_name=random.choice(self.customers),
                return_date=datetime.now(),
                status='initiated',
                reason=random.choice(['damaged', 'wrong_item', 'defective', 'not_needed']),
                total_value=random.uniform(50, 500),
                refund_amount=random.uniform(50, 500),
                refund_status='pending'
            )
            session.add(return_obj)
            
            # Add return line items
            num_lines = random.randint(1, 3)
            for i in range(num_lines):
                qty = random.randint(1, 5)
                line = ReturnLineItem(
                    return_id=rma,
                    sku=f"SKU-{random.randint(1000, 9999)}",
                    product_name=fake.catch_phrase(),
                    quantity=qty,
                    condition=random.choice(['resaleable', 'damaged', 'defective']),
                    restocking_fee=random.uniform(0, 20)
                )
                session.add(line)
        
        session.commit()
        print(f"✅ Created {count} return requests")
    
    def create_exceptions(self):
        """Create new exceptions/alerts"""
        print("\n⚠️ Creating exceptions...")
        session = self.sessions['exceptions']
        
        count = random.randint(1, 4)
        exception_types = [
            ('delay', 'Shipment Delay', 'critical', 'shipment'),
            ('inventory', 'Low Inventory Alert', 'warning', 'inventory'),
            ('quality', 'Quality Issue', 'critical', 'order'),
            ('billing', 'Invoice Overdue', 'warning', 'invoice'),
        ]
        
        for _ in range(count):
            exc_type, title, severity, entity_type = random.choice(exception_types)
            
            exception = ExceptionModel(
                exception_id=f"EXC-{random.randint(100000, 999999)}",
                exception_type=exc_type,
                severity=severity,
                title=title,
                description=fake.sentence(nb_words=12),
                source_system=random.choice(['WMS', 'TMS', 'OMS', 'Billing']),
                entity_type=entity_type,
                entity_id=f"REF-{random.randint(10000, 99999)}",
                status='open',
                detected_at=datetime.now(),
                customer=random.choice(self.customers),
                cost_impact=random.uniform(100, 5000)
            )
            session.add(exception)
        
        session.commit()
        print(f"✅ Created {count} exceptions")
    
    def create_dock_appointments(self):
        """Create new dock appointments"""
        print("\n🚪 Creating dock appointments...")
        session = self.sessions['yard']
        
        count = random.randint(2, 5)
        
        for _ in range(count):
            appointment_time = datetime.now() + timedelta(hours=random.randint(2, 48))
            
            appt = DockAppointment(
                appointment_id=f"APPT-{random.randint(100000, 999999)}",
                dock_door=f"DOOR-{random.randint(1, 20)}",
                appointment_type=random.choice(['inbound', 'outbound']),
                carrier=random.choice(self.carriers),
                trailer_number=f"TRL-{random.randint(1000, 9999)}",
                status='scheduled',
                scheduled_time=appointment_time,
                expected_duration_minutes=random.randint(30, 180)
            )
            session.add(appt)
        
        session.commit()
        print(f"✅ Created {count} dock appointments")
    
    def populate_all(self):
        """Run all population tasks"""
        print("=" * 60)
        print(f"🚀 Starting Live Data Population - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        try:
            # Create new orders first
            order_ids = self.populate_new_orders(count=random.randint(3, 7))
            
            # Create related data
            self.create_new_shipments(order_ids)
            self.progress_shipments()
            self.update_inventory()
            self.create_picking_tasks(order_ids)
            self.complete_picking_tasks()
            self.create_invoices()
            self.process_payments()
            self.create_returns()
            self.create_exceptions()
            self.create_dock_appointments()
            
            print("\n" + "=" * 60)
            print("✅ Live data population completed successfully!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error during population: {e}")
            raise
        finally:
            self.close_sessions()
    
    def close_sessions(self):
        """Close all database sessions"""
        for session in self.sessions.values():
            session.close()

def main():
    """Main entry point"""
    populator = LiveDataPopulator()
    populator.populate_all()

if __name__ == "__main__":
    main()
