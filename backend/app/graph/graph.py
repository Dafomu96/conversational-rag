from langgraph.graph import StateGraph, END
from app.graph.state import RAGState
from app.graph.nodes import expand_queries, retrieve_chunks, generate_answer, check_hallucination


def build_graph():
    graph = StateGraph(RAGState)

    graph.add_node("expand_queries", expand_queries)
    graph.add_node("retrieve", retrieve_chunks)
    graph.add_node("generate", generate_answer)
    graph.add_node("hallucination_check", check_hallucination)

    graph.set_entry_point("expand_queries")
    graph.add_edge("expand_queries", "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", "hallucination_check")

    def route_after_check(state: RAGState) -> str:
        # Si score muy bajo, podrías agregar un nodo de retry
        # Por ahora siempre termina
        return END

    graph.add_conditional_edges("hallucination_check", route_after_check)

    return graph.compile()


rag_graph = build_graph()