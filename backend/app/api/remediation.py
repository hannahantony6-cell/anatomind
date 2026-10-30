from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.deps import get_current_user
from ..database import get_db
from ..models import User
from ..schemas.learning import QuizOut
from ..schemas.remediation import RemediationOut, RemediationStartRequest
from ..services import quizzes, remediation

router = APIRouter(prefix="/remediation", tags=["remediation"])


@router.post("/start", response_model=RemediationOut)
def start(body: RemediationStartRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return remediation.start(db, user, body.concept_id, body.include_practice_questions, body.regenerate)


@router.get("/{concept_id}", response_model=RemediationOut)
def get_state(concept_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return remediation.get(db, user, concept_id)


@router.post("/{concept_id}/retry", response_model=QuizOut, status_code=201)
def retry(concept_id: str, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    quiz = remediation.retry_quiz(db, user, concept_id)
    return quizzes.quiz_out(db, quiz)
