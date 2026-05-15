"""
Periodic sync job to keep RAG index up-to-date.
Run this every hour or on-demand to index new records.
"""

import sys
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent))

from services.rag_chat_service import get_rag_chat_service
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def sync_rag_index():
    """Rebuild RAG index with latest data."""
    try:
        logger.info("=" * 70)
        logger.info("Starting RAG Index Sync")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)
        
        start_time = time.time()
        
        # Get chat service (this will load existing index)
        chat_service = get_rag_chat_service()
        
        # Rebuild index
        logger.info("Rebuilding index...")
        chat_service.rebuild_index()
        
        elapsed = time.time() - start_time
        stats = chat_service.get_statistics()
        
        logger.info("=" * 70)
        logger.info("✅ RAG Index Sync Complete!")
        logger.info(f"   Total documents: {stats['total_documents']}")
        logger.info(f"   Time taken: {elapsed:.1f} seconds")
        logger.info(f"   Next sync: Run this script again or schedule with cron")
        logger.info("=" * 70)
        
    except Exception as e:
        logger.error(f"❌ Sync failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    sync_rag_index()
