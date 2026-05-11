"""文本提取与分块"""

import os
import re


def parse_document(file_bytes: bytes, filename: str) -> str:
    ext = os.path.splitext(filename)[1].lower()

    if ext == ".pdf":
        return _parse_pdf(file_bytes)
    elif ext == ".docx":
        return _parse_docx(file_bytes)
    elif ext == ".txt":
        return file_bytes.decode("utf-8", errors="replace")
    else:
        raise ValueError(f"不支持的文件格式: {ext}")


def _parse_pdf(file_bytes: bytes) -> str:
    from pypdf import PdfReader
    reader = PdfReader(file_bytes)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text.strip():
            pages.append(text.strip())
    return "\n\n".join(pages)


def _parse_docx(file_bytes: bytes) -> str:
    import docx
    from io import BytesIO
    doc = docx.Document(BytesIO(file_bytes))
    paras = [p.text.strip() for p in doc.paragraphs if p.text.strip()]
    return "\n\n".join(paras)


def chunk_text(text: str, chunk_size: int = 800, overlap: int = 200) -> list[str]:
    """将文本切分为重叠的段落块"""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]

    chunks = []
    current = []
    current_len = 0

    for para in paragraphs:
        if current_len + len(para) > chunk_size and current:
            chunks.append("\n\n".join(current))
            # 保留尾部段落作为 overlap
            overlap_texts = []
            overlap_len = 0
            for p in reversed(current):
                if overlap_len + len(p) > overlap:
                    break
                overlap_texts.insert(0, p)
                overlap_len += len(p)
            current = overlap_texts
            current_len = overlap_len

        current.append(para)
        current_len += len(para)

    if current:
        chunks.append("\n\n".join(current))

    return chunks if chunks else [text[:chunk_size]]
