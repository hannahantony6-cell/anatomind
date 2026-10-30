export interface User { id: number; full_name: string; email: string; created_at: string }

export interface ConceptOut { id: string; title: string; ordinal: number; chunk_count: number; char_count: number; available: boolean }
export interface SectionOut { id: string; number: string; title: string; concepts: ConceptOut[] }
export interface ChapterOut { id: string; number: number; title: string; sections: SectionOut[] }
export interface UnitOut { id: string; number: number; title: string; chapters: ChapterOut[] }

export interface ConceptDetail {
  id: string; title: string; unit_id: string; unit_title: string; chapter_id: string; chapter_number: number
  chapter_title: string; section_id: string; section_number: string; section_title: string
  page_start: number | null; page_end: number | null; chunk_count: number; available: boolean
}

export interface EvidenceItem {
  label: string; chunk_id: string; score: number; section_title: string; concept_title: string
  pdf_pages: number[]; text: string
}
export interface NotesResponse {
  concept: ConceptDetail; notes_markdown: string; evidence: EvidenceItem[]; model: string
  generated_at: string; disclaimer: string
}

export interface QuizOption { id: 'A' | 'B' | 'C' | 'D'; text: string }
export interface QuizQuestion { id: string; question: string; options: QuizOption[]; concept_id: string; aspect: string | null }
export interface Quiz { id: number; concept: ConceptDetail; quiz_type: 'standard' | 'review' | 'remediation'; questions: QuizQuestion[]; submitted: boolean; created_at: string }

export interface SourceOut { chunk_id: string; unit_title: string; chapter_title: string; section_title: string; concept_id: string; pdf_pages: number[]; source: string; text: string }

export interface RemediationInfo { status: 'none' | 'active' | 'resolved' | 'exhausted'; attempts_used: number; max_attempts: number }
export interface ConceptOutcome {
  concept_id: string; concept_title: string; section_title: string; correct: number; total: number
  latest_performance: number; previous_mastery: number | null; mastery_score: number
  mastery_level: MasteryLevel; had_incorrect: boolean; action: 'celebrate' | 'reinforce' | 'remediate'
  message: string; remediation: RemediationInfo
  next_concept: { concept_id: string; title: string; section_title: string; chapter_title: string } | null
}
export interface QuestionResult {
  id: string; question: string; options: QuizOption[]; selected: string | null; correct: string; is_correct: boolean
  explanation: string; concept_id: string; concept_title: string; source_chunk_id: string | null; source_label: string | null
}
export interface QuizResult {
  attempt_id: number; quiz_id: number; quiz_type: 'standard' | 'review' | 'remediation'; concept: ConceptDetail
  correct_count: number; total_questions: number; score: number; submitted_at: string
  questions: QuestionResult[]; concept_outcomes: ConceptOutcome[]
}

export type MasteryLevel = 'good' | 'average' | 'weak'
export interface TopicRef { concept_id: string; concept_title: string; section_title: string; chapter_title: string; chapter_number: number }
export interface WeakConcept extends TopicRef { mastery_score: number; remediation_status: string }
export interface RecentTopic extends TopicRef { last_studied_at: string }
export interface Summary {
  full_name: string; topics_studied: number; quizzes_completed: number; average_score: number | null
  mastery: { good: number; average: number; weak: number; tracked: number; average_mastery: number | null }
  weak_concepts: WeakConcept[]; recent_topics: RecentTopic[]; continue_learning: RecentTopic | null
}
export interface TopicMastery extends TopicRef {
  mastery_score: number; mastery_level: MasteryLevel; attempts: number; previous_score: number | null
  latest_score: number; last_studied_at: string | null; needs_revision: boolean; remediation_status: string
  trend: { at: string; score: number }[]
}
export interface Attempt extends TopicRef {
  attempt_id: number; quiz_id: number; attempt_type: string; correct_count: number; total_questions: number
  score: number; created_at: string
}
export interface History { total: number; attempts: Attempt[] }

export interface Remediation {
  concept: ConceptDetail; status: 'active' | 'resolved' | 'exhausted'; attempts_used: number; max_attempts: number
  can_retry: boolean; mastery_score: number | null; mastery_level: MasteryLevel | null
  content_markdown: string | null; evidence: EvidenceItem[]; generated_at: string | null; message: string | null
}
