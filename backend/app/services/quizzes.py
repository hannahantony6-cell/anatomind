from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..config import get_settings
from ..core.errors import AppError
from ..models import Concept, Quiz, QuizAttempt, StudyEvent, User
from ..schemas.learning import QuizOption, QuizOut, QuizQuestionOut
from ..schemas.quiz import ConceptOutcome, QuestionResult, QuizResultOut, RemediationInfo
from . import generator, grading, mastery, remediation, retriever
from .topics import chunk_stats, detail, get_concept_or_404, require_available, topic_label

REUSE_WINDOW = timedelta(hours=6)



def create_quiz(db: Session, user: User, concept_id: str, quiz_type: str = "standard",
                force_new: bool = False, focus: str = "") -> Quiz:
    concept = get_concept_or_404(db, concept_id)
    require_available(db, concept)

    if not force_new:       # resume an unsubmitted quiz instead of spending another LLM call
        existing = db.scalar(
            select(Quiz).outerjoin(QuizAttempt, QuizAttempt.quiz_id == Quiz.id)
            .where(Quiz.user_id == user.id, Quiz.concept_id == concept_id, Quiz.quiz_type == quiz_type,
                   QuizAttempt.id.is_(None), Quiz.created_at > datetime.now(timezone.utc) - REUSE_WINDOW)
            .order_by(Quiz.created_at.desc()).limit(1))
        if existing:
            return existing

    label = topic_label(concept)
    chunks = retriever.retrieve(db, f"{label}. {focus}".strip(), concept_id=concept.id)
    if not retriever.is_sufficient(chunks):
        raise AppError(422, "insufficient_content", "Not enough textbook material was retrieved to build a quiz.")
    items = generator.generate_quiz(label, chunks, focus=focus)

    questions, key, refs = [], {}, {}
    for i, it in enumerate(items, 1):
        qid = f"q{i}"
        questions.append({"id": qid, "question": it["question"], "concept_id": concept.id, "aspect": it["aspect"],
                          "options": [{"id": k, "text": v} for k, v in sorted(it["options"].items())]})
        key[qid] = {"correct": it["correct"], "explanation": it["explanation"], "concept_id": concept.id,
                    "source_chunk_id": it["source_chunk_id"], "source_label": it["source_label"]}
        refs[qid] = {"chunk_id": it["source_chunk_id"], "label": it["source_label"]}
    quiz = Quiz(user_id=user.id, concept_id=concept.id, quiz_type=quiz_type, questions_json=questions,
                answer_key_json=key,
                source_references_json={"per_question": refs,
                                        "chunks": [{"chunk_id": c.chunk_id, "label": c.label, "score": c.score,
                                                    "pdf_pages": c.pdf_pages} for c in chunks]})
    db.add(quiz)
    db.commit()
    return quiz


def get_owned_quiz(db: Session, user: User, quiz_id: int) -> Quiz:
    quiz = db.scalar(select(Quiz).where(Quiz.id == quiz_id, Quiz.user_id == user.id))
    if not quiz:                                  # same 404 for "missing" and "someone else's"
        raise AppError(404, "quiz_not_found", "Quiz not found.")
    return quiz


def quiz_out(db: Session, quiz: Quiz) -> QuizOut:
    submitted = db.scalar(select(QuizAttempt.id).where(QuizAttempt.quiz_id == quiz.id)) is not None
    return QuizOut(
        id=quiz.id, concept=detail(db, db.get(Concept, quiz.concept_id)), quiz_type=quiz.quiz_type,
        submitted=submitted, created_at=quiz.created_at,
        questions=[QuizQuestionOut(id=q["id"], question=q["question"], concept_id=q["concept_id"],
                                   aspect=q.get("aspect"),
                                   options=[QuizOption(**o) for o in q["options"]]) for q in quiz.questions_json])


