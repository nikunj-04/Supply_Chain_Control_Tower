"""
Test script to verify KPI data is being retrieved correctly.
"""
import sys
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent
sys.path.insert(0, str(backend_path))

from rag.indexer import DataIndexer
from rag.retriever import RAGRetriever

def main():
    print("=" * 70)
    print("Testing KPI Data Retrieval")
    print("=" * 70)
    print()
    
    # Initialize indexer
    print("1️⃣ Loading vector store...")
    indexer = DataIndexer()
    
    if not indexer.vector_store.load("supplychain_full"):
        print("❌ No index found! Run build_index.py first")
        return
    
    # Get stats
    total_docs = len(indexer.vector_store)
    print(f"✅ Loaded {total_docs} documents")
    print()
    
    # Create retriever
    retriever = RAGRetriever(indexer.vector_store)
    
    # Test KPI query
    print("2️⃣ Testing KPI query: 'What is on-time ship %?'")
    print("-" * 70)
    
    query = "What is on-time ship percentage rate"
    query_embedding = indexer.embedder.encode([query])[0]
    results = indexer.vector_store.search(query_embedding, k=10)
    
    print(f"\nTop 10 results for: '{query}'")
    print("=" * 70)
    
    kpi_found = False
    for i, result in enumerate(results, 1):
        doc_metadata = result['metadata']
        score = result['score']
        source = doc_metadata.get('source', 'unknown')
        doc_type = doc_metadata.get('type', 'unknown')
        content = doc_metadata.get('content', '')[:200]
        
        print(f"\n#{i} (score: {score:.4f})")
        print(f"Source: {source}")
        print(f"Type: {doc_type}")
        
        if source == 'kpi_dashboard':
            kpi_found = True
            print("🎯 KPI DASHBOARD DATA FOUND!")
            print(f"Full content:\n{doc_metadata.get('content', '')}")
        else:
            print(f"Content: {content}...")
        
        print("-" * 70)
    
    print()
    if kpi_found:
        print("✅ SUCCESS: KPI dashboard data is being retrieved!")
    else:
        print("❌ PROBLEM: KPI dashboard data NOT in top 10 results!")
        print("   This means the LLM isn't seeing the official values.")
    
    print()
    print("3️⃣ Checking for KPI documents in index...")
    print("-" * 70)
    
    # Search specifically for KPI source
    all_metadata = indexer.vector_store.metadata
    kpi_docs = [m for m in all_metadata if m.get('source') == 'kpi_dashboard']
    
    print(f"Total KPI documents indexed: {len(kpi_docs)}")
    
    if kpi_docs:
        print("\nSample KPI documents:")
        for i, doc in enumerate(kpi_docs[:5], 1):
            print(f"\n  {i}. Type: {doc.get('type')}")
            print(f"     Label: {doc.get('metric_label', 'N/A')}")
            print(f"     Value: {doc.get('metric_value', 'N/A')}")
            if 'on-time' in doc.get('metric_label', '').lower():
                print(f"     🎯 FOUND ON-TIME SHIP METRIC!")
                print(f"     Content: {doc.get('content', '')[:300]}")
    else:
        print("❌ No KPI documents found in index!")
        print("   Run: python build_index.py")
    
    print()
    print("=" * 70)
    print("Test Complete")
    print("=" * 70)


if __name__ == "__main__":
    main()
