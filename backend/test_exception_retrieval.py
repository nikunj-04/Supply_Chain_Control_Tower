"""Test script to debug exception document retrieval."""

from rag.indexer import DataIndexer
from rag.retriever import RAGRetriever

# Initialize
indexer = DataIndexer()
indexer.vector_store.load('supplychain_full')
retriever = RAGRetriever(indexer.vector_store)

print(f"Total documents in index: {len(indexer.vector_store)}")

# Count exception documents
exc_count = sum(1 for m in indexer.vector_store.metadata if m.get('source') == 'exception_management')
print(f"Exception documents: {exc_count}")

# Test various queries
test_queries = [
    "What are my top 3 critical exceptions?",
    "Show me critical exceptions",
    "exception summary",
    "EXC-TMS-SHIP-25984",
    "delayed shipment exceptions"
]

for query in test_queries:
    print(f"\n{'='*80}")
    print(f"Query: {query}")
    print(f"{'='*80}")
    
    results = retriever.retrieve(query, k=10)
    
    print(f"Found {len(results)} results\n")
    
    for i, result in enumerate(results[:5], 1):
        source = result['metadata'].get('source', 'unknown')
        doc_type = result['metadata'].get('type', 'unknown')
        score = result['score']
        boosted = result.get('boosted', False)
        
        print(f"{i}. Source: {source} | Type: {doc_type} | Score: {score:.4f} | Boosted: {boosted}")
        
        # Show snippet if exception
        if source == 'exception_management':
            snippet = result['metadata'].get('text', '')[:200]
            print(f"   Preview: {snippet}...")
        print()
