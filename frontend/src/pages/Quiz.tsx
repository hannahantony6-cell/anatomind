import { ArrowLeft, ArrowRight, Send } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { QuizQuestionCard } from '../components/QuizQuestionCard'
import { Alert, ErrorState, LoadingState, ProgressBar } from '../components/ui'
import { useAsync } from '../hooks/useAsync'
import { api, errorMessage } from '../services/api'

export default function Quiz() {
  const quizId = Number(useParams().quizId)
  const nav = useNavigate()
  const { data: quiz, error, loading, reload } = useAsync(() => api.quiz(quizId), [quizId])
  const storeKey = `anatomind-quiz-${quizId}`
  const [answers, setAnswers] = useState<Record<string, string>>(() => {
    try { return JSON.parse(sessionStorage.getItem(storeKey) ?? '{}') } catch { return {} }
  })
  const [idx, setIdx] = useState(0)
  const [submitting, setSubmitting] = useState(false)
  const [submitErr, setSubmitErr] = useState<string | null>(null)
  const locked = useRef(false)          // blocks double-submits even before React re-renders

  useEffect(() => { try { sessionStorage.setItem(storeKey, JSON.stringify(answers)) } catch { /* ignore */ } }, [answers, storeKey])

  if (loading) return <LoadingState label="Loading quiz…" />
  if (error || !quiz) return <ErrorState message={error ?? 'Quiz not found.'} onRetry={reload} />
  if (quiz.submitted) return <Navigate to={`/results/${quiz.id}`} replace />

  const total = quiz.questions.length
  const q = quiz.questions[idx]
  const answered = quiz.questions.filter((x) => answers[x.id]).length
  const last = idx === total - 1
  const unanswered = quiz.questions.map((x, i) => (answers[x.id] ? null : i + 1)).filter(Boolean)

  const submit = async () => {
    if (locked.current) return
    if (unanswered.length) { setSubmitErr(`Please answer every question first. Unanswered: ${unanswered.join(', ')}.`); return }
    locked.current = true; setSubmitting(true); setSubmitErr(null)
    try {
      await api.submitQuiz(quiz.id, answers)
      sessionStorage.removeItem(storeKey)
      nav(`/results/${quiz.id}`, { replace: true })
    } catch (e) { setSubmitErr(errorMessage(e)); locked.current = false; setSubmitting(false) }
  }

  const title = quiz.concept.title === 'Overview' ? quiz.concept.section_title : quiz.concept.title
  return (
    <div className="mx-auto max-w-2xl">
      <p className="text-xs font-semibold uppercase tracking-wide text-navy-600">
        {quiz.quiz_type === 'remediation' ? 'Remediation quiz' : quiz.quiz_type === 'review' ? 'Review quiz' : 'Quiz'}
      </p>
      <h1 className="mb-4 text-2xl font-bold text-navy-900">{title}</h1>
      <div className="mb-5">
        <div className="mb-1 flex justify-between text-xs text-navy-600"><span>Question {idx + 1} of {total}</span><span>{answered} answered</span></div>
        <ProgressBar value={(answered / total) * 100} label="Quiz progress" />
      </div>
      <QuizQuestionCard question={q} index={idx} total={total} selected={answers[q.id]} onSelect={(o) => { setSubmitErr(null); setAnswers((a) => ({ ...a, [q.id]: o })) }} />
      {submitErr && <div className="mt-4"><Alert kind="error">{submitErr}</Alert></div>}
      <div className="mt-5 flex items-center justify-between">
        <button className="btn-secondary" disabled={idx === 0 || submitting} onClick={() => setIdx((i) => i - 1)}><ArrowLeft className="h-4 w-4" aria-hidden="true" />Previous</button>
        {last
          ? <button className="btn-primary" disabled={submitting} onClick={submit}><Send className="h-4 w-4" aria-hidden="true" />{submitting ? 'Submitting…' : 'Submit Quiz'}</button>
          : <button className="btn-navy" onClick={() => setIdx((i) => i + 1)}>Next<ArrowRight className="h-4 w-4" aria-hidden="true" /></button>}
      </div>
      <div className="mt-6 flex justify-center gap-2" aria-label="Jump to question">
        {quiz.questions.map((x, i) => (
          <button key={x.id} onClick={() => setIdx(i)} aria-label={`Go to question ${i + 1}${answers[x.id] ? ' (answered)' : ''}`} aria-current={i === idx}
            className={`h-8 w-8 rounded-full text-xs font-semibold ${i === idx ? 'bg-navy-800 text-white' : answers[x.id] ? 'bg-teal-100 text-teal-700' : 'bg-navy-100 text-navy-700'}`}>{i + 1}</button>
        ))}
      </div>
    </div>
  )
}
