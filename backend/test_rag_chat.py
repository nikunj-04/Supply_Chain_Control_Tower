"""
Test the RAG chat service with sample questions.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.rag_chat_service import RAGChatService
from config import settings
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    print("=" * 70)
    print("8NAPAI RAG Chat Service - Test")
    print("=" * 70)
    print()
    
    # Initialize chat service
    print("Initializing RAG Chat Service...")
    chat_service = RAGChatService(
        api_url=settings.chat_api_url,
        model_name=settings.chat_model_name
    )
    
    # Get statistics
    stats = chat_service.get_statistics()
    print(f"\nRAG Statistics:")
    print(f"  Documents: {stats['total_documents']}")
    print(f"  Model: {stats['model']}")
    print(f"  Dimension: {stats['embedding_dimension']}")
    print()
    
    # Test questions
    test_questions = [
        "What is the total outstanding balance for all invoices?",
        "Show me overdue invoices",
        "Which orders are delayed?",
        "What's our current inventory for SKU PROD-001?",
        "How many returns did we have this month?",
    ]
    
    print("=" * 70)
    print("Testing RAG Retrieval (Context Building)")
    print("=" * 70)
    print()
    
    for i, question in enumerate(test_questions, 1):
        print(f"{i}. Question: '{question}'")
        print(f"   Building context...")
        
        # Build context only (don't call LLM)
        context = chat_service._build_rag_context(question, max_results=5)
        
        print(f"   Context length: {len(context)} chars")
        print(f"   Preview:")
        print(f"   {context[:200]}...")
        print()
    
    print("=" * 70)
    print("✅ RAG Chat Service Test Complete!")
    print("=" * 70)
    print()
    print("To test with LLM:")
    print("  1. Start the backend: python main.py")
    print("  2. Use the chat interface in the frontend")
    print("  3. Or test via API: POST /api/v1/chat/message")
    print()


if __name__ == "__main__":
    main()
