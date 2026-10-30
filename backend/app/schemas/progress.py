from datetime import datetime

from pydantic import BaseModel


class MasteryOverview(BaseModel):
    good: int
    average: int
    weak: int
    tracked: int
    average_mastery: float | None


class TopicRef(BaseModel):
    concept_id: str
    concept_title: str
    section_title: str
    chapter_title: str
    chapter_number: int


class WeakConcept(TopicRef):
    mastery_score: float
    remediation_status: str


class RecentTopic(TopicRef):
    last_studied_at: datetime


class SummaryOut(BaseModel):
    full_name: str
    topics_studied: int
    quizzes_completed: int
    average_score: float | None
    mastery: MasteryOverview
    weak_concepts: list[WeakConcept]
    recent_topics: list[RecentTopic]
    continue_learning: RecentTopic | None


class TrendPoint(BaseModel):
    at: datetime
    score: float


class TopicMasteryOut(TopicRef):
    mastery_score: float
    mastery_level: str
    attempts: int
    previous_score: float | None
    latest_score: float
    last_studied_at: datetime | None
    needs_revision: bool
    remediation_status: str
    trend: list[TrendPoint]


class AttemptOut(TopicRef):
    attempt_id: int
    quiz_id: int
    attempt_type: str
    correct_count: int
    total_questions: int
    score: float
    created_at: datetime


class HistoryOut(BaseModel):
    total: int
    attempts: list[AttemptOut]
