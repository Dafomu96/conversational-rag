from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import tempfile
import os
import uuid

from app.extraction.pdf_extractor import extract_document
from app.rag.chunker import chunk_document
from app.graph.nodes import get_retriever, retriever_store
from app.graph.graph import rag_graph
from langchain_core.messages import HumanMessage

app = FastAPI(title="Conversational RAG API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Sesiones en memoria (para producción: Redis)
sessions: dict = {}


class ChatRequest(BaseModel):
    query: str
    session_id: str
    document_id: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[dict]
    hallucination_score: float
    is_grounded: bool
    session_id: str


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(400, "Only PDF files accepted")

    doc_id = str(uuid.uuid4())[:8]

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        raw_chunks = extract_document(tmp_path)
        chunks = chunk_document(raw_chunks)

        retriever = get_retriever(doc_id)
        retriever.index_chunks(chunks)

        # Estadísticas del documento
        text_chunks = [c for c in chunks if c["metadata"]["type"] == "text"]
        table_chunks = [c for c in chunks if c["metadata"]["type"] == "table"]

        return {
            "doc_id": doc_id,
            "filename": file.filename,
            "total_chunks": len(chunks),
            "text_chunks": len(text_chunks),
            "table_chunks": len(table_chunks),
            "pages": max(c["metadata"]["page"] for c in chunks),
        }
    finally:
        os.unlink(tmp_path)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    session_id = request.session_id
    doc_id = request.document_id

    if doc_id not in retriever_store:
        raise HTTPException(404, "Document not found. Please upload first.")

    # Recuperar historial de sesión
    session_messages = sessions.get(session_id, [])

    initial_state = {
        "messages": session_messages,
        "query": request.query,
        "expanded_queries": [],
        "retrieved_chunks": [],
        "answer": "",
        "sources": [],
        "hallucination_score": 1.0,
        "is_grounded": True,
        "session_id": session_id,
        "document_id": doc_id,
    }

    result = rag_graph.invoke(initial_state)

    # Guardar historial actualizado
    sessions[session_id] = result["messages"]

    # Serializar sources para JSON
    sources_serializable = []
    for s in result["sources"]:
        sources_serializable.append({
            "content": s["content"][:300],
            "page": s["metadata"].get("page"),
            "type": s["metadata"].get("type"),
            "section": s["metadata"].get("section"),
            "score": s.get("rerank_score", 0),
        })

    return ChatResponse(
        answer=result["answer"],
        sources=sources_serializable,
        hallucination_score=result["hallucination_score"],
        is_grounded=result["is_grounded"],
        session_id=session_id,
    )


@app.delete("/session/{session_id}")
async def clear_session(session_id: str):
    sessions.pop(session_id, None)
    return {"cleared": True}


@app.get("/health")
async def health():
    return {"status": "ok"}