"""RAG-powered chat service that uses the full RAG system."""
import requests
import time
from typing import Optional, Dict, Any
from rag.indexer import DataIndexer
from rag.retriever import RAGRetriever
from config import settings
from logger import setup_logger

logger = setup_logger(__name__)


class RAGChatService:
    """
    Chat service using advanced RAG with semantic search.
    Replaces the simple 5-record context with full historical search.
    """
    
    def __init__(self, api_url: str, model_name: str = ""):
        """
        Initialize RAG-powered chat service.
        
        Args:
            api_url: LLM API endpoint
            model_name: Model name (can be empty)
        """
        self.api_url = api_url
        self.model_name = model_name
        
        logger.info("Initializing RAG Chat Service...")
        logger.info(f"  API URL: {self.api_url}")
        
        # Initialize RAG components
        logger.info("Loading RAG system...")
        self.indexer = DataIndexer()
        
        # Load existing index (or build if not exists)
        if not self.indexer.vector_store.load("supplychain_full"):
            logger.warning("No index found, building from scratch...")
            self.indexer.index_all(load_existing=False)
        
        # Create retriever
        self.retriever = RAGRetriever(self.indexer.vector_store)
        
        # Get stats
        stats = self.retriever.get_statistics()
        logger.info(f"✅ RAG Chat Service ready!")
        logger.info(f"  Documents indexed: {stats['total_documents']}")
        logger.info(f"  Embedding model: {stats['model']}")
        logger.info(f"  Dimension: {stats['embedding_dimension']}")
    
    def chat(self, user_message: str, include_context: bool = True) -> str:
        """
        Chat with LLM using RAG-powered context.
        
        Args:
            user_message: User's question
            include_context: Whether to include retrieved context
            
        Returns:
            AI response
        """
        try:
            start_time = time.time()
            
            # Detect if this is a KPI/metrics question
            is_kpi_query = self._is_kpi_query(user_message)
            
            # Build context using RAG
            context = ""
            if include_context:
                # For KPI queries, retrieve more data
                context = self._build_rag_context(
                    user_message,
                    max_results=30 if is_kpi_query else 15,
                    max_chars=6000 if is_kpi_query else 4000
                )
                retrieval_time = time.time() - start_time
                logger.info(f"Context retrieved in {retrieval_time*1000:.0f}ms (KPI query: {is_kpi_query})")
            
            # Build prompt
            system_prompt = """You are 8NAP AI, an AI assistant for 3PL supply chain operations.

**CRITICAL INSTRUCTION - READ FIRST:**
When the context below contains data marked as "KPI Metric:", "KPI Category:", "KPI Dashboard Summary", "Operational Metric:", or "System:" - these are OFFICIAL PRE-CALCULATED VALUES from live dashboards.

YOU MUST:
1. Use these exact official values when they are present
2. Never recalculate or estimate when official values are provided
3. Cite them as "According to the dashboard..." or "The current metric shows..."

DO NOT:
1. Try to calculate from raw transaction data when official metrics are available
2. Say "insufficient data" if official dashboard metrics are in the context
3. Estimate or approximate when you have exact dashboard values

Your role is to help users with:
- KPI metrics and performance analytics
- System health and operational status
- Order and shipment tracking
- Inventory management
- Billing and invoicing questions
- Warehouse operations
- Returns processing
- Exception management and issue tracking

**EXCEPTION DATA PRIORITY:**
When context includes "=== EXCEPTION DETAIL ===" or "EXCEPTION MANAGEMENT CENTER SUMMARY", this is official exception data from the Exception Management Dashboard. Use this data to answer questions about:
- Critical/warning exceptions
- Specific exception details (IDs, descriptions, impacts)
- Exception counts by type, severity, or system
- Delayed shipments, inventory issues, processing delays
These exception records contain the most accurate and detailed information about system issues.

Answer based ONLY on the provided context. Be concise, accurate, and professional.

**When you see official dashboard data, USE IT DIRECTLY - don't try to recalculate!**
- On-Time In Full %: Similar to on-time ship % but also considering complete quantity
- Backlog aging: Average days between order date and current date for non-delivered orders

**Fulfillment KPIs:**
- Pick accuracy %: (completed picking tasks) / (total picking tasks)
- Lines per hour: Total picking tasks / total hours worked
- Order cycle time: Average time from order creation to shipment

**Inventory KPIs:**
- Days of inventory: (current quantity_on_hand) / (average daily usage)
- Inventory turnover: Total orders shipped / average inventory level
- Stock accuracy %: Items with correct quantities / total items

**Transportation KPIs:**
- On-time delivery %: (shipments delivered on time) / total shipments
- Cost per mile: Total shipping cost / total distance
- Carrier performance: Group by carrier and calculate on-time %

**Returns KPIs:**
- Return rate %: (total returns) / (total orders) * 100
- Return processing time: Average days from return creation to completion

**Dock/Yard KPIs:**
- Dock utilization %: (scheduled appointments) / (total dock capacity * hours)
- Average dwell time: Average time between check-in and check-out

When computing metrics:
1. Count the relevant records from the provided data
2. Apply the formula above
3. Show your calculation (e.g., "Based on 45 out of 50 orders delivered on time = 90%")
4. If insufficient data, estimate based on available samples and state this clearly"""
            
            if context:
                system_prompt += f"\n\nRELEVANT DATA:\n{context}"
            
            # Call LLM
            llm_start = time.time()
            response = self._call_llm(system_prompt, user_message)
            llm_time = time.time() - llm_start
            
            total_time = time.time() - start_time
            logger.info(f"Total response time: {total_time:.2f}s (retrieval: {retrieval_time*1000:.0f}ms, LLM: {llm_time:.2f}s)")
            
            return response
        
        except Exception as e:
            logger.error(f"Chat error: {e}", exc_info=True)
            return f"Sorry, I encountered an error processing your request: {str(e)}"
    
    def _is_kpi_query(self, query: str) -> bool:
        """
        Detect if query is asking about KPIs/metrics.
        
        Args:
            query: User's question
            
        Returns:
            True if KPI-related query
        """
        kpi_keywords = [
            'kpi', 'metric', 'performance', 'percentage', '%',
            'on-time', 'accuracy', 'rate', 'efficiency', 'utilization',
            'average', 'total orders', 'total shipments', 'how many',
            'dashboard', 'analytics', 'trends', 'statistics'
        ]
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in kpi_keywords)
    
    def _build_rag_context(self, query: str, max_results: int = 15, max_chars: int = 4000) -> str:
        """
        Build context using RAG retrieval.
        
        Args:
            query: User's question
            max_results: Maximum number of documents to retrieve
            max_chars: Maximum context character length
            
        Returns:
            Formatted context string
        """
        # Retrieve relevant documents
        context = self.retriever.build_context(
            query=query,
            k=max_results,
            max_chars=max_chars
        )
        
        return context
    
    def _call_llm(self, system_prompt: str, user_message: str) -> str:
        """
        Call the LLM API.
        
        Args:
            system_prompt: System prompt with context
            user_message: User's question
            
        Returns:
            LLM response text
        """
        try:
            payload = {
                "model": self.model_name,
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": user_message
                    }
                ],
                "temperature": 0.7,
                "max_tokens": 800  # Increased for detailed KPI calculations
            }
            
            logger.debug(f"Calling LLM API: {self.api_url}")
            response = requests.post(
                self.api_url,
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"]
            else:
                logger.error(f"LLM API error: {response.status_code} - {response.text}")
                return f"Error: LLM API returned status {response.status_code}"
        
        except requests.exceptions.Timeout:
            logger.error("LLM API timeout")
            return "Error: Request timed out. Please try again."
        except requests.exceptions.ConnectionError as e:
            logger.error(f"LLM API connection error: {e}")
            return "Error: Could not connect to LLM service."
        except Exception as e:
            logger.error(f"LLM API call failed: {e}", exc_info=True)
            return f"Error calling LLM: {str(e)}"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get RAG system statistics."""
        return {
            **self.retriever.get_statistics(),
            'api_url': self.api_url,
            'model': self.model_name or 'default'
        }
    
    def rebuild_index(self):
        """Rebuild the entire index (for updates)."""
        logger.info("Rebuilding RAG index...")
        self.indexer.index_all(load_existing=False)
        logger.info("✅ Index rebuilt successfully")


# Global instance (singleton)
_rag_chat_service: Optional[RAGChatService] = None


def get_rag_chat_service() -> RAGChatService:
    """Get or create RAG chat service instance."""
    global _rag_chat_service
    if _rag_chat_service is None:
        _rag_chat_service = RAGChatService(
            api_url=settings.chat_api_url,
            model_name=settings.chat_model_name
        )
    return _rag_chat_service
