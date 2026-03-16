"""RAG service — PDF extraction + TF-IDF search for RIZALTA documents."""

import os
import logging
from pathlib import Path

import fitz  # pymupdf
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

# Module-level state (initialized once at startup)
_chunks: list[dict] = []
_vectorizer: TfidfVectorizer | None = None
_tfidf_matrix = None

# Document display names
DOC_NAMES = {
    "ddu.pdf": "ДДУ",
    "arenda.pdf": "Договор аренды",
}


def _extract_text(pdf_path: str) -> list[dict]:
    """Extract text from PDF, returning list of {text, page} per page."""
    pages = []
    doc = fitz.open(pdf_path)
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text().strip()
        if text:
            pages.append({"text": text, "page": page_num + 1})
    doc.close()
    return pages


def _chunk_text(
    pages: list[dict],
    source: str,
    chunk_size: int = 600,
    overlap: int = 100,
) -> list[dict]:
    """Split page texts into overlapping chunks with metadata."""
    chunks = []
    for page_info in pages:
        text = page_info["text"]
        page = page_info["page"]
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk_text = text[start:end]
            if chunk_text.strip():
                chunks.append({
                    "text": chunk_text.strip(),
                    "source": source,
                    "page": page,
                })
            start += chunk_size - overlap
    return chunks


def init():
    """Initialize RAG: extract PDFs, build TF-IDF index. Call once at startup."""
    global _chunks, _vectorizer, _tfidf_matrix

    docs_dir = os.getenv("RAG_DOCS_DIR", "/opt/bot-dev/docs")
    files = ["ddu.pdf", "arenda.pdf"]

    all_chunks = []
    for filename in files:
        pdf_path = os.path.join(docs_dir, filename)
        if not os.path.exists(pdf_path):
            logger.warning(f"[RAG] File not found: {pdf_path}")
            continue

        source = DOC_NAMES.get(filename, filename)
        pages = _extract_text(pdf_path)
        chunks = _chunk_text(pages, source)
        all_chunks.extend(chunks)
        logger.info(f"[RAG] {filename}: {len(pages)} pages, {len(chunks)} chunks")

    if not all_chunks:
        logger.warning("[RAG] No documents loaded — RAG disabled")
        return

    _chunks = all_chunks

    # Build TF-IDF index
    _vectorizer = TfidfVectorizer(
        max_features=10000,
        ngram_range=(1, 2),
        sublinear_tf=True,
    )
    texts = [c["text"] for c in _chunks]
    _tfidf_matrix = _vectorizer.fit_transform(texts)

    logger.info(f"[RAG] Index built: {len(_chunks)} chunks, {_tfidf_matrix.shape[1]} features")


def search_documents(query: str, top_k: int = 5) -> list[dict]:
    """Search documents by query. Returns [{text, source, page}, ...]."""
    if _vectorizer is None or _tfidf_matrix is None or not _chunks:
        return []

    query_vec = _vectorizer.transform([query])
    scores = cosine_similarity(query_vec, _tfidf_matrix).flatten()

    # Get top_k indices sorted by score descending
    top_indices = scores.argsort()[::-1][:top_k]

    results = []
    for idx in top_indices:
        if scores[idx] > 0.01:  # minimum relevance threshold
            results.append({
                "text": _chunks[idx]["text"],
                "source": _chunks[idx]["source"],
                "page": _chunks[idx]["page"],
                "score": float(scores[idx]),
            })

    return results
