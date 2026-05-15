"""
Test script to demonstrate LLM computing KPIs from raw transactional data.
This tests Option B - having LLM calculate metrics instead of pre-indexing them.
"""

import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, str(Path(__file__).parent))

from services.rag_chat_service import get_rag_chat_service
from config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def test_kpi_questions():
    """Test various KPI-related questions."""
    
    print("=" * 80)
    print("Testing KPI Calculation from Raw Data (Option B)")
    print("=" * 80)
    print()
    
    # Get RAG chat service
    print("Loading RAG chat service...")
    chat_service = get_rag_chat_service()
    print("✅ Chat service ready\n")
    
    # Test questions
    test_questions = [
        "What is the on-time delivery percentage for shipments?",
        "How many orders do we have in total?",
        "What's the pick accuracy rate in the warehouse?",
        "Calculate the return rate percentage",
        "What's the average order value?",
        "How many delayed shipments are there currently?",
    ]
    
    print("Testing KPI Questions:")
    print("-" * 80)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i}. Question: {question}")
        print("-" * 80)
        
        try:
            response = chat_service.chat(question)
            print(f"Answer: {response}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        print()
    
    print("=" * 80)
    print("Test Complete!")
    print("=" * 80)
    print()
    print("The LLM should now be able to:")
    print("  1. Detect KPI-related questions")
    print("  2. Retrieve 30 records instead of 15")
    print("  3. Calculate metrics from the raw transactional data")
    print("  4. Show calculations (e.g., '45 out of 50 orders = 90%')")
    print()


if __name__ == "__main__":
    test_kpi_questions()
