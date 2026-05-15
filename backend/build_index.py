"""
Build the RAG index for the first time.
This script indexes all data sources into the vector store.
"""

import sys
import time
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from rag.indexer import DataIndexer
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    print("=" * 70)
    print("8NAPAI Advanced RAG - Initial Index Build")
    print("=" * 70)
    print()
    
    start_time = time.time()
    
    try:
        # Create indexer
        print("1️⃣ Initializing indexer...")
        indexer = DataIndexer()
        
        # Index all data (don't load existing)
        print("\n2️⃣ Starting full data indexing...")
        print("   This will index all 7 databases + PDFs")
        print("   Estimated time: 2-5 minutes")
        print()
        
        indexer.index_all(load_existing=False)
        
        # Show statistics
        vector_store = indexer.get_vector_store()
        elapsed = time.time() - start_time
        
        print()
        print("=" * 70)
        print("✅ INDEX BUILD COMPLETE!")
        print("=" * 70)
        print(f"Total documents indexed: {len(vector_store)}")
        print(f"Time taken: {elapsed:.1f} seconds")
        print(f"Index saved to: data/vector_index/")
        print()
        print("Next: Integrate with chat service")
        print("=" * 70)
        
    except Exception as e:
        logger.error(f"Index build failed: {e}", exc_info=True)
        print()
        print("❌ Index build failed. Check logs for details.")
        sys.exit(1)


if __name__ == "__main__":
    main()
