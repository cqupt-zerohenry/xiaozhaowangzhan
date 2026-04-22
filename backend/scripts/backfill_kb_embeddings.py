from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import select

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))

from app.db import SessionLocal
from app.models import KnowledgeChunk
from app.rag_service import embed_texts


def _needs_embedding(chunk: KnowledgeChunk) -> bool:
    emb = chunk.embedding
    return emb is None or not isinstance(emb, list) or len(emb) == 0


def backfill(batch_size: int = 32) -> dict[str, int]:
    db = SessionLocal()
    try:
        chunks = db.scalars(select(KnowledgeChunk).order_by(KnowledgeChunk.id)).all()
        pending = [chunk for chunk in chunks if _needs_embedding(chunk) and str(chunk.content or '').strip()]
        updated = 0
        skipped = len(chunks) - len(pending)

        for start in range(0, len(pending), batch_size):
            batch = pending[start:start + batch_size]
            texts = [str(item.content or '') for item in batch]
            vectors = embed_texts(texts)
            for item, vec in zip(batch, vectors, strict=False):
                if isinstance(vec, list) and len(vec) > 0:
                    item.embedding = vec
                    updated += 1

        db.commit()
        return {
            'total_chunks': len(chunks),
            'pending_chunks': len(pending),
            'updated_chunks': updated,
            'skipped_chunks': skipped,
        }
    finally:
        db.close()


if __name__ == '__main__':
    result = backfill()
    print(result)
