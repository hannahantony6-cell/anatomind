from datetime import datetime

from pydantic import BaseModel, Field

from .topics import ConceptDetail


class RemediationStartRequest(BaseModel):
    concept_id: str = Field(min_length=1, max_length=40)
    include_practice_questions: bool = False
    regenerate: bool = False


class RemediationOut(BaseModel):
    concept: ConceptDetail
    status: str                       # active|resolved|exhausted
    attempts_used: int
    max_attempts: int
    can_retry: bool
    mastery_score: float | None
    mastery_level: str | None
    content_markdown: str | None
    evidence: list[dict]
    generated_at: datetime | None
    message: str | None
