#!/usr/bin/env python3
"""Seed accessorial-charge-driving shipments and dock appointments."""

from datetime import datetime, timedelta
import random

from config import settings
from models.tms_models import get_tms_session, init_tms_db, Shipment
from models.yard_models import get_yard_session, init_yard_db, DockAppointment


CARRIERS = ["USPS", "FedEx", "DHL", "XPO Logistics"]
WAREHOUSES = ["Newark-NJ", "Jersey City-NJ", "Trenton-NJ", "Elizabeth-NJ"]


def seed_accessorial_activity():
    init_tms_db(settings.tms_db_path)
    init_yard_db(settings.yard_db_path)

    tms_session = get_tms_session(settings.tms_db_path)
    yard_session = get_yard_session(settings.yard_db_path)

    try:
        now = datetime.utcnow()
        created_shipments = []
        created_appts = []

        for idx in range(6):
            carrier = random.choice(CARRIERS)
            scheduled_pickup = now - timedelta(hours=random.randint(6, 48))
            estimated_delivery = scheduled_pickup + timedelta(days=random.randint(2, 5))
            actual_pickup = scheduled_pickup + timedelta(hours=random.randint(3, 7))
            actual_delivery = estimated_delivery + timedelta(hours=random.randint(4, 10))

            status = random.choice(["delayed", "exception"])
            if idx == 0:
                actual_delivery = None  # open exception for redelivery

            shipment = Shipment(
                shipment_id=f"SHIP-ACC-{now.strftime('%m%d%H%M%S')}-{idx}",
                order_id=f"ORD-ACC-{random.randint(10000, 99999)}",
                carrier=carrier,
                tracking_number=f"{carrier[:3].upper()}{random.randint(100000000, 999999999)}",
                status=status,
                origin=random.choice(WAREHOUSES),
                destination=f"{random.choice(['Dallas', 'Chicago', 'Atlanta', 'Phoenix'])}, {random.choice(['TX', 'IL', 'GA', 'AZ'])}",
                scheduled_pickup=scheduled_pickup,
                actual_pickup=actual_pickup,
                estimated_delivery=estimated_delivery,
                actual_delivery=actual_delivery,
                weight_lbs=random.uniform(50, 500),
                cost=random.uniform(120, 480)
            )
            tms_session.add(shipment)
            created_shipments.append(shipment.shipment_id)

        for idx in range(4):
            scheduled_time = now - timedelta(hours=random.randint(12, 72))
            expected_minutes = random.randint(60, 120)
            actual_minutes = expected_minutes + random.randint(45, 180)

            appt = DockAppointment(
                appointment_id=f"APPT-ACC-{now.strftime('%m%d%H%M%S')}-{idx}",
                dock_door=f"DOOR-{random.randint(1, 20)}",
                appointment_type=random.choice(["inbound", "outbound"]),
                carrier=random.choice(CARRIERS),
                trailer_number=f"TRL-{random.randint(1000, 9999)}",
                status="completed",
                scheduled_time=scheduled_time,
                actual_arrival=scheduled_time + timedelta(minutes=random.randint(15, 60)),
                actual_start=scheduled_time + timedelta(minutes=random.randint(20, 75)),
                actual_completion=scheduled_time + timedelta(minutes=actual_minutes),
                expected_duration_minutes=expected_minutes,
                actual_duration_minutes=actual_minutes,
            )
            yard_session.add(appt)
            created_appts.append(appt.appointment_id)

        tms_session.commit()
        yard_session.commit()
        print(f"✅ Created shipments: {', '.join(created_shipments)}")
        print(f"✅ Created dock appointments: {', '.join(created_appts)}")
    finally:
        tms_session.close()
        yard_session.close()


if __name__ == "__main__":
    seed_accessorial_activity()
