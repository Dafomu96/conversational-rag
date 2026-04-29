import pdfplumber
from dataclasses import dataclass
from typing import List, Optional
import re


@dataclass
class TextChunk:
    content: str
    page: int
    chunk_type: str  # "text" | "table"
    section: Optional[str]
    table_data: Optional[list] = None  # raw table para rendering


def extract_document(pdf_path: str) -> List[TextChunk]:
    chunks = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            # 1. Extraer tablas primero para excluirlas del texto plano
            tables = page.extract_tables()
            table_bboxes = [t.bbox for t in page.find_tables()] if page.find_tables() else []

            # 2. Extraer texto evitando zonas de tablas
            if table_bboxes:
                # Crop fuera de las tablas
                text_page = page
                for bbox in table_bboxes:
                    # pdfplumber permite filtrar chars por bbox
                    pass
                raw_text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""
            else:
                raw_text = page.extract_text(x_tolerance=3, y_tolerance=3) or ""

            # Detectar sección (heurística: líneas en mayúsculas o numeradas)
            section = _detect_section(raw_text)

            # 3. Limpiar y guardar texto
            clean_text = _clean_text(raw_text)
            if clean_text.strip():
                chunks.append(TextChunk(
                    content=clean_text,
                    page=page_num,
                    chunk_type="text",
                    section=section,
                ))

            # 4. Tablas como chunks completos
            for table in tables:
                if table and len(table) > 1:
                    table_md = _table_to_markdown(table)
                    chunks.append(TextChunk(
                        content=table_md,
                        page=page_num,
                        chunk_type="table",
                        section=section,
                        table_data=table,
                    ))

    return chunks


def _detect_section(text: str) -> Optional[str]:
    lines = text.split("\n")[:5]
    for line in lines:
        line = line.strip()
        if re.match(r'^(\d+\.?\s+)?[A-Z][A-Z\s]{3,}$', line):
            return line.title()
        if re.match(r'^\d+\.\d*\s+\w+', line):
            return line
    return None


def _clean_text(text: str) -> str:
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def _table_to_markdown(table: list) -> str:
    if not table:
        return ""
    rows = []
    header = table[0]
    rows.append("| " + " | ".join(str(c or "") for c in header) + " |")
    rows.append("|" + "|".join(["---"] * len(header)) + "|")
    for row in table[1:]:
        rows.append("| " + " | ".join(str(c or "") for c in row) + " |")
    return "\n".join(rows)