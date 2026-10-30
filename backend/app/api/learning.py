from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..core.deps import get_current_user
from ..core.errors import AppError
from ..database import get_db
from ..models import StudyEvent, TextbookChunk, User
from ..schemas.learning import EvidenceItem, NotesRequest, NotesResponse, QuizOut, QuizRequest, SourceOut
from ..services import generator, quizzes, retriever
from ..services.topics import detail, get_concept_or_404, require_available, topic_label

router = APIRouter(prefix="/learning", tags=["learning"])


@router.post("/notes", response_model=NotesResponse)
def notes(body: NotesRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    concept = get_concept_or_404(db, body.concept_id)
    require_available(db, concept)
    label = topic_label(concept)
    # metadata filter (concept) -> embed query -> cosine similarity -> rank
    chunks = retriever.retrieve(db, f"Study notes: definitions, structures, mechanisms and examples of {label}",
                                concept_id=concept.id, chapter_id=concept.chapter_id)
    if not retriever.is_sufficient(chunks):
        raise AppError(422, "insufficient_content",
                       "The available textbook material does not adequately cover this topic.")
    markdown = generator.generate_notes(label, chunks)
    db.add(StudyEvent(user_id=user.id, concept_id=concept.id, event_type="notes"))
    db.commit()
    return NotesResponse(
        concept=detail(db, concept), notes_markdown=markdown, model=get_settings().ollama_model,
        generated_at=datetime.now(timezone.utc), disclaimer=generator.DISCLAIMER,
        evidence=[EvidenceItem(label=c.label, chunk_id=c.chunk_id, score=c.score, section_title=c.section_title,
                               concept_title=concept.concept_title, pdf_pages=c.pdf_pages, text=c.content)
                  for c in chunks])


@router.post("/quiz", response_model=QuizOut, status_code=201)
def create_quiz(body: QuizRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    quiz = quizzes.create_quiz(db, user, body.concept_id, body.quiz_type, body.force_new)
    return quizzes.quiz_out(db, quiz)


@router.get("/sources", response_model=list[SourceOut])
def sources(chunk_id: list[str] = Query(min_length=1, max_length=20), _: User = Depends(get_current_user),
            db: Session = Depends(get_db)):
    rows = db.scalars(select(TextbookChunk).where(TextbookChunk.id.in_(chunk_id)))
    return [SourceOut(chunk_id=c.id, unit_title=c.unit_title, chapter_title=c.chapter_title,
                      section_title=c.section_title, concept_id=c.concept_id,
                      pdf_pages=(c.source_metadata or {}).get("pdf_pages", []),
                      source=(c.source_metadata or {}).get("source", ""), text=c.content) for c in rows]
