"""EMA concept mastery:  A_new = 0.6 * A_latest + 0.4 * A_previous  (alpha = 0.6)."""
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import ConceptMastery, MasteryHistory

ALPHA = 0.6
GOOD_MIN, AVERAGE_MIN = 0.80, 0.50


def ema_update(previous: float | None, latest: float, alpha: float = ALPHA) -> float:
    if not 0.0 <= latest <= 1.0:
        raise ValueError("latest performance must be within 0..1")
    if previous is None:                      # first attempt: initialise from observed performance
        return round(latest, 6)
    return round(alpha * latest + (1 - alpha) * previous, 6)


def classify(score: float) -> str:
    score = round(score, 6)                   # avoid float artefacts at the 0.5 / 0.8 boundaries
    if score >= GOOD_MIN:
        return "good"
    if score >= AVERAGE_MIN:
        return "average"
    return "weak"


def apply_attempt(db: Session, user_id: int, concept_id: str, attempt_id: int, latest: float) -> dict:
    """Update ONE student's mastery for ONE concept. Caller commits."""
    row = db.scalar(select(ConceptMastery).where(
        ConceptMastery.user_id == user_id, ConceptMastery.concept_id == concept_id))
    previous = row.mastery_score if row else None
    new = ema_update(previous, latest)
    level = classify(new)
    if row:
        row.mastery_score, row.mastery_level = new, level
        row.attempts_count += 1
        row.updated_at = datetime.now(timezone.utc)
    else:
        db.add(ConceptMastery(user_id=user_id, concept_id=concept_id, mastery_score=new,
                              mastery_level=level, attempts_count=1))
    db.add(MasteryHistory(user_id=user_id, concept_id=concept_id, attempt_id=attempt_id,
                          latest_performance=latest, previous_score=previous, new_score=new,
                          mastery_level=level))
    return {"previous": previous, "new": new, "level": level}
