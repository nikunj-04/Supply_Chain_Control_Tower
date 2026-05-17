# Future Scope — RAG-Powered Conversational Assistant

## Project: E-commerce Fulfillment Operations Control Tower

---

## Overview

This document describes the planned future enhancement to the E-commerce Fulfillment Operations Control Tower: a Retrieval-Augmented Generation (RAG) chatbot that will allow users to query operational data in natural language. This feature has been designed and partially implemented, but is currently disabled in the production build. This document explains the current status, what exists in the codebase, what the feature will do when enabled, and the steps required to activate it.

---

## Current Status — Feature Disabled

The RAG chat system is fully designed but currently disabled at the application level. The disablement was intentional to allow the core platform to be demonstrated without requiring the heavyweight machine learning dependencies.

**Evidence in `backend/main.py` (lines 38-40):**

```python
# TEMPORARILY DISABLED - RAG chat service requires additional dependencies
# from services.rag_chat_service import get_rag_chat_service
```

**Evidence in `frontend/src/App.jsx`:**

```javascript
// import Chat from './components/Chat'
```

All chat API endpoints are commented out in `main.py`. The frontend Chat component exists but is not imported or rendered.

---

## What Exists in the Codebase Today

The following files are part of the RAG system. They exist in the repository but are inactive:

| File | Location | Purpose |
|------|----------|---------|
| `rag/__init__.py` | `backend/rag/` | RAG module package initializer |
| `rag/embeddings.py` | `backend/rag/` | Text-to-vector embedding logic using sentence-transformers |
| `rag/indexer.py` | `backend/rag/` | Reads database records and builds documents for indexing |
| `rag/kpi_indexer.py` | `backend/rag/` | Specialized indexer for KPI metric documents |
| `rag/retriever.py` | `backend/rag/` | Semantic search engine — finds relevant documents for a query |
| `rag/vector_store.py` | `backend/rag/` | FAISS-based vector index storage and lookup |
| `build_index.py` | `backend/` | Standalone script to build the full vector index from scratch |
| `sync_rag_index.py` | `backend/` | Incremental index updater — adds new records to existing index |
| `refresh_kpi_index.py` | `backend/` | Re-indexes KPI data after a data refresh |
| `data/vector_index/` | `backend/data/` | Directory where the built index files are stored |
| `requirements-rag.txt` | `backend/` | Python dependencies for the RAG system |
| `Chat.jsx` | `frontend/src/components/` | React chat UI component |
| `test_rag_chat.py` | `backend/` | Integration tests for the RAG pipeline |
| `test_rag_poc.py` | `backend/` | Proof-of-concept RAG tests |

---

## What the RAG System Does

The RAG system enables users to ask questions about their supply chain operations in natural language and receive context-aware answers. Instead of navigating dashboard sections, the user can simply type a question and get a direct answer.

### Example Questions the System Will Handle

- "What are our on-time delivery rates for last month?"
- "Show me all critical exceptions in the warehouse"
- "Which shipments are currently delayed?"
- "What is the average dock detention time this week?"
- "List overdue invoices above $5,000"
- "How is carrier FedEx performing on our routes?"

### How It Differs From the Current System

| Capability | Current System | RAG System (Future) |
|------------|---------------|---------------------|
| Data access | Fixed dashboard panels | Natural language query |
| Interaction | Click-based navigation | Conversational chat |
| Context | Fixed per component | Dynamic, cross-system context |
| Output | Charts and tables | Prose answers with supporting data |
| Data source | Direct SQL queries | Vector similarity search |

---

## Technical Architecture of the RAG System

The RAG pipeline has three phases: indexing, retrieval, and generation.

### Phase 1 — Indexing (Offline / Batch)

The indexer reads all records from all six databases and converts them into text documents. Each document represents one record (one order, one shipment, one exception, etc.) and contains the key fields in readable text form.

The document collection is then converted into vector embeddings using a sentence-transformer model. Each document is mapped to a high-dimensional numeric vector that captures its semantic meaning. The vectors are stored in a FAISS vector index on disk at `backend/data/vector_index/`.

```
Data Sources  ──►  Indexer  ──►  Text Documents  ──►  Embeddings Model  ──►  FAISS Vector Index
  (6 DBs)                          (~903+ docs)        (sentence-transformers)  (disk storage)
```

### Phase 2 — Retrieval (Per Query)

When a user sends a chat message, the retriever:
1. Converts the user's question into a vector embedding using the same model
2. Performs a similarity search against the FAISS index
3. Retrieves the top-K most relevant documents (default: top 5 to 10)
4. Returns the document texts to the generation layer

The retrieval is purely semantic — the system does not need exact keyword matches. A question about "overdue payments" will find documents containing "unpaid invoices" or "pending billing" because they are semantically similar.

### Phase 3 — Generation (Per Query)

The retrieved document texts are assembled into a context block and passed to a large language model (LLM) along with the user's question. The LLM generates a natural language answer grounded in the retrieved data.

