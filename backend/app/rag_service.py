"""RAG service: text chunking, local sentence-transformers embedding, hybrid retrieval.

Embedding uses a local multilingual model (no API key needed).
LLM generation is handled separately by llm_service.py.
"""

from __future__ import annotations

import logging
import re
from typing import Sequence

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity as sklearn_cosine

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Text chunking
# ---------------------------------------------------------------------------

_SENTENCE_SPLIT = re.compile(r'(?<=[。！？.!?\n])\s*')


def chunk_text(text: str, chunk_size: int = 400, overlap: int = 80) -> list[str]:
    """Split *text* into overlapping chunks of roughly *chunk_size* characters."""
    text = text.strip()
    if not text:
        return []

    paragraphs = re.split(r'\n{2,}', text)
    sentences: list[str] = []
    for para in paragraphs:
        parts = _SENTENCE_SPLIT.split(para.strip())
        sentences.extend(p.strip() for p in parts if p.strip())

    if not sentences:
        return [text[:chunk_size]] if text else []

    chunks: list[str] = []
    current = ''
    for sent in sentences:
        if len(current) + len(sent) + 1 > chunk_size and current:
            chunks.append(current)
            current = current[-overlap:] + ' ' + sent if overlap else sent
        else:
            current = (current + ' ' + sent).strip() if current else sent

    if current:
        chunks.append(current)

    return chunks


# ---------------------------------------------------------------------------
# Local Embedding via sentence-transformers
# ---------------------------------------------------------------------------

import threading

_model = None
_model_lock = threading.Lock()


def _get_model():
    """Lazy-load the sentence-transformers model (thread-safe, downloaded on first use, ~130 MB)."""
    global _model
    if _model is not None:
        return _model
    with _model_lock:
        if _model is not None:
            return _model
        try:
            from sentence_transformers import SentenceTransformer
            from app.config import settings
            model_name = settings.embedding_model
            logger.info('Loading embedding model: %s (first load will download ~130 MB)', model_name)
            _model = SentenceTransformer(model_name)
            logger.info('Embedding model loaded successfully')
            return _model
        except Exception as exc:
            logger.error('Failed to load sentence-transformers model: %s — falling back to TF-IDF', exc)
            return None


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Encode texts into dense vectors using the local model."""
    model = _get_model()
    if model is not None:
        embeddings = model.encode(texts, show_progress_bar=False, normalize_embeddings=True)
        return [emb.tolist() for emb in embeddings]

    # Fallback: TF-IDF if sentence-transformers is not available
    return _tfidf_embed(texts)


def embed_one(text: str) -> list[float]:
    return embed_texts([text])[0]


# ---------------------------------------------------------------------------
# TF-IDF fallback (used if sentence-transformers fails to load)
# ---------------------------------------------------------------------------

_CHINESE_RE = re.compile(r'[\u4e00-\u9fff]+')
_ENGLISH_RE = re.compile(r'[A-Za-z][A-Za-z0-9#+.-]*')


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    tokens.extend(m.group().lower() for m in _ENGLISH_RE.finditer(text))
    for m in _CHINESE_RE.finditer(text):
        segment = m.group()
        for i in range(len(segment) - 1):
            tokens.append(segment[i:i + 2])
        if len(segment) == 1:
            tokens.append(segment)
    return tokens


def _tfidf_embed(texts: list[str]) -> list[list[float]]:
    if not texts:
        return []
    vec = TfidfVectorizer(tokenizer=_tokenize, token_pattern=None, max_features=384, sublinear_tf=True)
    try:
        matrix = vec.fit_transform(texts).toarray()
        return [row.tolist() for row in matrix]
    except Exception:
        return [[0.0] * 384 for _ in texts]


# ---------------------------------------------------------------------------
# Hybrid retrieval (dense embedding + sparse TF-IDF)
# ---------------------------------------------------------------------------

def retrieve_chunks(
    query: str,
    chunk_texts: list[str],
    chunk_embeddings: list[list[float] | None],
    top_k: int = 5,
    dense_weight: float = 0.6,
    sparse_weight: float = 0.4,
) -> list[tuple[int, float]]:
    """Return list of (chunk_index, score) for the most relevant chunks."""
    if not chunk_texts:
        return []

    n = len(chunk_texts)

    # --- Sparse retrieval: TF-IDF cosine ---
    try:
        sparse_vec = TfidfVectorizer(tokenizer=_tokenize, token_pattern=None, max_features=4096, sublinear_tf=True)
        corpus_matrix = sparse_vec.fit_transform(chunk_texts)
        query_vec = sparse_vec.transform([query])
        sparse_scores = sklearn_cosine(query_vec, corpus_matrix).flatten()
    except Exception:
        sparse_scores = np.zeros(n)

    # --- Dense retrieval: stored embeddings ---
    dense_scores = np.zeros(n)
    valid = [e for e in chunk_embeddings if e is not None and len(e) > 0]
    if valid:
        try:
            dim = len(valid[0])
            emb_matrix = np.array([
                e if e is not None and len(e) == dim else [0.0] * dim
                for e in chunk_embeddings
            ])
            query_emb = np.array(embed_texts([query]))
            # If dimensions differ (model changed), skip dense
            if query_emb.shape[1] == emb_matrix.shape[1]:
                dense_scores = sklearn_cosine(query_emb, emb_matrix).flatten()
        except Exception:
            pass

    final_scores = dense_weight * dense_scores + sparse_weight * sparse_scores
    indexed = sorted(enumerate(final_scores), key=lambda x: x[1], reverse=True)
    return [(idx, float(score)) for idx, score in indexed[:top_k] if score > 0]


# ---------------------------------------------------------------------------
# Chunk and embed a document
# ---------------------------------------------------------------------------

def chunk_and_embed(
    text: str,
    chunk_size: int = 400,
    overlap: int = 80,
) -> list[tuple[str, list[float]]]:
    """Chunk text and return (chunk_content, embedding) pairs."""
    chunks = chunk_text(text, chunk_size, overlap)
    if not chunks:
        return []

    embeddings = embed_texts(chunks)
    return list(zip(chunks, embeddings))