def submit_quiz(db: Session, user: User, quiz_id: int, answers: dict[str, str]) -> QuizResultOut:
    quiz = get_owned_quiz(db, user, quiz_id)
    if db.scalar(select(QuizAttempt.id).where(QuizAttempt.quiz_id == quiz.id)):
        raise AppError(409, "already_submitted", "This quiz has already been submitted.")
    key = quiz.answer_key_json
    unknown = set(answers) - set(key)
    if unknown:
        raise AppError(422, "invalid_answers", "Answers refer to questions that are not part of this quiz.")
    if any(a not in ("A", "B", "C", "D") for a in answers.values()):
        raise AppError(422, "invalid_answers", "Each answer must be one of A, B, C or D.")
    missing = [q for q in key if q not in answers]
    if missing:
        raise AppError(422, "unanswered", f"Please answer all {len(key)} questions before submitting.",
                       {"unanswered": missing})

    g = grading.grade(key, answers)                       # deterministic, backend-only
    perf = grading.concept_performance(g["per_question"])
    try:
        attempt = QuizAttempt(user_id=user.id, quiz_id=quiz.id, concept_id=quiz.concept_id,
                              attempt_type=quiz.quiz_type, selected_answers_json=answers,
                              correct_count=g["correct_count"], total_questions=g["total"], score=g["score"],
                              concept_results_json=[])
        db.add(attempt)
        db.flush()
        snapshots = []
        for cid, p in perf.items():
            m = mastery.apply_attempt(db, user.id, cid, attempt.id, p["performance"])
            remediation.on_quiz_submitted(db, user.id, cid, quiz.quiz_type, m["new"], m["level"])
            snapshots.append({"concept_id": cid, "correct": p["correct"], "total": p["total"],
                              "latest_performance": p["performance"], "previous_mastery": m["previous"],
                              "mastery_score": m["new"], "mastery_level": m["level"],
                              "had_incorrect": p["had_incorrect"]})
        attempt.concept_results_json = snapshots
        db.add(StudyEvent(user_id=user.id, concept_id=quiz.concept_id, event_type="quiz"))
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, "already_submitted", "This quiz has already been submitted.")
    return build_results(db, quiz, attempt)


def build_results(db: Session, quiz: Quiz, attempt: QuizAttempt) -> QuizResultOut:
    settings = get_settings()
    chunk_pages = {c["chunk_id"]: c["label"] for c in quiz.source_references_json.get("chunks", [])}
    concepts = {c.id: c for c in db.scalars(select(Concept).where(Concept.id.in_(
        {q["concept_id"] for q in quiz.questions_json} | {quiz.concept_id})))}
    results = []
    for q in quiz.questions_json:
        k = quiz.answer_key_json[q["id"]]
        sel = attempt.selected_answers_json.get(q["id"])
        results.append(QuestionResult(
            id=q["id"], question=q["question"], options=[QuizOption(**o) for o in q["options"]], selected=sel,
            correct=k["correct"], is_correct=sel == k["correct"], explanation=k["explanation"],
            concept_id=q["concept_id"], concept_title=concepts[q["concept_id"]].concept_title,
            source_chunk_id=k.get("source_chunk_id"), source_label=chunk_pages.get(k.get("source_chunk_id"))))
    outcomes = []
    for snap in attempt.concept_results_json:
        c = concepts.get(snap["concept_id"]) or db.get(Concept, snap["concept_id"])
        rem = remediation.get_state(db, attempt.user_id, c.id)
        level = snap["mastery_level"]
        action = {"good": "celebrate", "average": "reinforce", "weak": "remediate"}[level]
        msg = {"good": "Great work! You've shown strong mastery of this concept.",
               "average": "You're getting there. A short revision will help reinforce this concept.",
               "weak": "This concept needs more work. A simplified revision page has been prepared for you."}[level]
        nxt = None
        if level == "good":
            nxt = _next_available(db, c)
        outcomes.append(ConceptOutcome(
            concept_id=c.id, concept_title=c.concept_title, section_title=c.section_title,
            correct=snap["correct"], total=snap["total"], latest_performance=snap["latest_performance"],
            previous_mastery=snap["previous_mastery"], mastery_score=snap["mastery_score"], mastery_level=level,
            had_incorrect=snap["had_incorrect"], action=action, message=msg,
            remediation=RemediationInfo(status=rem.remediation_status if rem else "none",
                                        attempts_used=rem.attempt_count if rem else 0,
                                        max_attempts=settings.remediation_max_failed),
            next_concept=nxt))
    return QuizResultOut(
        attempt_id=attempt.id, quiz_id=quiz.id, quiz_type=quiz.quiz_type,
        concept=detail(db, concepts[quiz.concept_id]), correct_count=attempt.correct_count,
        total_questions=attempt.total_questions, score=attempt.score, submitted_at=attempt.created_at,
        questions=results, concept_outcomes=outcomes)


def get_results(db: Session, user: User, quiz_id: int) -> QuizResultOut:
    quiz = get_owned_quiz(db, user, quiz_id)
    attempt = db.scalar(select(QuizAttempt).where(QuizAttempt.quiz_id == quiz.id))
    if not attempt:
        raise AppError(409, "not_submitted", "Results are available only after the quiz is submitted.")
    return build_results(db, quiz, attempt)


def _next_available(db: Session, c: Concept) -> dict | None:
    cands = list(db.scalars(select(Concept).where(Concept.ordinal > c.ordinal).order_by(Concept.ordinal).limit(8)))
    stats = chunk_stats(db, [x.id for x in cands])
    for x in cands:
        if stats.get(x.id, (0, 0))[1] >= get_settings().min_context_chars:
            return {"concept_id": x.id, "title": x.concept_title, "section_title": x.section_title,
                    "chapter_title": x.chapter_title}
    return None
