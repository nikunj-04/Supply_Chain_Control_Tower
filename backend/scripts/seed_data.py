"""Seed data generator for all systems."""
import os
import sys
from datetime import datetime, timedelta
import random
from faker import Faker

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import settings
from models.wms_models import (
    init_wms_db, get_wms_session, Inventory, PickingTask, WarehouseMetrics
)
from models.oms_models import (
    init_oms_db, get_oms_session, Order, OrderLine, OrderMetrics
)
from models.tms_models import (
    init_tms_db, get_tms_session, Shipment, Route, TransportMetrics
)
from models.billing_models import (
    init_billing_db, get_billing_session, Invoice, BillingLineItem, BillingMetrics
)
from models.returns_models import (
    init_returns_db, get_returns_session, Return, ReturnLineItem, ReturnMetrics
)
from models.yard_models import (
    init_yard_db, get_yard_session, DockAppointment, YardLocation, YardMetrics
)
from logger import setup_logger

logger = setup_logger(__name__)
fake = Faker()


def ensure_data_dir():
    """Ensure data directory exists."""
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'data')
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def seed_wms():
    """Seed WMS database."""
    logger.info("Seeding WMS database...")
    init_wms_db(settings.wms_db_path)
    session = get_wms_session(settings.wms_db_path)
    
    try:
        # Seed inventory
        products = [
            "Electronics Widget", "Consumer Gadget", "Industrial Component",
            "Office Supply", "Household Item", "Fashion Accessory",
            "Automotive Part", "Sporting Goods", "Beauty Product", "Food Item"
        ]
        warehouses = ["WH-A", "WH-B", "WH-C"]
        
        for i in range(100):
            sku = f"SKU-{1000 + i}"
            product = random.choice(products) + f" {i}"
            warehouse = random.choice(warehouses)
            on_hand = random.randint(0, 1000)
            reserved = random.randint(0, min(on_hand, 200))
            available = on_hand - reserved
            
            inventory = Inventory(
                sku=sku,
                product_name=product,
                warehouse_location=warehouse,
                quantity_on_hand=on_hand,
                quantity_reserved=reserved,
                quantity_available=available,
                reorder_point=random.randint(50, 200),
                last_updated=datetime.utcnow() - timedelta(hours=random.randint(0, 48))
            )
            session.add(inventory)
        
        # Seed picking tasks
        statuses = ["pending", "in_progress", "completed", "delayed"]
        priorities = ["low", "normal", "high", "urgent"]
        
        for i in range(200):
            order_id = f"ORD-{10000 + i}"
            created = datetime.utcnow() - timedelta(hours=random.randint(0, 72))
            status = random.choice(statuses)
            
            task = PickingTask(
                order_id=order_id,
                sku=f"SKU-{1000 + random.randint(0, 99)}",
                quantity=random.randint(1, 10),
                location=f"{random.choice(warehouses)}-{random.randint(1, 20):02d}-{random.randint(1, 50):02d}",
                status=status,
                assigned_to=fake.name() if status != "pending" else None,
                created_at=created,
                completed_at=created + timedelta(minutes=random.randint(5, 60)) if status == "completed" else None,
                priority=random.choice(priorities)
            )
            session.add(task)
        
        # Seed warehouse metrics (last 30 days)
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=29 - i)
            total_picks = random.randint(100, 300)
            completed = int(total_picks * random.uniform(0.85, 0.98))
            delayed = total_picks - completed
            
            metrics = WarehouseMetrics(
                date=date,
                total_picks=total_picks,
                picks_completed=completed,
                picks_delayed=delayed,
                avg_pick_time_minutes=random.uniform(3.5, 8.5),
                inventory_accuracy_pct=random.uniform(97.0, 99.5),
                capacity_utilization_pct=random.uniform(65.0, 85.0)
            )
            session.add(metrics)
        
        session.commit()
        logger.info("WMS database seeded successfully")
    except Exception as e:
        logger.error(f"Error seeding WMS: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def seed_oms():
    """Seed OMS database."""
    logger.info("Seeding OMS database...")
    init_oms_db(settings.oms_db_path)
    session = get_oms_session(settings.oms_db_path)
    
    try:
        statuses = ["pending", "processing", "shipped", "delivered", "cancelled"]
        priorities = ["low", "normal", "high", "urgent"]
        
        # Seed orders
        for i in range(150):
            order_id = f"ORD-{10000 + i}"
            order_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))
            status = random.choice(statuses)
            
            num_items = random.randint(1, 5)
            total_value = random.uniform(50, 2000)
            
            promised_delivery = order_date + timedelta(days=random.randint(3, 7))
            actual_delivery = None
            if status == "delivered":
                actual_delivery = order_date + timedelta(days=random.randint(2, 8))
            
            order = Order(
                order_id=order_id,
                customer_id=f"CUST-{random.randint(1000, 5000)}",
                customer_name=fake.company(),
                status=status,
                order_date=order_date,
                promised_delivery_date=promised_delivery,
                actual_delivery_date=actual_delivery,
                total_items=num_items,
                total_value=total_value,
                priority=random.choice(priorities),
                shipping_address=fake.address()
            )
            session.add(order)
            
            # Seed order lines
            for j in range(num_items):
                unit_price = random.uniform(10, 500)
                quantity = random.randint(1, 5)
                
                line = OrderLine(
                    order_id=order_id,
                    sku=f"SKU-{1000 + random.randint(0, 99)}",
                    product_name=fake.catch_phrase(),
                    quantity=quantity,
                    unit_price=unit_price,
                    line_total=unit_price * quantity
                )
                session.add(line)
        
        # Seed order metrics (last 30 days)
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=29 - i)
            total = random.randint(40, 80)
            shipped = int(total * random.uniform(0.7, 0.9))
            delivered = int(shipped * random.uniform(0.85, 0.95))
            delayed = random.randint(0, 5)
            
            metrics = OrderMetrics(
                date=date,
                total_orders=total,
                orders_shipped=shipped,
                orders_delivered=delivered,
                orders_delayed=delayed,
                on_time_delivery_pct=random.uniform(90.0, 98.0),
                avg_processing_time_hours=random.uniform(18.0, 36.0),
                order_accuracy_pct=random.uniform(96.0, 99.5)
            )
            session.add(metrics)
        
        session.commit()
        logger.info("OMS database seeded successfully")
    except Exception as e:
        logger.error(f"Error seeding OMS: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def seed_tms():
    """Seed TMS database."""
    logger.info("Seeding TMS database...")
    init_tms_db(settings.tms_db_path)
    session = get_tms_session(settings.tms_db_path)
    
    try:
        carriers = ["FedEx", "UPS", "DHL", "USPS", "OnTrac"]
        shipment_statuses = ["scheduled", "in_transit", "delivered", "delayed", "exception"]
        cities = ["New York, NY", "Los Angeles, CA", "Chicago, IL", "Houston, TX", "Phoenix, AZ"]
        
        # Seed shipments
        for i in range(150):
            shipment_id = f"SHIP-{20000 + i}"
            order_id = f"ORD-{10000 + i}"
            
            scheduled_pickup = datetime.utcnow() - timedelta(days=random.randint(0, 20))
            status = random.choice(shipment_statuses)
            
            actual_pickup = scheduled_pickup + timedelta(hours=random.randint(-2, 4)) if status != "scheduled" else None
            estimated_delivery = scheduled_pickup + timedelta(days=random.randint(2, 5))
            actual_delivery = None
            if status == "delivered":
                actual_delivery = estimated_delivery + timedelta(hours=random.randint(-12, 12))
            
            shipment = Shipment(
                shipment_id=shipment_id,
                order_id=order_id,
                carrier=random.choice(carriers),
                tracking_number=f"TRK{random.randint(1000000000, 9999999999)}",
                status=status,
                origin=random.choice(cities),
                destination=random.choice(cities),
                scheduled_pickup=scheduled_pickup,
                actual_pickup=actual_pickup,
                estimated_delivery=estimated_delivery,
                actual_delivery=actual_delivery,
                weight_lbs=random.uniform(1.0, 100.0),
                cost=random.uniform(10.0, 200.0)
            )
            session.add(shipment)
        
        # Seed routes
        route_statuses = ["planned", "active", "completed"]
        vehicles = ["VAN-001", "TRUCK-002", "VAN-003", "TRUCK-004", "VAN-005"]
        
        for i in range(30):
            route_id = f"ROUTE-{3000 + i}"
            scheduled_start = datetime.utcnow() - timedelta(days=random.randint(0, 7))
            status = random.choice(route_statuses)
            total_stops = random.randint(5, 15)
            
            route = Route(
                route_id=route_id,
                driver=fake.name(),
                vehicle=random.choice(vehicles),
                status=status,
                scheduled_start=scheduled_start,
                actual_start=scheduled_start + timedelta(minutes=random.randint(-15, 30)) if status != "planned" else None,
                scheduled_end=scheduled_start + timedelta(hours=random.randint(4, 10)),
                actual_end=scheduled_start + timedelta(hours=random.randint(4, 12)) if status == "completed" else None,
                total_stops=total_stops,
                completed_stops=total_stops if status == "completed" else random.randint(0, total_stops),
                total_distance_miles=random.uniform(50.0, 300.0)
            )
            session.add(route)
        
        # Seed transport metrics (last 30 days)
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=29 - i)
            total = random.randint(30, 70)
            on_time = int(total * random.uniform(0.85, 0.95))
            delayed = total - on_time
            
            metrics = TransportMetrics(
                date=date,
                total_shipments=total,
                on_time_deliveries=on_time,
                delayed_shipments=delayed,
                on_time_delivery_pct=random.uniform(88.0, 96.0),
                avg_transit_time_hours=random.uniform(40.0, 60.0),
                total_transport_cost=random.uniform(2000.0, 5000.0),
                cost_per_shipment=random.uniform(50.0, 120.0)
            )
            session.add(metrics)
        
        session.commit()
        logger.info("TMS database seeded successfully")
    except Exception as e:
        logger.error(f"Error seeding TMS: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def seed_billing():
    """Seed Billing database."""
    logger.info("Seeding Billing database...")
    init_billing_db(settings.billing_db_path)
    session = get_billing_session(settings.billing_db_path)
    
    try:
        statuses = ["pending", "paid", "overdue", "disputed"]
        service_types = ["storage", "picking", "packing", "shipping", "handling"]
        
        # Seed invoices
        for i in range(100):
            invoice_id = f"INV-{30000 + i}"
            order_id = f"ORD-{10000 + i}"
            
            invoice_date = datetime.utcnow() - timedelta(days=random.randint(0, 60))
            due_date = invoice_date + timedelta(days=30)
            status = random.choice(statuses)
            
            subtotal = random.uniform(100.0, 5000.0)
            tax = subtotal * 0.08
            total = subtotal + tax
            
            amount_paid = 0.0
            payment_date = None
            if status == "paid":
                amount_paid = total
                payment_date = invoice_date + timedelta(days=random.randint(5, 25))
            elif status == "overdue":
                amount_paid = 0.0
            
            invoice = Invoice(
                invoice_id=invoice_id,
                customer_id=f"CUST-{random.randint(1000, 5000)}",
                customer_name=fake.company(),
                order_id=order_id,
                invoice_date=invoice_date,
                due_date=due_date,
                payment_date=payment_date,
                status=status,
                subtotal=subtotal,
                tax=tax,
                total=total,
                amount_paid=amount_paid,
                balance=total - amount_paid
            )
            session.add(invoice)
            
            # Seed billing line items
            num_items = random.randint(3, 8)
            for j in range(num_items):
                service = random.choice(service_types)
                quantity = random.uniform(1.0, 100.0)
                unit_price = random.uniform(0.5, 50.0)
                
                line = BillingLineItem(
                    invoice_id=invoice_id,
                    service_type=service,
                    description=f"{service.replace('_', ' ').title()} services",
                    quantity=quantity,
                    unit_price=unit_price,
                    line_total=quantity * unit_price
                )
                session.add(line)
        
        # Seed billing metrics (last 30 days)
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=29 - i)
            total = random.randint(20, 50)
            paid = int(total * random.uniform(0.7, 0.9))
            overdue = random.randint(0, 5)
            
            total_rev = random.uniform(10000.0, 30000.0)
            collected = total_rev * random.uniform(0.85, 0.98)
            
            metrics = BillingMetrics(
                date=date,
                total_invoices=total,
                invoices_paid=paid,
                invoices_overdue=overdue,
                total_revenue=total_rev,
                revenue_collected=collected,
                outstanding_balance=total_rev - collected,
                collection_rate_pct=random.uniform(92.0, 98.0)
            )
            session.add(metrics)
        
        session.commit()
        logger.info("Billing database seeded successfully")
    except Exception as e:
        logger.error(f"Error seeding Billing: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def seed_returns():
    """Seed Returns database."""
    logger.info("Seeding Returns database...")
    init_returns_db(settings.returns_db_path)
    session = get_returns_session(settings.returns_db_path)
    
    try:
        statuses = ["initiated", "in_transit", "received", "inspected", "processed", "refunded"]
        reasons = ["damaged", "wrong_item", "defective", "not_needed", "size_issue"]
        conditions = ["resaleable", "damaged", "defective"]
        refund_statuses = ["pending", "approved", "refunded"]
        
        # Seed returns
        for i in range(50):
            return_id = f"RET-{40000 + i}"
            order_id = f"ORD-{10000 + i}"
            
            return_date = datetime.utcnow() - timedelta(days=random.randint(0, 30))
            status = random.choice(statuses)
            
            received_date = None
            processed_date = None
            if status in ["received", "inspected", "processed", "refunded"]:
                received_date = return_date + timedelta(days=random.randint(2, 5))
            if status in ["processed", "refunded"]:
                processed_date = received_date + timedelta(days=random.randint(1, 3))
            
            total_value = random.uniform(50.0, 500.0)
            refund_amount = total_value * random.uniform(0.8, 1.0)
            
            ret = Return(
                return_id=return_id,
                order_id=order_id,
                customer_id=f"CUST-{random.randint(1000, 5000)}",
                customer_name=fake.company(),
                status=status,
                reason=random.choice(reasons),
                return_date=return_date,
                received_date=received_date,
                processed_date=processed_date,
                total_value=total_value,
                refund_amount=refund_amount,
                refund_status=random.choice(refund_statuses)
            )
            session.add(ret)
            
            # Seed return line items
            num_items = random.randint(1, 3)
            for j in range(num_items):
                line = ReturnLineItem(
                    return_id=return_id,
                    sku=f"SKU-{1000 + random.randint(0, 99)}",
                    product_name=fake.catch_phrase(),
                    quantity=random.randint(1, 3),
                    condition=random.choice(conditions),
                    restocking_fee=random.uniform(0.0, 20.0)
                )
                session.add(line)
        
        # Seed return metrics (last 30 days)
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=29 - i)
            total = random.randint(10, 30)
            processed = int(total * random.uniform(0.7, 0.9))
            pending = total - processed
            
            metrics = ReturnMetrics(
                date=date,
                total_returns=total,
                returns_processed=processed,
                returns_pending=pending,
                return_rate_pct=random.uniform(3.0, 7.0),
                avg_processing_time_days=random.uniform(2.5, 5.0),
                total_refund_amount=random.uniform(1000.0, 5000.0),
                resaleable_rate_pct=random.uniform(60.0, 80.0)
            )
            session.add(metrics)
        
        session.commit()
        logger.info("Returns database seeded successfully")
    except Exception as e:
        logger.error(f"Error seeding Returns: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def seed_yard():
    """Seed Yard database."""
    logger.info("Seeding Yard database...")
    init_yard_db(settings.yard_db_path)
    session = get_yard_session(settings.yard_db_path)
    
    try:
        appointment_statuses = ["scheduled", "checked_in", "loading", "unloading", "completed", "missed"]
        appointment_types = ["inbound", "outbound"]
        carriers = ["FedEx", "UPS", "DHL", "XPO Logistics", "Old Dominion"]
        
        # Seed dock appointments
        for i in range(80):
            appointment_id = f"APPT-{50000 + i}"
            scheduled_time = datetime.utcnow() - timedelta(days=random.randint(0, 7))
            status = random.choice(appointment_statuses)
            expected_duration = random.randint(30, 90)
            
            actual_arrival = None
            actual_start = None
            actual_completion = None
            actual_duration = None
            
            if status != "scheduled":
                actual_arrival = scheduled_time + timedelta(minutes=random.randint(-15, 30))
                actual_start = actual_arrival + timedelta(minutes=random.randint(5, 20))
            
            if status == "completed":
                actual_completion = actual_start + timedelta(minutes=random.randint(25, 100))
                actual_duration = int((actual_completion - actual_start).total_seconds() / 60)
            
            appt = DockAppointment(
                appointment_id=appointment_id,
                dock_door=f"DOCK-{random.randint(1, 12):02d}",
                appointment_type=random.choice(appointment_types),
                carrier=random.choice(carriers),
                trailer_number=f"TRL-{random.randint(10000, 99999)}",
                status=status,
                scheduled_time=scheduled_time,
                actual_arrival=actual_arrival,
                actual_start=actual_start,
                actual_completion=actual_completion,
                expected_duration_minutes=expected_duration,
                actual_duration_minutes=actual_duration
            )
            session.add(appt)
        
        # Seed yard locations
        zones = ["A", "B", "C", "D"]
        location_statuses = ["occupied", "available", "reserved", "maintenance"]
        contents_types = ["inbound_freight", "outbound_freight", "empty", "maintenance"]
        
        for zone in zones:
            for i in range(15):
                location_id = f"{zone}-{i+1:02d}"
                status = random.choice(location_statuses)
                
                trailer_number = None
                carrier = None
                check_in_time = None
                expected_departure = None
                contents = None
                
                if status == "occupied":
                    trailer_number = f"TRL-{random.randint(10000, 99999)}"
                    carrier = random.choice(carriers)
                    check_in_time = datetime.utcnow() - timedelta(hours=random.randint(1, 72))
                    expected_departure = datetime.utcnow() + timedelta(hours=random.randint(4, 48))
                    contents = random.choice(contents_types[:2])
                
                location = YardLocation(
                    location_id=location_id,
                    zone=zone,
                    status=status,
                    trailer_number=trailer_number,
                    carrier=carrier,
                    check_in_time=check_in_time,
                    expected_departure=expected_departure,
                    contents=contents
                )
                session.add(location)
        
        # Seed yard metrics (last 30 days)
        for i in range(30):
            date = datetime.utcnow() - timedelta(days=29 - i)
            total = random.randint(15, 35)
            completed = int(total * random.uniform(0.85, 0.95))
            missed = total - completed
            
            metrics = YardMetrics(
                date=date,
                total_appointments=total,
                appointments_completed=completed,
                appointments_missed=missed,
                on_time_arrival_pct=random.uniform(82.0, 92.0),
                avg_dock_time_minutes=random.uniform(35.0, 55.0),
                yard_capacity=60,
                yard_occupied=random.randint(30, 50),
                yard_utilization_pct=random.uniform(50.0, 85.0)
            )
            session.add(metrics)
        
        session.commit()
        logger.info("Yard database seeded successfully")
    except Exception as e:
        logger.error(f"Error seeding Yard: {e}")
        session.rollback()
        raise
    finally:
        session.close()


def main():
    """Main seed function."""
    logger.info("Starting database seeding...")
    ensure_data_dir()
    
    try:
        seed_wms()
        seed_oms()
        seed_tms()
        seed_billing()
        seed_returns()
        seed_yard()
        logger.info("All databases seeded successfully!")
    except Exception as e:
        logger.error(f"Seeding failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
