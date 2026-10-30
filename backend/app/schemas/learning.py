from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

from .topics import ConceptDetail


class NotesRequest(BaseModel):
    concept_id: str = Field(min_length=1, max_length=40)
    regenerate: bool = False


class EvidenceItem(BaseModel):
    label: str                 # "E1" ... as used in [E1] markers inside the notes
    chunk_id: str
    score: float               # cosine similarity
    section_title: str
    concept_title: str
    pdf_pages: list[int]
    text: str


class NotesResponse(BaseModel):
    concept: ConceptDetail
    notes_markdown: str
    evidence: list[EvidenceItem]
    model: str
    generated_at: datetime
    disclaimer: str


class QuizRequest(BaseModel):
    concept_id: str = Field(min_length=1, max_length=40)
    quiz_type: Literal["standard", "review"] = "standard"
    force_new: bool = False


class QuizOption(BaseModel):
    id: Literal["A", "B", "C", "D"]
    text: str


class QuizQuestionOut(BaseModel):
    id: str
    question: str
    options: list[QuizOption]
    concept_id: str
    aspect: str | None = None


class QuizOut(BaseModel):
    id: int
    concept: ConceptDetail
    quiz_type: str
    questions: list[QuizQuestionOut]
    submitted: bool
    created_at: datetime


class SourceOut(BaseModel):
    chunk_id: str
    unit_title: str
    chapter_title: str
    section_title: str
    concept_id: str
    pdf_pages: list[int]
    source: str
    text: str
