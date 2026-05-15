# Advanced RAG Architecture for 8NAPAI

## 🎯 Your Vision: Intelligent Document + Database RAG System

### Current Limitations (Simple RAG)
- ❌ Only queries **latest 5 records** per system
- ❌ Can't answer historical questions ("What happened in December?")
- ❌ No access to documentation, SOPs, or PDFs
- ❌ Fixed context format (always same structure)
- ❌ Limited to operational data only

### Proposed Solution: Full RAG with Vector Embeddings
- ✅ **ALL database data** indexed and searchable
- ✅ **PDF documents** (invoices, reports, SOPs) included
- ✅ **Semantic search** finds most relevant context
- ✅ **Flexible context** based on question relevance
- ✅ **Historical queries** supported ("Show me November shipments")

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    USER ASKS QUESTION                        │
│           "What was our recovery rate last month?"           │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              1. EMBED USER QUESTION                          │
│    sentence-transformers/all-MiniLM-L6-v2 (local, free)     │
│                Question → [768-dim vector]                   │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│        2. SEMANTIC SEARCH IN VECTOR DATABASE                 │
│                    ChromaDB (local)                          │
│    Find top 10 most relevant chunks by cosine similarity    │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              3. RETRIEVE CONTEXT CHUNKS                      │
│  Chunk 1: "Accessorial charges Nov: $4,200..."              │
│  Chunk 2: "Billing policy section 3.2..."                   │
│  Chunk 3: "Invoice INV-202411-1234: $3,500..."              │
│  ...                                                         │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│           4. BUILD DYNAMIC CONTEXT (2000 chars)              │
│   Combine most relevant chunks + metadata                   │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│              5. SEND TO LLM (Your GPU Server)                │
│         System: Context with relevant data                   │
│         User: Original question                              │
└─────────────────────────┬───────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────┐
│                   6. LLM RESPONDS                            │
│  "Last month's recovery rate was 87% with $4,200            │
│   recovered from 38 accessorial charge opportunities..."     │
└─────────────────────────────────────────────────────────────┘
```

---

## 📊 Data Sources to Index

### 1. **Database Records** (All 7 Systems)
```python
Sources:
- OMS: Orders, OrderLines (ALL records, not just 5)
- TMS: Shipments, Routes, Carriers
- WMS: Inventory, PickingTasks, Locations
- Billing: Invoices, LineItems, Payments
- Returns: Returns, ReturnLineItems
- Yard: DockAppointments, YardLocations
- Exceptions: All exceptions (open + resolved)

