from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import (
    JSON, CheckConstraint, DateTime, Float, ForeignKey, Index, Integer, LargeBinary, String,
    Text, UniqueConstraint, Boolean, TypeDecorator,
)
from sqlalchemy.orm import Mapped, mapped_column

from ..database import Base


class UTCDateTime(TypeDecorator):
    """Stores naive UTC in SQLite, always returns timezone-aware UTC."""
    impl = DateTime
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)
        return value

    def process_result_value(self, value, dialect):
        return value.replace(tzinfo=timezone.utc) if value is not None else None


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class RevokedToken(Base):
    """JWT ids invalidated by logout."""
    __tablename__ = "revoked_tokens"
    jti: Mapped[str] = mapped_column(String(64), primary_key=True)
    expires_at: Mapped[datetime] = mapped_column(UTCDateTime, index=True)


class Concept(Base):
    """One row per learnable topic. Hierarchy: Unit -> Chapter -> Section -> Concept."""
    __tablename__ = "concepts"
    id: Mapped[str] = mapped_column(String(40), primary_key=True)          # e.g. ch1-s5-c2
    ordinal: Mapped[int] = mapped_column(Integer, index=True)             # global book order
    unit_id: Mapped[str] = mapped_column(String(20), index=True)
    unit_number: Mapped[int] = mapped_column(Integer)
    unit_title: Mapped[str] = mapped_column(String(200))
    chapter_id: Mapped[str] = mapped_column(String(20), index=True)
    chapter_number: Mapped[int] = mapped_column(Integer)
    chapter_title: Mapped[str] = mapped_column(String(200))
    section_id: Mapped[str] = mapped_column(String(30), index=True)
    section_number: Mapped[str] = mapped_column(String(10))
    section_title: Mapped[str] = mapped_column(String(300))
    concept_title: Mapped[str] = mapped_column(String(300))
    page_start: Mapped[int | None] = mapped_column(Integer, nullable=True)
    page_end: Mapped[int | None] = mapped_column(Integer, nullable=True)
    source_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)


class TextbookChunk(Base):
    __tablename__ = "textbook_chunks"
    id: Mapped[str] = mapped_column(String(60), primary_key=True)          # <concept_id>#<index>
    unit_id: Mapped[str] = mapped_column(String(20))
    unit_title: Mapped[str] = mapped_column(String(200))
    chapter_id: Mapped[str] = mapped_column(String(20), index=True)
    chapter_title: Mapped[str] = mapped_column(String(200))
    section_id: Mapped[str] = mapped_column(String(30), index=True)
    section_title: Mapped[str] = mapped_column(String(300))
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id", ondelete="CASCADE"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    content_hash: Mapped[str] = mapped_column(String(64))
    embedding: Mapped[bytes] = mapped_column(LargeBinary)                  # 384 x float32
    source_metadata: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    __table_args__ = (UniqueConstraint("concept_id", "chunk_index", name="uq_chunk_concept_index"),)


class Quiz(Base):
    __tablename__ = "quizzes"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), index=True)
    quiz_type: Mapped[str] = mapped_column(String(20), default="standard")   # standard|review|remediation
    questions_json: Mapped[list] = mapped_column(JSON)        # what the student sees (no answers)
    answer_key_json: Mapped[dict] = mapped_column(JSON)       # server-side only until submission
    source_references_json: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    __table_args__ = (CheckConstraint("quiz_type IN ('standard','review','remediation')", name="ck_quiz_type"),)


class QuizAttempt(Base):
    __tablename__ = "quiz_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    quiz_id: Mapped[int] = mapped_column(ForeignKey("quizzes.id", ondelete="CASCADE"), unique=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), index=True)
    attempt_type: Mapped[str] = mapped_column(String(20))
    selected_answers_json: Mapped[dict] = mapped_column(JSON)
    correct_count: Mapped[int] = mapped_column(Integer)
    total_questions: Mapped[int] = mapped_column(Integer)
    score: Mapped[float] = mapped_column(Float)               # percentage 0-100
    concept_results_json: Mapped[list] = mapped_column(JSON)  # per-concept performance + mastery snapshot
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, index=True)
    __table_args__ = (
        CheckConstraint("correct_count >= 0 AND correct_count <= total_questions", name="ck_attempt_counts"),
        CheckConstraint("score >= 0 AND score <= 100", name="ck_attempt_score"),
    )


class ConceptMastery(Base):
    __tablename__ = "concept_mastery"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"))
    mastery_score: Mapped[float] = mapped_column(Float)
    mastery_level: Mapped[str] = mapped_column(String(10))   # good|average|weak
    attempts_count: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)
    __table_args__ = (
        UniqueConstraint("user_id", "concept_id", name="uq_mastery_user_concept"),
        CheckConstraint("mastery_score >= 0 AND mastery_score <= 1", name="ck_mastery_range"),
        CheckConstraint("mastery_level IN ('good','average','weak')", name="ck_mastery_level"),
    )


class MasteryHistory(Base):
    __tablename__ = "mastery_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"))
    attempt_id: Mapped[int] = mapped_column(ForeignKey("quiz_attempts.id", ondelete="CASCADE"))
    latest_performance: Mapped[float] = mapped_column(Float)
    previous_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    new_score: Mapped[float] = mapped_column(Float)
    mastery_level: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    __table_args__ = (Index("ix_mastery_hist_user_concept", "user_id", "concept_id", "created_at"),)


class RemediationAttempt(Base):
    __tablename__ = "remediation_attempts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"))
    attempt_count: Mapped[int] = mapped_column(Integer, default=0)       # FAILED remediation quizzes in this sequence
    last_score: Mapped[float | None] = mapped_column(Float, nullable=True)  # last mastery score seen
    remediation_status: Mapped[str] = mapped_column(String(12), default="active")  # active|resolved|exhausted
    content_json: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    content_generated_at: Mapped[datetime | None] = mapped_column(UTCDateTime, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow, onupdate=utcnow)
    __table_args__ = (
        UniqueConstraint("user_id", "concept_id", name="uq_remediation_user_concept"),
        CheckConstraint("remediation_status IN ('active','resolved','exhausted')", name="ck_remediation_status"),
    )


class StudyEvent(Base):
    """Records that a student opened notes / took a quiz. Never used to infer mastery."""
    __tablename__ = "study_events"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"))
    event_type: Mapped[str] = mapped_column(String(10))   # notes|quiz|remedial
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
    __table_args__ = (Index("ix_study_user_time", "user_id", "created_at"),)


class LLMTelemetry(Base):
    """Operational metrics only: no prompts, no student data, no tokens."""
    __tablename__ = "llm_telemetry"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    task_type: Mapped[str] = mapped_column(String(30))
    model: Mapped[str] = mapped_column(String(60))
    latency_ms: Mapped[int] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean)
    error_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    validation_failures: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(UTCDateTime, default=utcnow)
