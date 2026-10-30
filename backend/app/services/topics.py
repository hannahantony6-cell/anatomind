from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..core.errors import AppError
from ..models import Concept, TextbookChunk
from ..schemas.topics import ConceptDetail


def chunk_stats(db: Session, concept_ids: list[str] | None = None) -> dict[str, tuple[int, int]]:
    q = select(TextbookChunk.concept_id, func.count(), func.coalesce(func.sum(func.length(TextbookChunk.content)), 0)
               ).group_by(TextbookChunk.concept_id)
    if concept_ids is not None:
        q = q.where(TextbookChunk.concept_id.in_(concept_ids))
    return {cid: (int(n), int(chars)) for cid, n, chars in db.execute(q)}


def get_concept_or_404(db: Session, concept_id: str) -> Concept:
    c = db.get(Concept, concept_id)
    if not c:
        raise AppError(404, "topic_not_found", "That topic does not exist in the indexed textbook.")
    return c


def detail(db: Session, c: Concept) -> ConceptDetail:
    n, chars = chunk_stats(db, [c.id]).get(c.id, (0, 0))
    return ConceptDetail(
        id=c.id, title=c.concept_title, unit_id=c.unit_id, unit_title=c.unit_title, chapter_id=c.chapter_id,
        chapter_number=c.chapter_number, chapter_title=c.chapter_title, section_id=c.section_id,
        section_number=c.section_number, section_title=c.section_title, page_start=c.page_start,
        page_end=c.page_end, chunk_count=n, available=chars >= get_settings().min_context_chars)


def topic_label(c: Concept) -> str:
    """Human label used in prompts."""
    if c.concept_title == "Overview":
        return f"{c.section_number} {c.section_title} (overview)"
    return f"{c.section_number} {c.section_title}: {c.concept_title}"


def require_available(db: Session, c: Concept) -> None:
    _, chars = chunk_stats(db, [c.id]).get(c.id, (0, 0))
    if chars < get_settings().min_context_chars:
        raise AppError(422, "insufficient_content",
                       "The indexed textbook does not contain enough material for this topic, "
                       "so AI generation is disabled for it.")
