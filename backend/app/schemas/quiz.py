from datetime import datetime

from pydantic import BaseModel

from .learning import QuizOption
from .topics import ConceptDetail


class SubmitRequest(BaseModel):
    answers: dict[str, str]          # {"q1": "B", ...}


class RemediationInfo(BaseModel):
    status: str                      # none|active|resolved|exhausted
    attempts_used: int
    max_attempts: int


class ConceptOutcome(BaseModel):
    concept_id: str
    concept_title: str
    section_title: str
    correct: int
    total: int
    latest_performance: float
    previous_mastery: float | None
    mastery_score: float
    mastery_level: str
    had_incorrect: bool
    action: str                      # celebrate|reinforce|remediate
    message: str
    remediation: RemediationInfo
    next_concept: dict | None = None


class QuestionResult(BaseModel):
    id: str
    question: str
    options: list[QuizOption]
    selected: str | None
    correct: str
    is_correct: bool
    explanation: str
    concept_id: str
    concept_title: str
    source_chunk_id: str | None
    source_label: str | None


class QuizResultOut(BaseModel):
    attempt_id: int
    quiz_id: int
    quiz_type: str
    concept: ConceptDetail
    correct_count: int
    total_questions: int
    score: float
    submitted_at: datetime
    questions: list[QuestionResult]
    concept_outcomes: list[ConceptOutcome]