Chunking Strategy:
- Each invoice → 1 chunk (with line items)
- Each shipment → 1 chunk (with route info)
- Each order → 1 chunk (with lines)
- Group by date ranges for aggregations
```

### 2. **PDF Documents**
```python
Sources:
- backend/invoices/*.pdf (Generated invoices)
- /docs/*.pdf (SOPs, policies, reports)
- Any uploaded PDFs (customer contracts, etc.)

Chunking Strategy:
- Extract text page-by-page
- Split into 500-token chunks with 50-token overlap
- Preserve document metadata (filename, page, date)
```

### 3. **Documentation & Guides**
```python
Sources:
- README.md
- INTEGRATION_GUIDE.md
- QUICKSTART.md
- All *.md files in workspace

Chunking Strategy:
- Split by sections (## headers)
- Keep code blocks intact
- Link back to source file
```

### 4. **Business Metrics** (Pre-computed)
```python
Sources:
- Monthly aggregations (total revenue, recovery rates)
- KPI summaries (on-time delivery %, exception rates)
- Carrier performance metrics
- Customer profitability stats

Chunking Strategy:
- One chunk per metric per month
- Include comparisons (month-over-month)
```

---

## 🛠️ Technology Stack

### Recommended Tools (All Free & Local)

#### 1. **Embedding Model**
```python
from sentence_transformers import SentenceTransformer

# Best choice: Fast, high-quality, runs on CPU
model = SentenceTransformer('all-MiniLM-L6-v2')

Specs:
- Speed: ~1000 sentences/sec on CPU
- Output: 384-dimensional vectors
- Size: 80MB download
- Quality: 0.68 semantic similarity score
- Cost: FREE, fully local
```

**Alternative (Better Quality)**:
```python
# Slower but more accurate
model = SentenceTransformer('all-mpnet-base-v2')
# 768-dim, 0.72 similarity score
```

#### 2. **Vector Database** (Pick One)

**Option A: ChromaDB** ⭐ **RECOMMENDED**
```python
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.create_collection(
    name="supplychain_knowledge",
    metadata={"hnsw:space": "cosine"}
)

Pros:
✅ Easiest to set up (pip install chromadb)
✅ Persistent local storage
✅ Built-in metadata filtering
✅ Good for <1M vectors
✅ Active development

Cons:
⚠️ Slower than FAISS on huge datasets
```

**Option B: FAISS (Facebook AI)**
```python
import faiss

index = faiss.IndexFlatL2(384)  # 384-dim vectors

Pros:
✅ FASTEST similarity search
✅ Battle-tested (Facebook scale)
✅ Optimized for CPU/GPU

Cons:
⚠️ No built-in metadata
⚠️ Need separate storage for text
⚠️ More complex setup
```

**Option C: Qdrant** (Production-Ready)
```python
from qdrant_client import QdrantClient

client = QdrantClient(path="./qdrant_db")

Pros:
✅ Production-grade
✅ Excellent filtering
✅ RESTful API
✅ Scales to millions

Cons:
⚠️ Heavier than ChromaDB
```

**My Recommendation**: Start with **ChromaDB**, migrate to Qdrant if you scale.

#### 3. **PDF Processing**
```python
# Option 1: PyPDF2 (simple)
from PyPDF2 import PdfReader

# Option 2: pdfplumber (better formatting)
import pdfplumber

# Option 3: pymupdf (fastest)
import fitz  # PyMuPDF
```

#### 4. **Text Chunking**
```python
# Option 1: LangChain (easiest)
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=500,
    chunk_overlap=50,
    separators=["\n\n", "\n", " ", ""]
)

# Option 2: Custom (more control)
def chunk_text(text, size=500, overlap=50):
    # Your logic
```

---

## 📋 Implementation Roadmap

### Phase 1: Foundation (Week 1)
```bash
# Install dependencies
pip install chromadb sentence-transformers pdfplumber langchain

# Create directory structure
backend/
  rag/
    __init__.py
    embeddings.py      # Embedding generation
    vector_store.py    # ChromaDB interface
    indexer.py         # Index all data sources
    retriever.py       # Semantic search
    chunker.py         # Text chunking logic
```

**Files to Create**:
1. `embeddings.py` - Initialize embedding model
2. `vector_store.py` - ChromaDB wrapper
3. `indexer.py` - Extract & index all data
4. `chunker.py` - Split text into chunks

### Phase 2: Data Indexing (Week 1)
```python
# Script: index_all_data.py
def index_databases():
    """Index all 7 database systems"""
    # Extract all orders, shipments, invoices, etc.
    # Chunk into semantic units
    # Generate embeddings
    # Store in ChromaDB with metadata
    
def index_pdfs():
    """Index all PDF documents"""
    # Find all PDFs in workspace
    # Extract text page by page
    # Chunk with overlap
    # Store with metadata (file, page)
    
def index_markdown():
    """Index documentation"""
    # Find all .md files
    # Split by headers
    # Store with source links
```

**Metadata Example**:
```python
{
    "text": "Invoice INV-20231115-1234 for $3,500...",
    "type": "invoice",
    "source": "billing_db",
    "invoice_id": "INV-20231115-1234",
    "customer": "Acme Corp",
    "date": "2023-11-15",
    "amount": 3500.00,
    "chunk_id": "inv_123_chunk_0"
}
```

### Phase 3: Retrieval Logic (Week 2)
```python
# retriever.py
class RAGRetriever:
    def __init__(self, collection):
        self.collection = collection
        self.embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    def search(self, query: str, top_k: int = 10):
        # 1. Embed user question
        query_vector = self.embedder.encode(query)
        
        # 2. Search vector DB
        results = self.collection.query(
            query_embeddings=[query_vector],
            n_results=top_k
        )
        
        # 3. Return relevant chunks
        return results['documents'], results['metadatas']
    
    def build_context(self, chunks, metadatas, max_chars=2000):
        # Smart context building
        context = "RELEVANT INFORMATION:\n\n"
        
        for chunk, meta in zip(chunks, metadatas):
            context += f"[{meta['type']}] {chunk}\n\n"
            if len(context) > max_chars:
                break
        
        return context
```

### Phase 4: Integration (Week 2)
```python
# Update chat_service.py
class SNAPaiChatService:
    def __init__(self, api_url, model_name):
        self.api_url = api_url
        self.model_name = model_name
        self.retriever = RAGRetriever()  # NEW
    
    def chat(self, user_message, include_context=True):
        if include_context:
            # OLD: Query latest 5 records
            # context = self.build_simple_context()
            
            # NEW: Semantic search
            relevant_chunks = self.retriever.search(user_message, top_k=10)
            context = self.retriever.build_context(relevant_chunks)
        
        # Send to LLM (same as before)
        return self.call_llm(context, user_message)
```

### Phase 5: Periodic Updates (Week 3)
```python
# Script: sync_vector_db.py
import schedule
import time

def sync_databases():
    """Update vectors when data changes"""
    # Check for new/modified records
    # Re-index changed data
    # Update ChromaDB
    
def sync_pdfs():
    """Watch for new PDFs"""
    # Monitor invoices/ directory
    # Index new files
    
# Run every hour
schedule.every(1).hours.do(sync_databases)
schedule.every(1).hours.do(sync_pdfs)

while True:
    schedule.run_pending()
    time.sleep(60)
```

---

## 📈 Performance Comparison

### Current Simple RAG
```
Query: "How much did we recover in November?"

Process:
1. Query latest 5 invoices → 0.5s
2. Format context (661 chars) → 0.1s
3. Send to LLM → 3.5s
Total: 4.1s

Result: ❌ "I don't have November data" 
        (only has latest 5 records)
```

### Advanced RAG with Vectors
```
Query: "How much did we recover in November?"

Process:
1. Embed query → 0.05s
2. Search 50,000 vectors → 0.3s
3. Retrieve top 10 chunks → 0.05s
4. Build context (2000 chars) → 0.1s
5. Send to LLM → 3.8s
Total: 4.3s

Result: ✅ "In November 2025, you recovered $4,235.67 
        from 38 accessorial charges. This represents
        an 87% recovery rate..." (actual data from Nov)
```

**Performance**: Similar speed, MUCH better answers!

---

## 💡 Benefits Analysis

### What You Gain:

#### 1. **Answer ANY Question**
```
Current:  "What's the average detention charge?" 
          → ❌ Can't answer (no historical data)

With RAG: "What's the average detention charge?"
          → ✅ "$125.34 based on 487 detention charges 
              over the last 6 months"
```

#### 2. **Use Documentation**
```
Current:  "What's our billing policy for detention?"
          → ❌ No policy documents indexed

With RAG: "What's our billing policy for detention?"
          → ✅ "According to policy document section 3.2,
              detention charges are billed after 2 hours
              at $75/hour..."
```

#### 3. **Historical Analysis**
```
Current:  "Compare Q3 vs Q4 revenue"
          → ❌ Only has current data

With RAG: "Compare Q3 vs Q4 revenue"
          → ✅ "Q3 revenue: $1.2M, Q4 revenue: $1.4M
              (16.7% increase). Main driver was 
              increased warehouse utilization..."
```

#### 4. **Better Context Relevance**
```
Current:  Always sends same 661-char context
          (even if irrelevant)

With RAG: Dynamically builds context based on question
          Only relevant chunks included
```

#### 5. **Scale to Millions of Records**
```
Current:  Limited to latest 5 per system (35 records)

With RAG: Index 1M+ records, still fast search
```

---

## 🚀 Estimated Effort

### Timeline: **2-3 Weeks** (Full Implementation)

| Phase | Tasks | Time | Complexity |
|-------|-------|------|------------|
| Setup | Install libs, test embeddings | 2 hours | Easy |
| Database Indexing | Extract all data, chunk, embed | 1 week | Medium |
| PDF Indexing | Parse PDFs, chunk, embed | 3 days | Easy |
| Retrieval Logic | Semantic search, context building | 3 days | Medium |
| Integration | Update chat service | 2 days | Easy |
| Testing | Test queries, tune relevance | 3 days | Medium |
| Optimization | Performance tuning | 2 days | Medium |

**Total**: 15-20 days (one developer)

---

## 💰 Cost Analysis

### Storage Requirements:
```
Embeddings:
- 100,000 records × 384 floats × 4 bytes = 154 MB
- ChromaDB overhead: ~50 MB
- PDF text storage: ~100 MB
Total: ~300 MB

Disk Space Needed: 500 MB (safe margin)
```

### Compute Requirements:
```
Indexing (One-Time):
- 100,000 records × 2ms embed time = 200 seconds = 3.3 min
- Can run as background job

Query Time:
- Embed query: 50ms
- Search vectors: 300ms
- Total overhead: 350ms (vs. 600ms for DB queries)

Faster than current approach!
```

### Costs:
- ✅ Embedding model: FREE (local)
- ✅ Vector DB: FREE (ChromaDB)
- ✅ LLM: FREE (your GPU server)
- **Total: $0/month** 🎉

---

## ⚠️ Challenges & Solutions

### Challenge 1: Initial Indexing Time
**Problem**: Embedding 100k records takes time  
**Solution**: 
- Run as one-time background job
- Show progress bar
- Can use while indexing (partial data)

### Challenge 2: Keeping Vectors Updated
**Problem**: New data needs re-indexing  
**Solution**:
- Hourly sync job for new records
- Incremental updates (only changed data)
- Webhook triggers on new invoices

### Challenge 3: Context Size Limits
**Problem**: LLM has token limits  
**Solution**:
- Limit to top 10 chunks (~2000 chars)
- Prioritize by relevance score
- Summarize less relevant chunks

### Challenge 4: Embedding Quality
**Problem**: Poor embeddings = irrelevant results  
**Solution**:
- Test different models (MiniLM vs. mpnet)
- Add metadata filters (date, type, customer)
- Hybrid search (vector + keyword)

### Challenge 5: PDF Quality
**Problem**: Scanned PDFs, bad formatting  
**Solution**:
- Use pdfplumber (better formatting)
- OCR for scanned PDFs (tesseract)
- Manual review of critical docs

---

## 🎯 Recommended Next Steps

### Step 1: **Proof of Concept (2 days)**
```bash
# Install and test basics
pip install chromadb sentence-transformers

# Create test script
python test_embeddings.py
```

Test with:
- 100 sample invoices
- 10 sample questions
- Measure relevance

### Step 2: **Index One System (3 days)**
Start with Billing (most important):
```python
# index_billing.py
- Extract all invoices
- Chunk by invoice
- Generate embeddings
- Store in ChromaDB
- Test retrieval
```

### Step 3: **Compare Results (1 day)**
```python
# Run same question with both approaches
question = "What's our total outstanding?"

# Current approach
answer_v1 = simple_rag_chat(question)

# New RAG approach
answer_v2 = vector_rag_chat(question)

# Compare accuracy, speed, relevance
```

### Step 4: **Full Rollout (2 weeks)**
If PoC successful:
- Index remaining 6 systems
- Add PDF indexing
- Integrate with chat service
- Deploy sync jobs

---

## 📊 Success Metrics

### How to Measure Improvement:

1. **Answer Coverage**
   - Current: ~20% of questions answered correctly
   - Target: 90%+ with RAG

2. **Response Time**
   - Current: 4-5 seconds
   - Target: 4-5 seconds (same)

3. **Context Relevance**
   - Manually rate 100 test questions
   - Target: 85%+ relevance score

4. **User Satisfaction**
   - Survey users before/after
   - Target: 40% → 80% satisfaction

---

## 🏁 Conclusion

### Is This Achievable?
**YES! 100% Achievable** with your current setup:
- ✅ Python backend (check)
- ✅ SQLite databases (check)
- ✅ Local LLM server (check)
- ✅ PDF documents (check)

### Is This Worth It?
**ABSOLUTELY!** Benefits:
- 🎯 Answer ANY question (not just recent data)
- 📊 Historical analysis capabilities
- 📄 Include documentation and policies
- 🚀 Scale to millions of records
- 💰 Still $0 cost (all local)
- ⚡ Same speed as current approach

### Recommended Path:
1. **Start small**: PoC with billing data only
2. **Measure**: Compare old vs. new approach
3. **Iterate**: Add more systems gradually
4. **Deploy**: Full rollout once proven

### Libraries to Install:
```bash
pip install chromadb
pip install sentence-transformers
pip install pdfplumber
pip install langchain
pip install schedule
```

**Total new dependencies**: 5 packages, all stable and well-maintained.

---

## 🎓 Learning Resources

- [ChromaDB Docs](https://docs.trychroma.com/)
- [Sentence Transformers](https://www.sbert.net/)
- [LangChain Text Splitting](https://python.langchain.com/docs/modules/data_connection/document_transformers/)
- [RAG Tutorial](https://www.pinecone.io/learn/retrieval-augmented-generation/)

---

**Bottom Line**: This is a game-changing upgrade that transforms 8NAPAI from a "recent data bot" into a true "AI knowledge assistant" for your entire supply chain operation. It's achievable, cost-effective, and will dramatically improve answer quality.

**Recommendation**: Start with a 2-day proof of concept on billing data, then decide whether to proceed with full implementation.
