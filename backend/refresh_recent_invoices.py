#!/usr/bin/env python3
"""Add fresh invoices from last 30 days to billing database."""

from datetime import datetime, timedelta
from models.billing_models import get_billing_session, Invoice, init_billing_db
from config import settings
import random

def add_recent_invoices():
    """Add invoices from last 30 days for profitability data."""
    init_billing_db(settings.billing_db_path)
    session = get_billing_session(settings.billing_db_path)
    
    try:
        # Add invoices from last 30 days for various customers
        now = datetime.utcnow()
        customers = [f'CUST-{i}' for i in range(1000, 1100)]  # 100 customer IDs
        
        added_count = 0
        for day in range(30):
            invoice_date = now - timedelta(days=day)
            # 3-5 invoices per day
            for _ in range(random.randint(3, 5)):
                customer_id = random.choice(customers)
                subtotal = random.uniform(500, 5000)
                tax = subtotal * 0.08
                total = subtotal + tax
                
                invoice = Invoice(
                    invoice_id=f'INV-{invoice_date.strftime("%Y%m%d")}-{random.randint(10000, 99999)}',
                    customer_id=customer_id,
                    customer_name=f'Customer-{customer_id.split("-")[1]}',
                    order_id=f'ORD-{random.randint(10000, 99999)}',
                    invoice_date=invoice_date,
                    due_date=invoice_date + timedelta(days=30),
                    payment_date=invoice_date + timedelta(days=random.randint(5, 25)) if random.random() > 0.3 else None,
                    status=random.choice(['pending', 'paid', 'overdue']),
                    subtotal=subtotal,
                    tax=tax,
                    total=total,
                    amount_paid=total if random.random() > 0.3 else 0,
                    balance=0 if random.random() > 0.3 else total
                )
                session.add(invoice)
                added_count += 1
        
        session.commit()
        print(f'✅ Added {added_count} invoices from last 30 days')
    finally:
        session.close()

if __name__ == '__main__':
    add_recent_invoices()
