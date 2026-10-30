from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..core.deps import get_current_user
from ..database import get_db
from ..models import User
from ..schemas.learning import QuizOut
from ..schemas.quiz import QuizResultOut, SubmitRequest
from ..services import quizzes

router = APIRouter(prefix="/quizzes", tags=["quizzes"])


@router.get("/{quiz_id}", response_model=QuizOut)
def get_quiz(quiz_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return quizzes.quiz_out(db, quizzes.get_owned_quiz(db, user, quiz_id))   # never includes the answer key


@router.post("/{quiz_id}/submit", response_model=QuizResultOut)
def submit(quiz_id: int, body: SubmitRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return quizzes.submit_quiz(db, user, quiz_id, body.answers)


@router.get("/{quiz_id}/results", response_model=QuizResultOut)
def results(quiz_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return quizzes.get_results(db, user, quiz_id)
