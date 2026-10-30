import { CheckCircle2, ChevronDown, Home, RotateCcw, XCircle } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { MasteryBadge } from '../components/MasteryBadge'
import { ScoreSummary } from '../components/ScoreSummary'
import { Alert, ErrorState, LoadingState } from '../components/ui'
import { useAsync } from '../hooks/useAsync'
import { api, errorCode, errorMessage } from '../services/api'
import type { ConceptOutcome, QuestionResult, QuizResult, SourceOut } from '../types'

function SourceToggle({ chunkId, label }: { chunkId: string; label: string | null }) {
  const [src, setSrc] = useState<SourceOut | null>(null)
  const [err, setErr] = useState<string | null>(null)
  const load = (open: boolean) => { if (open && !src) api.sources([chunkId]).then((r) => setSrc(r[0] ?? null)).catch((e) => setErr(errorMessage(e))) }
  return (
    <details onToggle={(e) => load((e.target as HTMLDetailsElement).open)} className="mt-2 rounded-lg border border-navy-100 text-xs">
      <summary className="cursor-pointer px-3 py-2 font-medium text-navy-700">Textbook source {label ? `(${label})` : ''}</summary>
      <div className="border-t border-navy-100 bg-sky-25 px-3 py-2 text-navy-800">
        {err ? err : !src ? 'Loading…' : (<>
          <p className="mb-1 font-semibold">{src.section_title} · PDF p. {src.pdf_pages.join('–')}</p>
          <p className="whitespace-pre-line">{src.text}</p>
          <p className="mt-1 font-mono text-[10px] text-navy-600/60">{src.chunk_id}</p></>)}
      </div>
    </details>
  )
}

