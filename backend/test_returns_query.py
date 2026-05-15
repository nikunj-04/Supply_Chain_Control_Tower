"""Quick test of RAG chat with returns query."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.rag_chat_service import get_rag_chat_service
import logging

logging.basicConfig(level=logging.INFO)

print("Testing RAG Chat with returns query...")
print()

chat_service = get_rag_chat_service()

# Test the actual query
question = "Which customer has the most returns?"
print(f"Question: {question}")
print()

# First, check what context is retrieved
context = chat_service._build_rag_context(question, max_results=20)
print(f"Context retrieved ({len(context)} chars):")
print("=" * 70)
print(context)
print("=" * 70)
print()

# Count returns by customer from context
import re
customer_pattern = r"Customer: ([^\n]+)"
customers = re.findall(customer_pattern, context)
from collections import Counter
customer_counts = Counter(customers)

print(f"Returns by customer (from context):")
for customer, count in customer_counts.most_common(10):
    print(f"  {customer}: {count} returns")
print()

print("Now testing full chat (with LLM)...")
print()

response = chat_service.chat(question, include_context=True)
print(f"LLM Response:")
print(response)
