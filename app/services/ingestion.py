from io import BytesIO
from typing import List
from pypdf import PdfReader

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """Extract raw text content from uploaded PDF or TXT files."""
    filename_lower = filename.lower()

    if filename_lower.endswith(".pdf"):
        reader = PdfReader(BytesIO(file_bytes))
        text_content: List[str] = []
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text_content.append(extracted)
        return "\n".join(text_content)

    elif filename_lower.endswith(".txt"):
        return file_bytes.decode("utf-8")

    else:
        raise ValueError("Unsupported file format. Only .pdf and .txt are allowed.")


def chunk_text_fixed_size(text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
    """Strategy A: Fixed-size character splitting with defined overlap."""
    if not text:
        return []

    chunks: List[str] = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap

    return chunks


def chunk_text_by_paragraph(text: str, min_length: int = 20) -> List[str]:
    """Strategy B: Semantic paragraph-based splitting using double line breaks."""
    if not text:
        return []

    paragraphs = text.split("\n\n")
    cleaned_chunks = [p.strip() for p in paragraphs if len(p.strip()) >= min_length]
    return cleaned_chunks