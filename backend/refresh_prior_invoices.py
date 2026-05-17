#!/usr/bin/env python3
"""Add invoices from prior 30-60 days for growth calculation."""

from datetime import datetime, timedelta
from models.billing_models import get_billing_session, Invoice, init_billing_db
from config import settings
import random

def add_prior_period_invoices():
    """Add invoices from days 30-60 for prior period in growth calculations."""
    init_billing_db(settings.billing_db_path)
    session = get_billing_session(settings.billing_db_path)
    
    try:
        now = datetime.utcnow()
        customers = [f'CUST-{i}' for i in range(1000, 1100)]
        
        added_count = 0
        # Days 30-60: prior 30-day period
        for day in range(30, 60):
            invoice_date = now - timedelta(days=day)
            # 2-4 invoices per day
            for _ in range(random.randint(2, 4)):
                customer_id = random.choice(customers)
                subtotal = random.uniform(400, 4500)  # Slightly lower than current period
                tax = subtotal * 0.08
                total = subtotal + tax
                
                invoice = Invoice(
                    invoice_id=f'INV-{invoice_date.strftime("%Y%m%d")}-{random.randint(10000, 99999)}',
                    customer_id=customer_id,
                    customer_name=f'Customer-{customer_id.split("-")[1]}',
                    order_id=f'ORD-{random.randint(10000, 99999)}',
                    invoice_date=invoice_date,
                    due_date=invoice_date + timedelta(days=30),
                    payment_date=invoice_date + timedelta(days=random.randint(5, 25)) if random.random() > 0.4 else None,
                    status=random.choice(['pending', 'paid', 'overdue']),
                    subtotal=subtotal,
                    tax=tax,
                    total=total,
                    amount_paid=total if random.random() > 0.4 else 0,
                    balance=0 if random.random() > 0.4 else total
                )
                session.add(invoice)
                added_count += 1
        
        session.commit()
        print(f'✅ Added {added_count} invoices from days 30-60 (prior period)')
    finally:
        session.close()

if __name__ == '__main__':
    add_prior_period_invoices()
