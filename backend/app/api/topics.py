from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..core.deps import get_current_user
from ..database import get_db
from ..models import Concept, User
from ..schemas.topics import (ChapterOut, ConceptDetail, ConceptOut, FlatChapterOut, FlatSectionOut, FlatUnitOut,
                              SectionOut, UnitOut)
from ..services.topics import chunk_stats, detail, get_concept_or_404

router = APIRouter(prefix="/topics", tags=["topics"], dependencies=[Depends(get_current_user)])


def _concept_out(c: Concept, stats) -> ConceptOut:
    n, chars = stats.get(c.id, (0, 0))
    return ConceptOut(id=c.id, title=c.concept_title, ordinal=c.ordinal, chunk_count=n, char_count=chars,
                      available=chars >= get_settings().min_context_chars)


@router.get("/tree", response_model=list[UnitOut])
def tree(db: Session = Depends(get_db)):
    """Full Unit -> Chapter -> Section -> Concept hierarchy, built from the indexed concepts."""
    rows = list(db.scalars(select(Concept).order_by(Concept.ordinal)))
    stats = chunk_stats(db)
    units: dict[str, UnitOut] = {}
    chapters: dict[str, ChapterOut] = {}
    sections: dict[str, SectionOut] = {}
    for c in rows:
        u = units.setdefault(c.unit_id, UnitOut(id=c.unit_id, number=c.unit_number, title=c.unit_title))
        ch = chapters.get(c.chapter_id)
        if ch is None:
            ch = chapters[c.chapter_id] = ChapterOut(id=c.chapter_id, number=c.chapter_number, title=c.chapter_title)
            u.chapters.append(ch)
        s = sections.get(c.section_id)
        if s is None:
            s = sections[c.section_id] = SectionOut(id=c.section_id, number=c.section_number, title=c.section_title)
            ch.sections.append(s)
        s.concepts.append(_concept_out(c, stats))
    return list(units.values())


@router.get("/units", response_model=list[FlatUnitOut])
def units(db: Session = Depends(get_db)):
    seen, out = set(), []
    for c in db.scalars(select(Concept).order_by(Concept.ordinal)):
        if c.unit_id not in seen:
            seen.add(c.unit_id)
            out.append(FlatUnitOut(id=c.unit_id, number=c.unit_number, title=c.unit_title))
    return out


@router.get("/chapters", response_model=list[FlatChapterOut])
def chapters(unit_id: str | None = None, db: Session = Depends(get_db)):
    q = select(Concept).order_by(Concept.ordinal)
    if unit_id:
        q = q.where(Concept.unit_id == unit_id)
    seen, out = set(), []
    for c in db.scalars(q):
        if c.chapter_id not in seen:
            seen.add(c.chapter_id)
            out.append(FlatChapterOut(id=c.chapter_id, number=c.chapter_number, title=c.chapter_title, unit_id=c.unit_id))
    return out


@router.get("/sections", response_model=list[FlatSectionOut])
def sections(chapter_id: str, db: Session = Depends(get_db)):
    seen, out = set(), []
    for c in db.scalars(select(Concept).where(Concept.chapter_id == chapter_id).order_by(Concept.ordinal)):
        if c.section_id not in seen:
            seen.add(c.section_id)
            out.append(FlatSectionOut(id=c.section_id, number=c.section_number, title=c.section_title, chapter_id=c.chapter_id))
    return out


@router.get("/concepts", response_model=list[ConceptOut])
def concepts(section_id: str, db: Session = Depends(get_db)):
    rows = list(db.scalars(select(Concept).where(Concept.section_id == section_id).order_by(Concept.ordinal)))
    stats = chunk_stats(db, [c.id for c in rows])
    return [_concept_out(c, stats) for c in rows]


@router.get("/concepts/{concept_id}", response_model=ConceptDetail)
def concept_detail(concept_id: str, db: Session = Depends(get_db)):
    return detail(db, get_concept_or_404(db, concept_id))


@router.get("/search", response_model=list[ConceptDetail])
def search(q: str = Query(min_length=2, max_length=80), limit: int = Query(30, ge=1, le=100),
           db: Session = Depends(get_db)):
    like = "%" + q.strip().replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%"
    rows = db.scalars(select(Concept).where(
        Concept.concept_title.ilike(like, escape="\\") | Concept.section_title.ilike(like, escape="\\")
        | Concept.chapter_title.ilike(like, escape="\\")).order_by(Concept.ordinal).limit(limit))
    return [detail(db, c) for c in rows]
