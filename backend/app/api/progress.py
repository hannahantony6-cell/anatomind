from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..core.deps import get_current_user
from ..database import get_db
from ..models import Concept, ConceptMastery, MasteryHistory, QuizAttempt, RemediationAttempt, StudyEvent, User
from ..schemas.progress import (AttemptOut, HistoryOut, MasteryOverview, RecentTopic, SummaryOut, TopicMasteryOut,
                                TrendPoint, WeakConcept)

router = APIRouter(prefix="/progress", tags=["progress"])


def _ref(c: Concept) -> dict:
    return dict(concept_id=c.id, concept_title=c.concept_title, section_title=c.section_title,
                chapter_title=c.chapter_title, chapter_number=c.chapter_number)


def _remediation_map(db: Session, user_id: int) -> dict[str, str]:
    return {r.concept_id: r.remediation_status
            for r in db.scalars(select(RemediationAttempt).where(RemediationAttempt.user_id == user_id))}


def _last_studied(db: Session, user_id: int) -> dict:
    return dict(db.execute(select(StudyEvent.concept_id, func.max(StudyEvent.created_at))
                           .where(StudyEvent.user_id == user_id).group_by(StudyEvent.concept_id)).all())


@router.get("/summary", response_model=SummaryOut)
def summary(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    studied = db.scalar(select(func.count(func.distinct(StudyEvent.concept_id))).where(
        StudyEvent.user_id == user.id, StudyEvent.event_type == "notes")) or 0
    n_quiz, avg = db.execute(select(func.count(), func.avg(QuizAttempt.score)).where(
        QuizAttempt.user_id == user.id)).one()
    rows = list(db.execute(select(ConceptMastery, Concept).join(Concept, Concept.id == ConceptMastery.concept_id)
                           .where(ConceptMastery.user_id == user.id)))
    counts = {"good": 0, "average": 0, "weak": 0}
    for m, _ in rows:
        counts[m.mastery_level] += 1
    rem = _remediation_map(db, user.id)
    weak = sorted([(m, c) for m, c in rows if m.mastery_level == "weak"], key=lambda t: t[0].mastery_score)[:8]
    last = _last_studied(db, user.id)
    recent_ids = sorted(last, key=lambda k: last[k], reverse=True)[:6]
    cmap = {c.id: c for c in db.scalars(select(Concept).where(Concept.id.in_(recent_ids)))} if recent_ids else {}
    recent = [RecentTopic(**_ref(cmap[i]), last_studied_at=last[i]) for i in recent_ids if i in cmap]
    return SummaryOut(
        full_name=user.full_name, topics_studied=studied, quizzes_completed=n_quiz,
        average_score=round(float(avg), 1) if avg is not None else None,
        mastery=MasteryOverview(**counts, tracked=len(rows),
                                average_mastery=round(sum(m.mastery_score for m, _ in rows) / len(rows), 3) if rows else None),
        weak_concepts=[WeakConcept(**_ref(c), mastery_score=m.mastery_score,
                                   remediation_status=rem.get(c.id, "none")) for m, c in weak],
        recent_topics=recent, continue_learning=recent[0] if recent else None)


@router.get("/topics", response_model=list[TopicMasteryOut])
def topics(level: str | None = Query(None, pattern="^(good|average|weak)$"),
           user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = (select(ConceptMastery, Concept).join(Concept, Concept.id == ConceptMastery.concept_id)
         .where(ConceptMastery.user_id == user.id).order_by(ConceptMastery.mastery_score))
    if level:
        q = q.where(ConceptMastery.mastery_level == level)
    rows = list(db.execute(q))
    hist: dict[str, list[MasteryHistory]] = {}
    for h in db.scalars(select(MasteryHistory).where(MasteryHistory.user_id == user.id)
                        .order_by(MasteryHistory.created_at, MasteryHistory.id)):
        hist.setdefault(h.concept_id, []).append(h)
    rem, last = _remediation_map(db, user.id), _last_studied(db, user.id)
    out = []
    for m, c in rows:
        h = hist.get(c.id, [])
        out.append(TopicMasteryOut(
            **_ref(c), mastery_score=m.mastery_score, mastery_level=m.mastery_level, attempts=m.attempts_count,
            previous_score=h[-1].previous_score if h else None, latest_score=m.mastery_score,
            last_studied_at=last.get(c.id), needs_revision=m.mastery_level != "good",
            remediation_status=rem.get(c.id, "none"),
            trend=[TrendPoint(at=x.created_at, score=x.new_score) for x in h[-12:]]))
    return out


@router.get("/history", response_model=HistoryOut)
def history(limit: int = Query(50, ge=1, le=200), offset: int = Query(0, ge=0),
            user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total = db.scalar(select(func.count()).select_from(QuizAttempt).where(QuizAttempt.user_id == user.id)) or 0
    rows = db.execute(select(QuizAttempt, Concept).join(Concept, Concept.id == QuizAttempt.concept_id)
                      .where(QuizAttempt.user_id == user.id).order_by(QuizAttempt.created_at.desc(), QuizAttempt.id.desc())
                      .limit(limit).offset(offset))
    return HistoryOut(total=total, attempts=[
        AttemptOut(**_ref(c), attempt_id=a.id, quiz_id=a.quiz_id, attempt_type=a.attempt_type,
                   correct_count=a.correct_count, total_questions=a.total_questions, score=a.score,
                   created_at=a.created_at) for a, c in rows])
