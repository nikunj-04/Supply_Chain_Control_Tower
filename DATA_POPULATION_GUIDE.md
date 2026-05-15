# Live Data Population Scripts

These scripts simulate live business operations by continuously generating and updating data across all systems. Perfect for demos and testing!

## 📋 What Gets Generated

The scripts create realistic, incremental data changes including:

### Orders & Fulfillment
- ✅ New customer orders (3-7 per run)
- ✅ Order status progressions (pending → processing → shipped)
- ✅ New picking tasks
- ✅ Completed picking tasks

### Transportation
- ✅ New shipments (3-7 per run)
- ✅ Shipment status updates (scheduled → in_transit → delivered)
- ✅ Route progressions

### Warehouse
- ✅ Inventory level changes (realistic consumption)
- ✅ Low inventory alerts
- ✅ Out-of-stock notifications
- ✅ New dock appointments

### Billing & Finance
- ✅ New invoices (2-5 per run)
- ✅ Invoice payments processing
- ✅ Payment status updates

### Returns
- ✅ New return requests (1-3 per run)
- ✅ Return status progressions

### Exceptions
- ✅ Critical alerts (low inventory, delays, etc.)
- ✅ Exception creation across all systems

## 🚀 Usage

### Option 1: One-Time Population (Quick Demo Setup)

Run the data population once:

```bash
# Windows
populate-data.bat

# Manual (from backend directory with venv activated)
python scripts/populate_live_data.py
```

**Use case:** Quick refresh before a demo or meeting

### Option 2: Scheduled Continuous Population (Live Demo)

Run data population every 5 minutes automatically:

```bash
# Windows
run-data-scheduler.bat

# Manual (from backend directory with venv activated)
python scripts/run_live_data_scheduler.py
```

**Use case:** During live demos, long presentations, or testing sessions

Press `Ctrl+C` to stop the scheduler.

## 📊 Demo Workflow

### Before a Demo:
1. Run `populate-data.bat` to seed initial activity
2. Start backend and frontend servers
3. Open dashboards to show current state

### During a Live Demo:
1. Start `run-data-scheduler.bat` in a separate terminal
2. Navigate through dashboards
3. Point out real-time changes as they occur
4. Show new orders, shipments, and alerts appearing

### What Viewers Will See:
- New orders appearing in Order Management
- Shipments progressing on the tracking map
- Inventory levels changing
- Real-time exceptions being created
- Statistics updating across dashboards
- Fresh data every 5 minutes

## ⚙️ Customization

### Change Update Frequency

Edit `run_live_data_scheduler.py`:

```python
# Every 5 minutes (default)
schedule.every(5).minutes.do(run_population)

# Every 2 minutes (more frequent)
schedule.every(2).minutes.do(run_population)

# Every 10 minutes (less frequent)
schedule.every(10).minutes.do(run_population)

# Every 30 seconds (very frequent - for intense demos)
schedule.every(30).seconds.do(run_population)
```

### Adjust Data Volume

Edit `populate_live_data.py` and modify the `count` parameters:

```python
# More orders per run
self.populate_new_orders(count=10)  # Instead of 5

# More shipments
count = random.randint(5, 12)  # Instead of 3, 7

# More exceptions
count = random.randint(2, 8)  # Instead of 1, 4
```

## 🎯 Best Practices for Demos

1. **Pre-load data**: Run seed_data.py before the demo for baseline data
2. **Start scheduler early**: Start 10-15 minutes before demo begins
3. **Monitor terminal**: Keep scheduler terminal visible to show activity
4. **Refresh dashboards**: Have auto-refresh enabled on dashboards
5. **Point out changes**: Call attention to new data as it appears
6. **Stop cleanly**: Use Ctrl+C to stop scheduler gracefully

## 📝 Installation

The `schedule` library is required:

```bash
cd backend
pip install schedule
# Or
pip install -r requirements.txt
```

## 🔍 Troubleshooting

### Script fails to run
- Ensure virtual environment is activated
- Check that all databases exist (run `seed_data.py` first)
- Verify `config.py` has correct database paths

### No visible changes in dashboards
- Ensure backend server is running
- Check dashboard auto-refresh is enabled
- Verify time since last population (should be < 5 min)
- Check terminal for error messages

### Too much/too little data
- Adjust the `count` parameters in the script
- Change the scheduler frequency
- Run one-time population for controlled amounts

## 📈 Impact on Database

Each scheduled run adds approximately:
- 3-7 new orders
- 3-7 new shipments  
- 5-10 new picking tasks
- 2-5 new invoices
- 1-3 new returns
- 2-5 new dock appointments
- 1-4 new exceptions

**Database growth:** ~50-100 records per 5-minute cycle

## 🎬 Demo Script Example

```
1. [Before Demo]
   - Run populate-data.bat
   - Start servers
   
2. [Demo Start]
   - Show KPI Dashboard: "These are live metrics..."
   - Start run-data-scheduler.bat
   
3. [5 Minutes Later]
   - "Notice the order count increased..."
   - "New shipments appeared on the map..."
   - "Real-time exception just appeared..."
   
4. [End of Demo]
   - Stop scheduler with Ctrl+C
```

## 🚦 Performance Notes

- Each population run takes 2-5 seconds
- No impact on running servers
- Safe to run while users are viewing dashboards
- Database locks are minimal and brief

## 💡 Tips

- Use **one-time** for quick demos (< 10 minutes)
- Use **scheduler** for longer demos (30+ minutes)
- Combine with manual data refresh API calls
- Monitor the scheduler terminal for errors
- Keep baseline data fresh (re-seed weekly)

Happy demoing! 🎉