```
User Question
      │
      ▼
Embedding Model  ──►  Query Vector
      │
      ▼
FAISS Index  ──►  Top-K Relevant Documents
      │
      ▼
Context Assembly  ──►  [System Prompt + Retrieved Docs + User Question]
      │
      ▼
LLM (External API or Local)  ──►  Natural Language Answer
      │
      ▼
Chat Response sent to Frontend
```

---

## Index Size and Document Categories

When fully built, the vector index contains documents from all six enterprise systems:

| Document Category | Source System | Estimated Document Count |
|-------------------|--------------|--------------------------|
| Order records | OMS | ~200 documents |
| Shipment tracking records | TMS | ~150 documents |
| Inventory items | WMS | ~200 documents |
| Picking task records | WMS | ~100 documents |
| Invoice and billing records | Billing | ~100 documents |
| Return order records | Returns | ~80 documents |
| Dock appointment records | Yard | ~80 documents |
| Computed KPI summaries | All systems | ~20 documents |
| **Total** | | **~930 documents** |

KPI summaries are generated by `kpi_indexer.py` and represent aggregated statistics rather than individual records. These allow the system to answer high-level questions ("What is our on-time delivery rate?") without scanning hundreds of individual shipment documents.

---

## LLM Integration Options

The generation layer is designed to support multiple LLM backends. The code structure accommodates:

| Option | Description | Trade-offs |
|--------|-------------|-----------|
| **OpenAI API** | Cloud-based GPT models via REST API | Requires API key and internet; high quality responses |
| **Local Model (Ollama)** | Open-source models running on local hardware | No API key needed; works offline; lower resource requirements |
| **Azure OpenAI** | Enterprise Azure-hosted GPT models | Suitable for corporate data security requirements |
| **Fallback Mode** | Returns raw retrieved documents without LLM generation | No external dependency; lower quality but always available |

The system was designed with a fallback: if no LLM is configured or available, it returns the top retrieved document texts directly without generating a prose answer.

---

## Steps to Enable the RAG System

When ready to activate this feature, the following steps are required:

### Step 1 — Install RAG Dependencies

```
cd backend
pip install -r requirements-rag.txt
```

Key packages added:
- `sentence-transformers` — For text embedding generation
- `faiss-cpu` — For vector similarity search (or `faiss-gpu` for GPU acceleration)
- `torch` — PyTorch, required by sentence-transformers
- LLM client library (openai, or a local model adapter)

> Note: These dependencies are large (several hundred MB) and may require a GPU for optimal performance. This is why they are separated into `requirements-rag.txt`.

### Step 2 — Build the Vector Index

```
cd backend
python build_index.py
```

This script reads all records from all six databases and builds the FAISS vector index. Expected runtime: 2 to 10 minutes depending on data volume and hardware.

Output: Files saved to `backend/data/vector_index/`

### Step 3 — Configure the LLM

Set the LLM API key and endpoint in the `.env` file:

```
LLM_PROVIDER=openai              # or: ollama, azure
OPENAI_API_KEY=sk-...            # if using OpenAI
LLM_MODEL=gpt-4o-mini            # model name
```

### Step 4 — Uncomment the RAG Service in `main.py`

Remove the comment markers from lines 38-40:

```python
from services.rag_chat_service import get_rag_chat_service
```

Also uncomment the chat endpoint routes further down in `main.py`.

### Step 5 — Re-enable the Chat Component in the Frontend

In `frontend/src/App.jsx`, uncomment:

```javascript
import Chat from './components/Chat'
```

And add the `<Chat />` component to the JSX render output.

### Step 6 — Restart Services

```
cd backend && python main.py
cd frontend && npm run dev
```

A chat icon will appear in the dashboard. Users can click it to open the conversational assistant.

---

## Index Freshness and Update Strategy

The vector index must be kept in sync with the live databases. Three scripts handle this:

| Script | Trigger | Action |
|--------|---------|--------|
| `build_index.py` | One-time setup or full reset | Rebuilds entire index from scratch |
| `sync_rag_index.py` | After bulk data changes | Adds newly created records to existing index |
| `refresh_kpi_index.py` | After `populate_live_data.py` runs | Re-indexes KPI summary documents |

In a production environment, `sync_rag_index.py` would be called automatically after each data refresh cycle (every 5 minutes by the scheduler), so the chatbot always answers based on current data.

---

## Future Scope — Planned Enhancements Beyond Initial RAG

Beyond the base RAG chatbot, the following enhancements are planned for future development iterations:

### Multi-Turn Conversation Context

The current RAG design supports single-turn questions. A future enhancement will add conversation history so users can ask follow-up questions:
- "Which carriers are most delayed this week?"
- "What about their performance last month?" ← (follow-up referencing previous answer)

### Proactive Alerts via Chat

The assistant will proactively push alerts to the chat interface when critical exceptions are detected, rather than requiring the user to navigate to the Exception Center.

### Natural Language Report Generation

Users will be able to say "Generate a weekly performance summary" and receive a formatted report combining data from all six systems.

### Role-Aware Response Filtering

The chat assistant will apply the same RBAC rules as the dashboard. A `customer_user` asking about shipments will only see their own orders. A `warehouse_manager` asking about billing will receive a permission-denied response.

### Voice Input Integration

A planned enhancement adds browser-based speech recognition so users can speak their questions instead of typing them.
