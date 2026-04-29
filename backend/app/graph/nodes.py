from dotenv import load_dotenv
load_dotenv()

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from app.graph.state import RAGState
from app.rag.retriever import HybridRetriever
from typing import Dict
import json
import re

llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
retriever_store: Dict[str, HybridRetriever] = {}  # doc_id → retriever


def get_retriever(doc_id: str) -> HybridRetriever:
    if doc_id not in retriever_store:
        retriever_store[doc_id] = HybridRetriever(collection_name=f"doc_{doc_id}")
    return retriever_store[doc_id]


# --- Node: Query Expansion ---
def expand_queries(state: RAGState) -> RAGState:
    query = state["query"]
    history_context = ""
    if state.get("messages"):
        last_turns = state["messages"][-4:]
        history_context = "\n".join(
            f"{'User' if isinstance(m, HumanMessage) else 'Assistant'}: {m.content}"
            for m in last_turns
        )

    prompt = f"""Given this conversation history:
{history_context}

Current question: {query}

Generate 2 alternative phrasings of this question to improve document retrieval.
Return ONLY a JSON array of strings, no explanation.
Example: ["alternative 1", "alternative 2"]"""

    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        expanded = json.loads(response.content)
        if not isinstance(expanded, list):
            expanded = []
    except Exception:
        expanded = []

    return {**state, "expanded_queries": [query] + expanded[:2]}


# --- Node: Retrieval ---
def retrieve_chunks(state: RAGState) -> RAGState:
    doc_id = state.get("document_id")
    if not doc_id:
        return {**state, "retrieved_chunks": []}

    retriever = get_retriever(doc_id)
    all_chunks = []
    seen_ids = set()

    for q in state["expanded_queries"]:
        chunks = retriever.retrieve(q, k=8, final_k=4)
        for c in chunks:
            if c["id"] not in seen_ids:
                seen_ids.add(c["id"])
                all_chunks.append(c)

    # Reordenar por rerank_score final
    all_chunks.sort(key=lambda x: x.get("rerank_score", 0), reverse=True)

    return {**state, "retrieved_chunks": all_chunks[:6]}


# --- Node: Generate Answer ---
def generate_answer(state: RAGState) -> RAGState:
    chunks = state["retrieved_chunks"]
    query = state["query"]

    # Construir contexto con metadatos
    context_parts = []
    for i, chunk in enumerate(chunks):
        meta = chunk["metadata"]
        label = f"[Source {i+1} | Page {meta.get('page', '?')} | {meta.get('type', 'text').upper()} | {meta.get('section', '')}]"
        context_parts.append(f"{label}\n{chunk['content']}")
    context = "\n\n---\n\n".join(context_parts)

    # Historial de conversación
    history = state.get("messages", [])
    messages = [
        SystemMessage(content=f"""You are a precise document analyst. Answer questions using ONLY the provided context.
Always cite your sources using [Source N] notation.
For tables, reference specific values and rows.
If the context doesn't contain the answer, say so clearly.

CONTEXT:
{context}""")
    ]
    messages.extend(history[-6:])  # últimos 3 turnos
    messages.append(HumanMessage(content=query))

    response = llm.invoke(messages)
    answer = response.content

    # Extraer fuentes citadas
    cited_indices = [int(m) - 1 for m in re.findall(r'\[Source (\d+)\]', answer)]
    sources = [chunks[i] for i in cited_indices if i < len(chunks)]
    if not sources:
        sources = chunks[:2]  # fallback

    new_messages = list(history) + [
        HumanMessage(content=query),
        AIMessage(content=answer)
    ]

    return {**state, "answer": answer, "sources": sources, "messages": new_messages}


# --- Node: Hallucination Check ---
def check_hallucination(state: RAGState) -> RAGState:
    answer = state["answer"]
    chunks = state["retrieved_chunks"]
    context = "\n\n".join(c["content"] for c in chunks)

    prompt = f"""You are a factual grounding checker. 

CONTEXT FROM DOCUMENT:
{context}

GENERATED ANSWER:
{answer}

Evaluate if every factual claim in the answer is supported by the context.
Respond ONLY with a JSON object:
{{"score": 0.0-1.0, "grounded": true/false, "issues": "description or none"}}

Score 1.0 = fully grounded, 0.0 = hallucinated."""

    response = llm.invoke([HumanMessage(content=prompt)])
    try:
        result = json.loads(response.content)
        score = float(result.get("score", 0.5))
        grounded = result.get("grounded", score > 0.7)
    except Exception:
        score = 0.5
        grounded = True

    return {**state, "hallucination_score": score, "is_grounded": grounded}