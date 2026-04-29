from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.extraction.pdf_extractor import TextChunk
from typing import List, Dict, Any


def chunk_document(raw_chunks: List[TextChunk]) -> List[Dict[str, Any]]:
    """
    Texto → RecursiveCharacterTextSplitter
    Tablas → un chunk completo (no fragmentar)
    """
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100,
        separators=["\n\n", "\n", ". ", " "],
    )

    final_chunks = []

    for raw in raw_chunks:
        if raw.chunk_type == "table":
            # Tabla entera = un chunk
            final_chunks.append({
                "content": raw.content,
                "metadata": {
                    "page": raw.page,
                    "type": "table",
                    "section": raw.section or "Unknown",
                    "table_data": raw.table_data,
                }
            })
        else:
            # Texto → split
            splits = splitter.split_text(raw.content)
            for i, split in enumerate(splits):
                final_chunks.append({
                    "content": split,
                    "metadata": {
                        "page": raw.page,
                        "type": "text",
                        "section": raw.section or "Unknown",
                        "split_index": i,
                    }
                })

    return final_chunks