function QuestionReview({ q, n }: { q: QuestionResult; n: number }) {
  return (
    <li className="card p-5">
      <div className="mb-2 flex items-start gap-2">
        {q.is_correct ? <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-teal-600" aria-label="Correct" /> : <XCircle className="mt-0.5 h-5 w-5 shrink-0 text-red-600" aria-label="Incorrect" />}
        <p className="font-semibold text-navy-900">{n}. {q.question}</p>
      </div>
      <ul className="space-y-1.5 text-sm">
        {q.options.map((o) => {
          const right = o.id === q.correct, mine = o.id === q.selected
          return (
            <li key={o.id} className={`rounded-lg border px-3 py-2 ${right ? 'border-teal-500 bg-teal-50' : mine ? 'border-red-300 bg-red-50' : 'border-navy-100'}`}>
              <span className="font-bold">{o.id}.</span> {o.text}
              {right && <span className="ml-2 text-xs font-semibold text-teal-700">Correct answer</span>}
              {mine && !right && <span className="ml-2 text-xs font-semibold text-red-700">Your answer</span>}
            </li>
          )
        })}
      </ul>
      <p className="mt-3 text-sm text-navy-800"><span className="font-semibold">Explanation: </span>{q.explanation}</p>
      {q.source_chunk_id && <SourceToggle chunkId={q.source_chunk_id} label={q.source_label} />}
    </li>
  )
}

function Outcome({ o, result }: { o: ConceptOutcome; result: QuizResult }) {
  const nav = useNavigate()
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  const run = async (fn: () => Promise<string>) => {
    setBusy(true); setErr(null)
    try { nav(await fn()) } catch (e) { setErr(errorMessage(e)); setBusy(false) }
  }
  const title = o.concept_title === 'Overview' ? o.section_title : o.concept_title
  const exhausted = o.remediation.status === 'exhausted'
  return (
    <div className="card p-5">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h3 className="font-semibold text-navy-900">{title}</h3>
        <MasteryBadge level={o.mastery_level} score={o.mastery_score} />
      </div>
      <p className="mt-1 text-xs text-navy-600">
        This quiz: {o.correct}/{o.total} · previous mastery {o.previous_mastery === null ? 'none (first attempt)' : `${Math.round(o.previous_mastery * 100)}%`} → now {Math.round(o.mastery_score * 100)}%
      </p>
      <p className="mt-3 text-sm text-navy-800">{o.message}</p>
      {exhausted && <div className="mt-3"><Alert kind="warn">You have used all {o.remediation.max_attempts} remediation quizzes for this concept. Please consult your teacher or attend office hours.</Alert></div>}
      {err && <div className="mt-3"><Alert kind="error">{err}</Alert></div>}
      <div className="mt-4 flex flex-wrap gap-2">
        {o.action === 'remediate' && (
          <button className="btn-primary" disabled={busy} onClick={() => run(async () => { await api.startRemediation(o.concept_id); return `/remediation/${o.concept_id}` })}>
            {busy ? 'Preparing…' : exhausted ? 'View revision & guidance' : 'Review Weak Concepts'}
          </button>
        )}
        {o.action === 'reinforce' && (<>
          <Link className="btn-primary" to={`/learn/${o.concept_id}`}>Short revision</Link>
          <button className="btn-secondary" disabled={busy} onClick={() => run(async () => `/quiz/${(await api.createQuiz(o.concept_id, 'review', true)).id}`)}>{busy ? 'Building…' : 'Take a review quiz'}</button>
        </>)}
        {o.action === 'celebrate' && o.next_concept && (
          <Link className="btn-primary" to={`/learn/${o.next_concept.concept_id}`}>Next: {o.next_concept.title === 'Overview' ? o.next_concept.section_title : o.next_concept.title}</Link>
        )}
        {o.action === 'celebrate' && <Link className="btn-secondary" to={`/learn/${o.concept_id}`}>Revisit this topic</Link>}
      </div>
      {result.quiz_type === 'remediation' && o.remediation.status === 'active' && (
        <p className="mt-3 text-xs text-navy-600">Remediation quizzes used: {o.remediation.attempts_used} of {o.remediation.max_attempts}</p>
      )}
    </div>
  )
}

export default function Results() {
  const quizId = Number(useParams().quizId)
  const nav = useNavigate()
  const { data: r, error, loading, reload } = useAsync(() => api.results(quizId), [quizId])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)
  if (loading) return <LoadingState label="Loading results…" />
  if (error || !r) return <ErrorState message={error ?? 'Results not found.'} onRetry={reload} />

  const retry = async () => {
    setBusy(true); setErr(null)
    try {
      const quiz = r.quiz_type === 'remediation' ? await api.retryRemediation(r.concept.id) : await api.createQuiz(r.concept.id, r.quiz_type === 'review' ? 'review' : 'standard', true)
      nav(`/quiz/${quiz.id}`)
    } catch (e) {
      setErr(errorCode(e) === 'remediation_limit_reached' ? 'No more remediation quizzes are available for this concept. Please consult your teacher.' : errorMessage(e))
      setBusy(false)
    }
  }
  const weakOutcomes = r.concept_outcomes.filter((o) => o.had_incorrect)

  return (
    <div className="mx-auto max-w-3xl space-y-6">
      <div>
        <p className="text-xs font-semibold uppercase tracking-wide text-navy-600">Quiz results</p>
        <h1 className="text-2xl font-bold text-navy-900">{r.concept.title === 'Overview' ? r.concept.section_title : r.concept.title}</h1>
      </div>
      <ScoreSummary result={r} />
      <section aria-labelledby="co-h" className="space-y-3">
        <h2 id="co-h" className="text-lg font-semibold text-navy-900">Concept mastery</h2>
        {weakOutcomes.length === 0 && <Alert kind="success">Every question was answered correctly. Excellent!</Alert>}
        {r.concept_outcomes.map((o) => <Outcome key={o.concept_id} o={o} result={r} />)}
      </section>
      <section aria-labelledby="rv-h">
        <h2 id="rv-h" className="mb-3 flex items-center gap-2 text-lg font-semibold text-navy-900">Answer review <ChevronDown className="h-4 w-4" aria-hidden="true" /></h2>
        <ol className="space-y-4">{r.questions.map((q, i) => <QuestionReview key={q.id} q={q} n={i + 1} />)}</ol>
      </section>
      {err && <Alert kind="error">{err}</Alert>}
      <div className="flex flex-wrap gap-2 pb-6">
        <button className="btn-navy" disabled={busy} onClick={retry}><RotateCcw className="h-4 w-4" aria-hidden="true" />{busy ? 'Building quiz…' : 'Retry Quiz'}</button>
        <Link className="btn-secondary" to="/dashboard"><Home className="h-4 w-4" aria-hidden="true" />Return to Dashboard</Link>
      </div>
    </div>
  )
}
