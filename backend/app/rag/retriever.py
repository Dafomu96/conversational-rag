import chromadb
from chromadb.utils import embedding_functions
from rank_bm25 import BM25Okapi
from sentence_transformers import CrossEncoder
from typing import List, Dict, Any
import uuid
import numpy as np


CROSS_ENCODER_MODEL = "cross-encoder/ms-marco-MiniLM-L-6-v2"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"


class HybridRetriever:
    def __init__(self, collection_name: str = "rag_docs"):
        self.client = chromadb.PersistentClient(path="./chroma_db")
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=EMBEDDING_MODEL
        )
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            embedding_function=self.ef,
            metadata={"hnsw:space": "cosine"}
        )
        self.cross_encoder = CrossEncoder(CROSS_ENCODER_MODEL)
        self._bm25 = None
        self._all_docs: List[Dict] = []

    def index_chunks(self, chunks: List[Dict[str, Any]]):
        """Indexa chunks en ChromaDB y prepara BM25."""
        ids, documents, metadatas = [], [], []

        for chunk in chunks:
            doc_id = str(uuid.uuid4())
            ids.append(doc_id)
            documents.append(chunk["content"])
            # ChromaDB no acepta None en metadata
            meta = {k: v for k, v in chunk["metadata"].items()
                    if v is not None and k != "table_data"}
            metadatas.append(meta)

        self.collection.add(ids=ids, documents=documents, metadatas=metadatas)
        self._all_docs = [{"id": i, "content": d, "metadata": m}
                          for i, d, m in zip(ids, documents, metadatas)]

        # BM25 sobre todos los docs
        tokenized = [doc["content"].lower().split() for doc in self._all_docs]
        self._bm25 = BM25Okapi(tokenized)

    def retrieve(self, query: str, k: int = 10, final_k: int = 5) -> List[Dict]:
        """
        1. Semantic search (ChromaDB) → top k
        2. BM25 keyword search → top k
        3. Fusión por score (RRF)
        4. Cross-encoder reranking → top final_k
        """
        # --- Semántico ---
        semantic_results = self.collection.query(
            query_texts=[query],
            n_results=min(k, self.collection.count()),
            include=["documents", "metadatas", "distances"]
        )
        semantic_ids = set()
        candidates = []

        if semantic_results["ids"][0]:
            for doc_id, doc, meta, dist in zip(
                semantic_results["ids"][0],
                semantic_results["documents"][0],
                semantic_results["metadatas"][0],
                semantic_results["distances"][0],
            ):
                semantic_ids.add(doc_id)
                candidates.append({
                    "id": doc_id,
                    "content": doc,
                    "metadata": meta,
                    "semantic_score": 1 - dist,  # cosine similarity
                    "bm25_score": 0.0,
                })

        # --- BM25 ---
        if self._bm25 and self._all_docs:
            query_tokens = query.lower().split()
            bm25_scores = self._bm25.get_scores(query_tokens)
            top_bm25_idx = np.argsort(bm25_scores)[::-1][:k]

            for idx in top_bm25_idx:
                doc = self._all_docs[idx]
                if doc["id"] not in semantic_ids:
                    candidates.append({
                        "id": doc["id"],
                        "content": doc["content"],
                        "metadata": doc["metadata"],
                        "semantic_score": 0.0,
                        "bm25_score": float(bm25_scores[idx]),
                    })
                else:
                    # Enriquecer candidato ya existente
                    for c in candidates:
                        if c["id"] == doc["id"]:
                            c["bm25_score"] = float(bm25_scores[idx])

        # --- RRF Fusion ---
        for c in candidates:
            sem_rank = 1 / (1 + candidates.index(c))
            c["rrf_score"] = 0.6 * c["semantic_score"] + 0.4 * c["bm25_score"]

        candidates.sort(key=lambda x: x["rrf_score"], reverse=True)
        top_candidates = candidates[:k]

        # --- Cross-encoder reranking ---
        if top_candidates:
            pairs = [(query, c["content"]) for c in top_candidates]
            ce_scores = self.cross_encoder.predict(pairs)
            for c, score in zip(top_candidates, ce_scores):
                c["rerank_score"] = float(score)
            top_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        return top_candidates[:final_k]

    def clear(self):
        self.client.delete_collection(self.collection.name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection.name,
            embedding_function=self.ef,
        )
        self._bm25 = None
        self._all_docs = []