"""
Refresh KPI Data in Vector Index

This script refreshes only the KPI metrics in the vector index
without rebuilding the entire index. This is much faster than
a full rebuild and ensures chatbot responses stay aligned with
current dashboard data.

Run this script:
1. After data changes that affect KPIs
2. On a schedule (e.g., every hour or daily)
3. Before important demos to ensure fresh data
"""

import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from rag.indexer import DataIndexer
from logger import setup_logger

logger = setup_logger(__name__)


def main():
    """Refresh KPI metrics in the vector index."""
    print("=" * 60)
    print("   KPI Data Refresh for RAG System")
    print("=" * 60)
    print()
    
    print("🔄 Initializing indexer...")
    indexer = DataIndexer()
    
    print("📊 Refreshing KPI metrics from dashboard service...")
    print("   This will update KPI data to match current dashboards")
    print()
    
    try:
        indexer.refresh_kpi_data()
        
        print()
        print("=" * 60)
        print("✅ KPI Data Refresh Complete!")
        print("=" * 60)
        print()
        print("The chatbot will now return KPI values that match")
        print("the current dashboard displays exactly.")
        print()
        
        # Get stats
        stats = indexer.vector_store.get_stats()
        print(f"📈 Total documents in index: {stats.get('total_documents', 'unknown')}")
        print()
        
        return 0
        
    except Exception as e:
        print()
        print("❌ Error refreshing KPI data:")
        print(f"   {str(e)}")
        print()
        logger.error(f"KPI refresh failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
