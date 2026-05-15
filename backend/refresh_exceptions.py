"""Script to refresh exceptions - clear old ones and detect new ones."""
from services.exception_service import ExceptionService
from models.exception_models import Exception, SessionLocal

def refresh_exceptions():
    """Clear resolved exceptions and detect new ones."""
    session = SessionLocal()
    service = ExceptionService()
    
    try:
        # Optional: Delete old resolved exceptions (keep open/in_progress)
        # Uncomment if you want to clean up resolved exceptions
        # resolved_count = session.query(Exception).filter(
        #     Exception.status == 'resolved'
        # ).delete()
        # session.commit()
        # print(f"🧹 Cleared {resolved_count} resolved exceptions")
        
        # Detect new exceptions
        print("🔍 Scanning systems for exceptions...")
        detected = service.detect_exceptions()
        service.session.commit()
        
        print(f"✅ Exception detection complete!")
        print(f"   - {len(detected)} new exceptions detected")
        
        # Show breakdown by type
        types = {}
        for exc in detected:
            exc_type = exc.get('type', 'unknown')
            types[exc_type] = types.get(exc_type, 0) + 1
        
        print("\n📊 Breakdown by type:")
        for exc_type, count in types.items():
            print(f"   - {exc_type}: {count}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        session.rollback()
    finally:
        session.close()
        service.session.close()

if __name__ == "__main__":
    refresh_exceptions()
