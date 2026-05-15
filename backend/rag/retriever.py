"""
RAG Retriever - Performs semantic search and builds context for LLM.
"""

import logging
from typing import List, Dict, Any, Optional
from .embeddings import EmbeddingService
from .vector_store import VectorStore

logger = logging.getLogger(__name__)


class RAGRetriever:
    """
    Performs semantic search and builds LLM context.
    """
    
    def __init__(self, vector_store: VectorStore):
        """
        Initialize retriever.
        
        Args:
            vector_store: Initialized vector store with indexed data
        """
        self.vector_store = vector_store
        self.embedder = EmbeddingService()
        logger.info("✅ RAG retriever initialized")
    
    def retrieve(
        self,
        query: str,
        k: int = 10,
        source_filter: Optional[List[str]] = None,
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query.
        Prioritizes KPI and operational dashboard data.
        
        Args:
            query: User's question
            k: Number of results to retrieve
            source_filter: Filter by source (e.g., ['billing', 'oms'])
            min_score: Minimum similarity score (0-1)
            
        Returns:
            List of relevant documents with metadata
        """
        # Generate query embedding
        query_embedding = self.embedder.encode(query)
        
        # Search vector store (get more results initially)
        results = self.vector_store.search(query_embedding, k=k * 3)
        
        # BOOST KPI and Operational Dashboard results significantly
        boosted_results = []
        for result in results:
            source = result['metadata'].get('source', '')
            score = result['score']
            
            # Apply boost multipliers
            if source == 'kpi_dashboard':
                result['score'] = score * 3.0  # 3x boost for KPI data
                result['boosted'] = True
            elif source == 'operational_dashboard':
                result['score'] = score * 2.5  # 2.5x boost for operational data
                result['boosted'] = True
            elif source == 'exception_management':
                result['score'] = score * 2.8  # 2.8x boost for exception data
                result['boosted'] = True
            
            boosted_results.append(result)
        
        # Re-sort by boosted scores
        boosted_results.sort(key=lambda x: x['score'], reverse=True)
        
        # Filter by source if specified
        if source_filter:
            boosted_results = [r for r in boosted_results if r['metadata'].get('source') in source_filter]
        
        # Filter by minimum score
        boosted_results = [r for r in boosted_results if r['score'] >= min_score]
        
        # Return top k
        return boosted_results[:k]
    
    def build_context(
        self,
        query: str,
        k: int = 10,
        max_chars: int = 3000
    ) -> str:
        """
        Build context string for LLM.
        KPI and operational data appears first for maximum visibility.
        
        Args:
            query: User's question
            k: Number of documents to retrieve
            max_chars: Maximum context length
            
        Returns:
            Formatted context string
        """
        # Retrieve relevant documents (already boosted and sorted)
        results = self.retrieve(query, k=k)
        
        if not results:
            return "No relevant information found in the database."
        
        # Separate KPI/Operational/Exception data from other data
        priority_results = []
        other_results = []
        
        for result in results:
            source = result['metadata'].get('source', '')
            if source in ['kpi_dashboard', 'operational_dashboard', 'exception_management']:
                priority_results.append(result)
            else:
                other_results.append(result)
        
        # Build context string - KPI/Exception data FIRST
        context_parts = []
        
        if priority_results:
            context_parts.append("=" * 80)
            context_parts.append("⚠️  OFFICIAL DASHBOARD DATA (USE THESE VALUES FIRST) ⚠️")
            context_parts.append("=" * 80)
            context_parts.append("")
        
        current_length = sum(len(p) for p in context_parts)
        
        # Add priority results first
        for i, result in enumerate(priority_results, 1):
            metadata = result['metadata']
            score = result['score']
            
            part = self._format_result(metadata, score, i)
            
            if current_length + len(part) > max_chars:
                break
            
            context_parts.append(part)
            current_length += len(part)
        
        # Add separator if we have other data
        if other_results and current_length < max_chars:
            context_parts.append("")
            context_parts.append("=" * 80)
            context_parts.append("ADDITIONAL TRANSACTION DATA (for context only)")
            context_parts.append("=" * 80)
            context_parts.append("")
        
        # Add other results
        for i, result in enumerate(other_results, len(priority_results) + 1):
            metadata = result['metadata']
            score = result['score']
            
            part = self._format_result(metadata, score, i)
            
            # Check length limit
            if current_length + len(part) > max_chars:
                context_parts.append(f"\n(... {len(other_results) - (i - len(priority_results) - 1)} more results omitted due to length)")
                break
            
            context_parts.append(part)
            current_length += len(part)
        
        return "\n".join(context_parts)
    
    def _format_result(self, metadata: Dict[str, Any], score: float, index: int) -> str:
        """Format a result for context."""
        source = metadata.get('source', 'unknown')
        doc_type = metadata.get('type', 'unknown')
        
        # *** PRIORITY: Format KPI and Operational dashboard data prominently ***
        if source == 'kpi_dashboard':
            if doc_type == 'kpi_metric':
                return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 OFFICIAL KPI METRIC #{index} (Dashboard Source - Use This Value!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Category: {metadata.get('category')}
Metric: {metadata.get('metric_label')}
OFFICIAL VALUE: {metadata.get('metric_value')}
Status: {metadata.get('metric_status')}
Last Updated: {metadata.get('last_updated')}

⚠️ This is the OFFICIAL value from the dashboard - DO NOT RECALCULATE!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            elif doc_type == 'kpi_summary':
                return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 KPI DASHBOARD SUMMARY #{index} (Official Dashboard Data)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{metadata.get('content', '')}
⚠️ These are OFFICIAL values - Use them as-is!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
            else:
                return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 KPI DATA #{index} (Official Dashboard - Use These Values!)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{metadata.get('content', '')}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        elif source == 'operational_dashboard':
            return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 OPERATIONAL METRIC #{index} (Dashboard Source - Official Data)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{metadata.get('content', '')}
⚠️ Official system metric - Use this value!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Format based on source
        if source == 'billing' and doc_type == 'invoice':
            return f"""
{index}. Invoice {metadata.get('invoice_number')}
   Customer: {metadata.get('client_name')}
   Amount: ${metadata.get('amount', 0):.2f}
   Status: {metadata.get('status')}
   Date: {metadata.get('date')}
   (Relevance: {score:.2f})
"""
        
        elif source == 'oms' and doc_type == 'order':
            return f"""
{index}. Order {metadata.get('order_number')}
   Customer: {metadata.get('customer')}
   Total: ${metadata.get('total', 0):.2f}
   Status: {metadata.get('status')}
   (Relevance: {score:.2f})
"""
        
        elif source == 'tms' and doc_type == 'trip':
            return f"""
{index}. Trip {metadata.get('trip_number')}
   Carrier: {metadata.get('carrier')}
   Status: {metadata.get('status')}
   Cost: ${metadata.get('cost', 0):.2f}
   (Relevance: {score:.2f})
"""
        
        elif source == 'tms' and doc_type == 'carrier_performance':
            return f"""
{index}. Carrier Performance: {metadata.get('carrier')}
   On-Time: {metadata.get('on_time', 0):.1f}%
   Rating: {metadata.get('rating', 0):.1f}/5.0
   (Relevance: {score:.2f})
"""
        
        elif source == 'wms' and doc_type == 'inventory':
            return f"""
{index}. Inventory: {metadata.get('product')}
   SKU: {metadata.get('sku')}
   Warehouse: {metadata.get('warehouse')}
   Quantity: {metadata.get('quantity')}
   (Relevance: {score:.2f})
"""
        
        elif source == 'wms' and doc_type == 'picking_task':
            return f"""
{index}. Picking Task: {metadata.get('order_id')}
   Worker: {metadata.get('assigned_to', 'Unassigned')}
   SKU: {metadata.get('sku')}
   Status: {metadata.get('status')}
   Priority: {metadata.get('priority')}
   Created: {metadata.get('created_date', '')[:10]}
   (Relevance: {score:.2f})
"""
        
        elif source == 'returns' and doc_type == 'return_order':
            return f"""
{index}. Return {metadata.get('rma_number')}
   Customer: {metadata.get('customer')}
   Reason: {metadata.get('reason')}
   Status: {metadata.get('status')}
   Amount: ${metadata.get('amount', 0):.2f}
   (Relevance: {score:.2f})
"""
        
        elif source == 'yard':
            return f"""
{index}. Yard: {metadata.get('trailer', 'N/A')}
   Carrier: {metadata.get('carrier')}
   Status: {metadata.get('status')}
   (Relevance: {score:.2f})
"""
        
        elif source == 'pdf':
            content_preview = metadata.get('content', '')[:200]
            return f"""
{index}. Document: {metadata.get('filename')}
   {content_preview}...
   (Relevance: {score:.2f})
"""
        
        else:
            # Generic format
            content = metadata.get('content', str(metadata))[:200]
            return f"""
{index}. {source.upper()} ({doc_type})
   {content}...
   (Relevance: {score:.2f})
"""
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get retriever statistics."""
        return {
            'total_documents': len(self.vector_store),
            'embedding_dimension': self.embedder.get_dimension(),
            'model': self.embedder.model_name
        }
