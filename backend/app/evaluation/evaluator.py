"""
Evaluación completa: RAGAS + tablas + memoria conversacional
Ejecutar: python -m app.evaluation.evaluator
"""
import json
import csv
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision, context_recall
from langchain_groq import ChatGroq
from langchain_community.embeddings import HuggingFaceEmbeddings

# --- Dataset de test (mínimo 20 preguntas) ---
# Adapta esto a tu PDF de prueba. Aquí estructura genérica.
TEST_DATASET = [
    # Preguntas de texto plano
    {
        "id": "T1", "type": "text",
        "question": "What is the main objective described in the introduction?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    {
        "id": "T2", "type": "text",
        "question": "What methodology was used in the study?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    {
        "id": "T3", "type": "text",
        "question": "What are the main conclusions of the document?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    {
        "id": "T4", "type": "text",
        "question": "Who are the authors or organizations mentioned?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    {
        "id": "T5", "type": "text",
        "question": "What limitations are discussed?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    # Preguntas de tablas
    {
        "id": "TB1", "type": "table",
        "question": "What is the value in the first row of the main results table?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    {
        "id": "TB2", "type": "table",
        "question": "Which category shows the highest value according to the data?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    {
        "id": "TB3", "type": "table",
        "question": "What is the total or sum shown in the summary table?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    {
        "id": "TB4", "type": "table",
        "question": "Compare the values across the columns in the data table.",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    {
        "id": "TB5", "type": "table",
        "question": "What percentage or ratio is shown in the table?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    # Preguntas encadenadas (memoria)
    {
        "id": "C1", "type": "conversational", "chain": 1,
        "question": "What is the document about?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    {
        "id": "C2", "type": "conversational", "chain": 1,
        "question": "Can you elaborate on what you just explained?",  # requiere memoria
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    {
        "id": "C3", "type": "conversational", "chain": 1,
        "question": "Based on that, what would you recommend?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    {
        "id": "C4", "type": "conversational", "chain": 2,
        "question": "What are the key metrics mentioned?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    {
        "id": "C5", "type": "conversational", "chain": 2,
        "question": "How do those metrics compare to industry standards?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    # Más texto
    {
        "id": "T6", "type": "text",
        "question": "What future work is proposed?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    {
        "id": "T7", "type": "text",
        "question": "What datasets or sources are referenced?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    {
        "id": "T8", "type": "text",
        "question": "What technical terms are defined in the document?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    {
        "id": "TB6", "type": "table",
        "question": "What are the column headers in the main table?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
    {
        "id": "TB7", "type": "table",
        "question": "Which row has the minimum value in the table?",
        "ground_truth": "FILL_WITH_ACTUAL_ANSWER",
    },
]


def run_evaluation(doc_id: str, api_base: str = "http://localhost:8000"):
    """Ejecuta evaluación completa y genera informe."""
    import httpx
    import uuid

    print("🔍 Starting evaluation pipeline...")
    results = []
    
    # Sesiones separadas para texto, tablas, y cada cadena conversacional
    sessions = {
        "text": str(uuid.uuid4()),
        "table": str(uuid.uuid4()),
        "chain_1": str(uuid.uuid4()),
        "chain_2": str(uuid.uuid4()),
    }

    ragas_data = {"question": [], "answer": [], "contexts": [], "ground_truth": []}

    with httpx.Client(timeout=120) as client:
        for item in TEST_DATASET:
            q_type = item["type"]
            chain = item.get("chain", 0)

            # Seleccionar sesión
            if q_type == "conversational":
                session_id = sessions[f"chain_{chain}"]
            elif q_type == "table":
                session_id = sessions["table"]
            else:
                session_id = sessions["text"]

            print(f"  [{item['id']}] {item['question'][:60]}...")

            res = client.post(f"{api_base}/chat", json={
                "query": item["question"],
                "session_id": session_id,
                "document_id": doc_id,
            })
            data = res.json()

            result = {
                "id": item["id"],
                "type": q_type,
                "question": item["question"],
                "answer": data["answer"],
                "ground_truth": item["ground_truth"],
                "sources": data["sources"],
                "hallucination_score": data["hallucination_score"],
                "is_grounded": data["is_grounded"],
            }
            results.append(result)

            ragas_data["question"].append(item["question"])
            ragas_data["answer"].append(data["answer"])
            ragas_data["contexts"].append([s["content"] for s in data["sources"]])
            ragas_data["ground_truth"].append(item["ground_truth"])

    # RAGAS evaluation
    print("\n📊 Running RAGAS metrics...")
    llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")

    dataset = Dataset.from_dict(ragas_data)
    ragas_results = evaluate(
        dataset,
        metrics=[faithfulness, answer_relevancy, context_precision, context_recall],
        llm=llm,
        embeddings=embeddings,
    )
    ragas_df = ragas_results.to_pandas()

    # Métricas por tipo
    type_labels = [r["type"] for r in results]
    ragas_df["type"] = type_labels
    ragas_df["id"] = [r["id"] for r in results]
    ragas_df["hallucination_score"] = [r["hallucination_score"] for r in results]
    ragas_df["is_grounded"] = [r["is_grounded"] for r in results]

    # Guardar CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    os.makedirs("evaluation_results", exist_ok=True)
    csv_path = f"evaluation_results/eval_{timestamp}.csv"
    ragas_df.to_csv(csv_path, index=False)
    print(f"\n✅ Results saved: {csv_path}")

    # Generar visualizaciones
    _generate_plots(ragas_df, timestamp)

    # Imprimir resumen
    _print_summary(ragas_df)

    return ragas_df


def _generate_plots(df: pd.DataFrame, timestamp: str):
    metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall"]
    available = [m for m in metrics if m in df.columns]

    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    fig.patch.set_facecolor('#1a1814')

    # Plot 1: Scores por métrica y tipo
    type_means = df.groupby("type")[available].mean()
    type_means.plot(kind="bar", ax=axes[0], colormap="Set2")
    axes[0].set_title("RAGAS Scores by Question Type", color='white', fontsize=12)
    axes[0].set_facecolor('#0f0e0c')
    axes[0].tick_params(colors='white')
    axes[0].legend(fontsize=8)
    axes[0].set_ylim(0, 1)

    # Plot 2: Hallucination scores
    df.groupby("type")["hallucination_score"].mean().plot(
        kind="bar", ax=axes[1], color=['#4ade80', '#60a5fa', '#f59e0b']
    )
    axes[1].set_title("Grounding Score by Type", color='white', fontsize=12)
    axes[1].set_facecolor('#0f0e0c')
    axes[1].tick_params(colors='white')
    axes[1].set_ylim(0, 1)

    plt.tight_layout()
    plot_path = f"evaluation_results/eval_{timestamp}.png"
    plt.savefig(plot_path, dpi=150, bbox_inches='tight')
    print(f"📈 Plot saved: {plot_path}")


def _print_summary(df: pd.DataFrame):
    metrics = ["faithfulness", "answer_relevancy", "context_precision", "context_recall", "hallucination_score"]
    available = [m for m in metrics if m in df.columns]
    
    print("\n" + "="*50)
    print("EVALUATION SUMMARY")
    print("="*50)
    for metric in available:
        val = df[metric].mean()
        print(f"  {metric:30s}: {val:.3f}")
    print("\nBy question type:")
    print(df.groupby("type")[available].mean().to_string())
    print("="*50)


if __name__ == "__main__":
    import sys
    doc_id = sys.argv[1] if len(sys.argv) > 1 else input("Enter doc_id: ")
    run_evaluation(doc_id)