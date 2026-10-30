"""Adaptive remediation state machine.

Per (student, concept) row in `remediation_attempts`:
  active     remediation sequence in progress; `attempt_count` = FAILED remediation quizzes so far
  exhausted  attempt_count reached the limit (default 3) -> no more remediation quizzes; teacher advised
  resolved   mastery climbed back to >= 0.50; the next sequence (if ever needed) starts at 0

A remediation quiz is "failed" when mastery (after the EMA update) is still Weak (< 0.50).
Counters live in the database, so refreshing the page can never reset them.
"""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import get_settings
from ..core.errors import AppError
from ..models import ConceptMastery, Quiz, QuizAttempt, RemediationAttempt, StudyEvent, User
from ..schemas.remediation import RemediationOut
from . import generator, retriever
from .topics import detail, get_concept_or_404, require_available, topic_label

TEACHER_MESSAGE = ("You've completed the maximum number of remediation quizzes for this concept. "
                   "Please consult your teacher or attend office hours. You can still revisit the original "
                   "study notes and your full history at any time.")


def get_state(db: Session, user_id: int, concept_id: str) -> RemediationAttempt | None:
    return db.scalar(select(RemediationAttempt).where(
        RemediationAttempt.user_id == user_id, RemediationAttempt.concept_id == concept_id))


def _mastery(db: Session, user_id: int, concept_id: str) -> ConceptMastery | None:
    return db.scalar(select(ConceptMastery).where(
        ConceptMastery.user_id == user_id, ConceptMastery.concept_id == concept_id))


def on_quiz_submitted(db: Session, user_id: int, concept_id: str, quiz_type: str, new_score: float, level: str) -> None:
    """Called inside the quiz-submission transaction (caller commits)."""
    row = get_state(db, user_id, concept_id)
    if row is None:
        return
    row.last_score = new_score
    row.updated_at = datetime.now(timezone.utc)
    if level != "weak":
        row.remediation_status = "resolved"          # mastery recovered (Average or Good)
    elif quiz_type == "remediation" and row.remediation_status == "active":
        row.attempt_count += 1                      # a failed remediation quiz
        if row.attempt_count >= get_settings().remediation_max_failed:
            row.remediation_status = "exhausted"


def _out(db: Session, user_id: int, concept_id: str, row: RemediationAttempt) -> RemediationOut:
    s = get_settings()
    m = _mastery(db, user_id, concept_id)
    can_retry = row.remediation_status == "active" and row.attempt_count < s.remediation_max_failed
    message = TEACHER_MESSAGE if row.remediation_status == "exhausted" else None
    if row.remediation_status == "resolved":
        message = "Your mastery of this concept has improved beyond the Weak range. Keep practising to consolidate it."
    c = get_concept_or_404(db, concept_id)
    content = row.content_json or {}
    return RemediationOut(
        concept=detail(db, c), status=row.remediation_status, attempts_used=row.attempt_count,
        max_attempts=s.remediation_max_failed, can_retry=can_retry,
        mastery_score=m.mastery_score if m else None, mastery_level=m.mastery_level if m else None,
        content_markdown=content.get("markdown"), evidence=content.get("evidence", []),
        generated_at=row.content_generated_at, message=message)


def _weak_focus(db: Session, user_id: int, concept_id: str) -> str:
    """Question stems the student got wrong most recently -> used to steer retrieval."""
    att = db.scalar(select(QuizAttempt).where(QuizAttempt.user_id == user_id, QuizAttempt.concept_id == concept_id)
                    .order_by(QuizAttempt.created_at.desc()).limit(1))
    if not att:
        return ""
    quiz = db.get(Quiz, att.quiz_id)
    wrong = [q["question"] for q in quiz.questions_json
             if att.selected_answers_json.get(q["id"]) != quiz.answer_key_json[q["id"]]["correct"]]
    return " ".join(wrong)[:600]


def start(db: Session, user: User, concept_id: str, include_practice: bool = False,
          regenerate: bool = False) -> RemediationOut:
    concept = get_concept_or_404(db, concept_id)
    row = get_state(db, user.id, concept_id)
    m = _mastery(db, user.id, concept_id)
    if m is None and row is None:
        raise AppError(409, "no_mastery_record", "Take a quiz on this concept before starting revision.")
    if row is None or (row.remediation_status == "resolved"):
        if m is None or m.mastery_level != "weak":
            if row is not None:                      # let a resolved student re-read their revision page
                return _out(db, user.id, concept_id, row)
            raise AppError(409, "not_weak", "This concept is not currently in the Weak range, so remediation isn't needed.")
        if row is None:
            row = RemediationAttempt(user_id=user.id, concept_id=concept_id, attempt_count=0,
                                     last_score=m.mastery_score, remediation_status="active")
            db.add(row)
        else:                                        # new sequence after relapsing into Weak
            row.remediation_status, row.attempt_count, row.content_json = "active", 0, None
            row.last_score = m.mastery_score
        db.flush()

    if row.content_json is None or regenerate:
        require_available(db, concept)
        focus = _weak_focus(db, user.id, concept_id)
        label = topic_label(concept)
        # Restricted to the weak concept's chapter AND concept metadata
        chunks = retriever.retrieve(db, f"simple explanation of {label}. {focus}".strip(),
                                    concept_id=concept.id, chapter_id=concept.chapter_id)
        if not retriever.is_sufficient(chunks):
            raise AppError(422, "insufficient_content", "Not enough textbook material to build revision content.")
        md = generator.generate_remedial(label, chunks, focus, include_practice)
        row.content_json = {"markdown": md, "evidence": [
            {"label": c.label, "chunk_id": c.chunk_id, "score": c.score, "pdf_pages": c.pdf_pages,
             "section_title": c.section_title, "concept_title": c.concept_title, "text": c.content} for c in chunks]}
        row.content_generated_at = datetime.now(timezone.utc)
        db.add(StudyEvent(user_id=user.id, concept_id=concept_id, event_type="remedial"))
    db.commit()
    return _out(db, user.id, concept_id, row)


def get(db: Session, user: User, concept_id: str) -> RemediationOut:
    row = get_state(db, user.id, concept_id)
    if row is None:
        raise AppError(404, "no_remediation", "No revision has been started for this concept.")
    return _out(db, user.id, concept_id, row)


def retry_quiz(db: Session, user: User, concept_id: str) -> Quiz:
    from .quizzes import create_quiz            # avoid circular import
    row = get_state(db, user.id, concept_id)
    if row is None:
        raise AppError(409, "no_remediation", "Start revision for this concept first.")
    if row.remediation_status == "exhausted" or row.attempt_count >= get_settings().remediation_max_failed:
        raise AppError(409, "remediation_limit_reached", TEACHER_MESSAGE)
    if row.remediation_status != "active":
        raise AppError(409, "remediation_not_active", "This concept is no longer in remediation.")
    return create_quiz(db, user, concept_id, quiz_type="remediation", focus=_weak_focus(db, user.id, concept_id))
