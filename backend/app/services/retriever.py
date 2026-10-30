"""Metadata-filtered semantic retrieval.

Order of operations (as required): (1) filter stored chunks by chapter/section/concept metadata,
(2) embed the query, (3) cosine similarity against ONLY the filtered chunks, (4) rank, take top-k.
"""
from dataclasses import dataclass

import numpy as np
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..models import TextbookChunk
from .embeddings import from_bytes, get_embedder


@dataclass
class RetrievedChunk:
    label: str            # E1, E2 ... (rank order)
    chunk_id: str
    score: float
    content: str
    concept_id: str
    section_title: str
    concept_title: str
    pdf_pages: list[int]
    chunk_index: int


def cosine_similarity(query: np.ndarray, matrix: np.ndarray) -> np.ndarray:
    qn = np.linalg.norm(query)
    mn = np.linalg.norm(matrix, axis=1)
    denom = np.where(mn * qn == 0, 1.0, mn * qn)
    return (matrix @ query) / denom


def retrieve(db: Session, query: str, *, concept_id: str | None = None, section_id: str | None = None,
             chapter_id: str | None = None, top_k: int | None = None) -> list[RetrievedChunk]:
    if not (concept_id or section_id or chapter_id):
        raise ValueError("retrieve() requires at least one metadata filter")
    stmt = select(TextbookChunk)
    if chapter_id:
        stmt = stmt.where(TextbookChunk.chapter_id == chapter_id)
    if section_id:
        stmt = stmt.where(TextbookChunk.section_id == section_id)
    if concept_id:
        stmt = stmt.where(TextbookChunk.concept_id == concept_id)
    chunks = list(db.scalars(stmt.order_by(TextbookChunk.concept_id, TextbookChunk.chunk_index)))
    if not chunks:
        return []
    k = top_k or get_settings().retrieval_top_k
    matrix = np.vstack([from_bytes(c.embedding) for c in chunks])
    sims = cosine_similarity(get_embedder().embed_query(query), matrix)
    order = np.argsort(-sims)[:k]
    out = []
    for rank, i in enumerate(order, 1):
        c = chunks[int(i)]
        meta = c.source_metadata or {}
        out.append(RetrievedChunk(
            label=f"E{rank}", chunk_id=c.id, score=round(float(sims[int(i)]), 4), content=c.content,
            concept_id=c.concept_id, section_title=c.section_title,
            concept_title=meta.get("concept_title", ""), pdf_pages=meta.get("pdf_pages", []),
            chunk_index=c.chunk_index))
    return out


def is_sufficient(chunks: list[RetrievedChunk]) -> bool:
    return sum(len(c.content) for c in chunks) >= get_settings().min_context_chars
