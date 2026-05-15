"""
Scheduler for Live Data Population
Runs data population at configurable intervals for demo purposes
"""

import sys
import time
from pathlib import Path
from datetime import datetime
import schedule

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.populate_live_data import LiveDataPopulator

def run_population():
    """Run the data population"""
    print(f"\n⏰ Scheduled run triggered at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    try:
        populator = LiveDataPopulator()
        populator.populate_all()
    except Exception as e:
        print(f"❌ Scheduled run failed: {e}")

def main():
    """Main scheduler"""
    print("=" * 80)
    print("🔄 Live Data Population Scheduler Started")
    print("=" * 80)
    print("\nConfiguration:")
    print("  - Runs every 5 minutes")
    print("  - Press Ctrl+C to stop")
    print("\n" + "=" * 80)
    
    # Schedule the job every 5 minutes
    schedule.every(5).minutes.do(run_population)
    
    # Run once immediately
    print("\n🚀 Running initial population...")
    run_population()
    
    print("\n⏳ Scheduler is now running. Waiting for next scheduled time...")
    
    # Keep running
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n🛑 Scheduler stopped by user")
        print("=" * 80)

if __name__ == "__main__":
    main()
