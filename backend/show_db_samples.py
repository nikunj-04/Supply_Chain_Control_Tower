import sqlite3

def query_db(db_path, table, limit=5):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute(f'SELECT * FROM {table} LIMIT {limit}')
    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows

print('=' * 80)
print('WMS DATABASE (wms.db)')
print('=' * 80)

print('\n--- INVENTORY (5 records) ---')
inventory = query_db('data/wms.db', 'inventory', 5)
for row in inventory:
    print(f'SKU: {row["sku"]:12} | Product: {row["product_name"]:30} | Location: {row["warehouse_location"]:6} | On Hand: {row["quantity_on_hand"]:4} | Available: {row["quantity_available"]:4}')

print('\n--- PICKING TASKS (5 records) ---')
tasks = query_db('data/wms.db', 'picking_tasks', 5)
for row in tasks:
    print(f'Order: {row["order_id"]:12} | SKU: {row["sku"]:12} | Qty: {row["quantity"]:2} | Status: {row["status"]:12} | Priority: {row["priority"]:8}')

print('\n' + '=' * 80)
print('OMS DATABASE (oms.db)')
print('=' * 80)

print('\n--- ORDERS (5 records) ---')
orders = query_db('data/oms.db', 'orders', 5)
for row in orders:
    print(f'Order: {row["order_id"]:12} | Customer: {row["customer_name"]:30} | Status: {row["status"]:12} | Total: ${row["total_value"]:8.2f} | Items: {row["total_items"]}')

print('\n--- ORDER LINES (5 records) ---')
lines = query_db('data/oms.db', 'order_lines', 5)
for row in lines:
    print(f'Order: {row["order_id"]:12} | SKU: {row["sku"]:12} | Product: {row["product_name"]:35} | Qty: {row["quantity"]:2} | Total: ${row["line_total"]:8.2f}')

print('\n' + '=' * 80)
print('TMS DATABASE (tms.db)')
print('=' * 80)

print('\n--- SHIPMENTS (5 records) ---')
shipments = query_db('data/tms.db', 'shipments', 5)
for row in shipments:
    print(f'Shipment: {row["shipment_id"]:12} | Carrier: {row["carrier"]:20} | Status: {row["status"]:12} | Weight: {row["weight_lbs"]:6.1f} lbs | Cost: ${row["cost"]:7.2f}')

print('\n--- ROUTES (5 records) ---')
routes = query_db('data/tms.db', 'routes', 5)
for row in routes:
    print(f'Route: {row["route_id"]:12} | Driver: {row["driver"]:25} | Vehicle: {row["vehicle"]:10} | Status: {row["status"]:10} | Stops: {row["completed_stops"]}/{row["total_stops"]}')

print('\n' + '=' * 80)
print('BILLING DATABASE (billing.db)')
print('=' * 80)

print('\n--- INVOICES (5 records) ---')
invoices = query_db('data/billing.db', 'invoices', 5)
for row in invoices:
    print(f'Invoice: {row["invoice_id"]:12} | Customer: {row["customer_name"]:30} | Status: {row["status"]:10} | Total: ${row["total"]:9.2f} | Balance: ${row["balance"]:9.2f}')

print('\n--- BILLING LINE ITEMS (5 records) ---')
billing_lines = query_db('data/billing.db', 'billing_line_items', 5)
for row in billing_lines:
    print(f'Invoice: {row["invoice_id"]:12} | Service: {row["service_type"]:15} | Qty: {row["quantity"]:5.1f} | Unit Price: ${row["unit_price"]:7.2f} | Total: ${row["line_total"]:8.2f}')

print('\n' + '=' * 80)
print('RETURNS DATABASE (returns.db)')
print('=' * 80)

print('\n--- RETURNS (5 records) ---')
returns = query_db('data/returns.db', 'returns', 5)
for row in returns:
    print(f'Return: {row["return_id"]:12} | Customer: {row["customer_name"]:30} | Status: {row["status"]:12} | Refund: ${row["refund_amount"]:8.2f}')

print('\n--- RETURN LINE ITEMS (5 records) ---')
return_lines = query_db('data/returns.db', 'return_line_items', 5)
for row in return_lines:
    print(f'Return: {row["return_id"]:12} | SKU: {row["sku"]:12} | Qty: {row["quantity"]:2} | Condition: {row["condition"]:20} | Restock Fee: ${row["restocking_fee"]:7.2f}')

print('\n' + '=' * 80)
print('YARD DATABASE (yard.db)')
print('=' * 80)

print('\n--- DOCK APPOINTMENTS (5 records) ---')
appointments = query_db('data/yard.db', 'dock_appointments', 5)
for row in appointments:
    print(f'Appt: {row["appointment_id"]:12} | Carrier: {row["carrier"]:20} | Dock: {row["dock_door"]:8} | Type: {row["appointment_type"]:10} | Status: {row["status"]:12}')

print('\n--- YARD LOCATIONS (5 records) ---')
yard_locs = query_db('data/yard.db', 'yard_locations', 5)
for row in yard_locs:
    trailer = row["trailer_number"] if row["trailer_number"] else "N/A"
    carrier = row["carrier"] if row["carrier"] else "N/A"
    print(f'Location: {row["location_id"]:10} | Zone: {row["zone"]:5} | Status: {row["status"]:12} | Trailer: {trailer:12} | Carrier: {carrier:20}')

print('\n' + '=' * 80)
print('SUMMARY: All 6 databases queried successfully!')
print('=' * 80)
