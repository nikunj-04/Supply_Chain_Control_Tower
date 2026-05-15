"""Test labor queries with the RAG system."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.rag_chat_service import get_rag_chat_service
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)

print("=" * 70)
print("Testing Labor/Worker Queries")
print("=" * 70)
print()

chat_service = get_rag_chat_service()

# Test queries about workers/labor
test_queries = [
    "how many workers do I have today",
    "show me picking tasks assigned to workers",
    "which employees are working on orders",
    "list all warehouse staff assignments",
    "who is assigned to picking tasks",
]

for i, query in enumerate(test_queries, 1):
    print(f"{i}. Query: '{query}'")
    print()
    
    # Get context
    context = chat_service._build_rag_context(query, max_results=10)
    print(f"   Context length: {len(context)} chars")
    print(f"   Preview:")
    print(context[:800])
    print()
    print("-" * 70)
    print()

print("=" * 70)
print("Testing Full Chat with LLM")
print("=" * 70)
print()

# Test with LLM
query = "How many workers are assigned to picking tasks today?"
print(f"Question: {query}")
print()

response = chat_service.chat(query, include_context=True)
print("LLM Response:")
print(response)
print()
