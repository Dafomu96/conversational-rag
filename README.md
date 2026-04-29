# DocRAG — Conversational RAG over Structured Documents

A production-grade conversational AI system that answers questions about PDF documents using advanced retrieval techniques, table extraction, and hallucination detection.

![Python](https://img.shields.io/badge/Python-3.11-blue)
![LangGraph](https://img.shields.io/badge/LangGraph-1.1-green)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-teal)
![React](https://img.shields.io/badge/React-19-61DAFB)
![Docker](https://img.shields.io/badge/Docker-compose-2496ED)

## Demo

> Upload a PDF → ask questions → get answers with cited sources, page references, and grounding scores.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                     React Frontend                       │
│  Drag & drop upload · Chat UI · PDF viewer · Table render│
└──────────────────────┬──────────────────────────────────┘
                       │ HTTP
┌──────────────────────▼──────────────────────────────────┐
│                   FastAPI Backend                        │
│                                                          │
│  ┌─────────────────────────────────────────────────┐    │
│  │              LangGraph Pipeline                  │    │
│  │                                                  │    │
│  │  expand_queries → retrieve → generate → check   │    │
│  │                                                  │    │
│  │  • Query expansion (2-3 variants per question)  │    │
│  │  • Hybrid retrieval (BM25 + ChromaDB semantic)  │    │
│  │  • Cross-encoder reranking                      │    │
│  │  • Hallucination grounding check                │    │
│  └─────────────────────────────────────────────────┘    │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │  pdfplumber  │  │   ChromaDB   │  │  Groq LLM    │  │
│  │  extraction  │  │  + BM25      │  │  Llama 3.3   │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## Key Technical Features

### RAG Pipeline
- **Hybrid retrieval**: BM25 keyword search + ChromaDB semantic search fused via Reciprocal Rank Fusion (RRF)
- **Cross-encoder reranking**: `ms-marco-MiniLM-L-6-v2` reranks candidates after initial retrieval for precision
- **Query expansion**: LLM generates 2 alternative phrasings per question to improve recall
- **Intelligent chunking**: text split with `RecursiveCharacterTextSplitter` (800 tokens, 100 overlap); tables kept as complete chunks to preserve structure
- **Rich metadata**: every chunk carries page number, type (text/table), and detected section for precise citation

### Table Extraction
- `pdfplumber` extracts structured tables separately from prose
- Tables converted to Markdown and stored as atomic chunks (never split)
- Frontend renders table responses as interactive HTML tables

### Memory & Conversation
- Session-based conversational memory via LangGraph state
- Last 3 conversation turns injected into each generation prompt
- Independent sessions per user via UUID

### Hallucination Detection
- Dedicated LangGraph node evaluates every response against retrieved context
- Returns grounding score (0–1) displayed in the UI

## Stack

| Layer | Technology |
|---|---|
| LLM | Groq — Llama 3.3 70B |
| Orchestration | LangGraph |
| Vector store | ChromaDB + sentence-transformers |
| Keyword search | BM25 (rank-bm25) |
| Reranking | CrossEncoder (ms-marco-MiniLM-L-6-v2) |
| PDF extraction | pdfplumber |
| API | FastAPI + uvicorn |
| Frontend | React 19 + Tailwind CSS v4 |
| Deploy | Docker + docker-compose |

## Project Structure

```
conversational-rag/
├── backend/
│   ├── app/
│   │   ├── extraction/     # pdfplumber text + table extraction
│   │   ├── rag/            # chunker, hybrid retriever, reranker
│   │   ├── graph/          # LangGraph nodes, edges, state
│   │   ├── api/            # FastAPI routes
│   │   └── evaluation/     # RAGAS evaluation pipeline
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # UploadZone, ChatPanel, Message, PDFViewer
│   │   └── App.jsx
│   ├── Dockerfile
│   └── nginx.conf
└── docker-compose.yml
```

## Quick Start

### Local Development

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt

# Add your Groq API key
echo "GROQ_API_KEY=your_key" > .env

uvicorn app.api.routes:app --host 0.0.0.0 --port 8000 --reload

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Docker

```bash
# Add GROQ_API_KEY to .env in project root
echo "GROQ_API_KEY=your_key" > .env

docker-compose up --build
# Frontend: http://localhost:5173
# Backend:  http://localhost:8000
```

## Evaluation

RAGAS evaluation across 20 test questions covering plain text, table data, and multi-turn conversational chains.

### Running the evaluation

```bash
cd backend
python -m app.evaluation.evaluator YOUR_DOC_ID
```

Generates:
- `evaluation_results/eval_TIMESTAMP.csv` — per-question scores
- `evaluation_results/eval_TIMESTAMP.png` — score visualization

### Metrics (on 2503.16870v2.pdf — Sparse Logit Sampling paper)

| Metric | Text Q&A | Table Q&A | Conversational |
|---|---|---|---|
| Faithfulness | — | — | — |
| Answer Relevancy | — | — | — |
| Context Precision | — | — | — |
| Context Recall | — | — | — |
| Grounding Score | — | — | — |

> Metrics will be populated after running the evaluation script.

## Design Decisions

**Why LangGraph over a simple chain?**
LangGraph allows conditional routing between nodes — the hallucination check node could trigger a retry loop if grounding score falls below threshold, which is not possible with linear chains.

**Why hybrid BM25 + semantic retrieval?**
Semantic search alone fails on exact numerical queries (e.g. "what is the value in row 3"). BM25 handles keyword matching; semantic handles conceptual queries. RRF fusion captures both.

**Why cross-encoder reranking?**
Bi-encoder embeddings (used in ChromaDB) trade accuracy for speed. Cross-encoders compare query+document jointly, giving significantly better relevance scoring at the cost of latency — acceptable for a RAG pipeline where retrieval quality matters most.

**Why pdfplumber over PyMuPDF?**
pdfplumber provides structured table extraction with cell-level coordinates, which PyMuPDF does not support natively. The tradeoff is slightly slower extraction.