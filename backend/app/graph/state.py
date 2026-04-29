from typing import TypedDict, List, Optional, Annotated
from langchain_core.messages import BaseMessage
import operator


class RAGState(TypedDict):
    # Conversación
    messages: Annotated[List[BaseMessage], operator.add]
    query: str
    expanded_queries: List[str]
    
    # Retrieval
    retrieved_chunks: List[dict]
    
    # Generación
    answer: str
    sources: List[dict]
    
    # Validación
    hallucination_score: float
    is_grounded: bool
    
    # Sesión
    session_id: str
    document_id: Optional[str]