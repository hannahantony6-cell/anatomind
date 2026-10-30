import { BookOpen, ClipboardCheck, Clock, Gauge, Library, TrendingUp } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { EmptyState, ErrorState, LoadingState, PageHeader } from '../components/ui'
import { useAsync } from '../hooks/useAsync'
import { api, errorMessage } from '../services/api'

function Stat({ Icon, label, value }: { Icon: typeof Gauge; label: string; value: string | number }) {
  return (
    <div className="card flex items-center gap-4 p-5">
      <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-teal-50 text-teal-600"><Icon className="h-5 w-5" aria-hidden="true" /></span>
      <div><p className="text-2xl font-bold text-navy-900">{value}</p><p className="text-xs text-navy-600">{label}</p></div>
    </div>
  )
}

export default function Dashboard() {
  const { data: s, error, loading, reload } = useAsync(() => api.summary(), [])
  const nav = useNavigate()
  const [actionError, setActionError] = useState<string | null>(null)
  const [busyId, setBusyId] = useState<string | null>(null)

  if (loading) return <LoadingState label="Loading your dashboard…" />
  if (error || !s) return <ErrorState message={error ?? 'Could not load dashboard.'} onRetry={reload} />

  const revise = async (id: string) => {
    setBusyId(id); setActionError(null)
    try { await api.startRemediation(id); nav(`/remediation/${id}`) }
    catch (e) { setActionError(errorMessage(e)); setBusyId(null) }
  }
  const m = s.mastery
  const seg = (n: number) => (m.tracked ? (n / m.tracked) * 100 : 0)

  return (
    <>
      <PageHeader title={`Hello, ${s.full_name.split(' ')[0]} 👋`} subtitle="Here is where your learning stands."
        actions={<>
          {s.continue_learning && <Link className="btn-primary" to={`/learn/${s.continue_learning.concept_id}`}>Continue Learning</Link>}
          <Link className="btn-secondary" to="/topics"><Library className="h-4 w-4" aria-hidden="true" />Browse Textbook Topics</Link>
          <Link className="btn-secondary" to="/progress"><TrendingUp className="h-4 w-4" aria-hidden="true" />Learning Progress</Link>
        </>} />
      {actionError && <p role="alert" className="mb-4 rounded-xl bg-red-50 p-3 text-sm text-red-800">{actionError}</p>}

      <div className="grid gap-4 sm:grid-cols-3">
        <Stat Icon={BookOpen} label="Topics studied" value={s.topics_studied} />
        <Stat Icon={ClipboardCheck} label="Quizzes completed" value={s.quizzes_completed} />
        <Stat Icon={Gauge} label="Average quiz score" value={s.average_score === null ? '—' : `${s.average_score}%`} />
      </div>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <section className="card p-6" aria-labelledby="mastery-h">
          <h2 id="mastery-h" className="mb-4 font-semibold text-navy-900">Overall concept mastery</h2>
          {m.tracked === 0 ? (
            <EmptyState title="No mastery data yet">Finish a quiz and Anatomind will start tracking each concept.</EmptyState>
          ) : (
            <>
              <div className="flex h-3 overflow-hidden rounded-full bg-navy-100" role="img" aria-label={`${m.good} good, ${m.average} average, ${m.weak} weak`}>
                <div className="bg-teal-500" style={{ width: `${seg(m.good)}%` }} />
                <div className="bg-amber-500" style={{ width: `${seg(m.average)}%` }} />
                <div className="bg-red-500" style={{ width: `${seg(m.weak)}%` }} />
              </div>
              <dl className="mt-4 grid grid-cols-3 gap-2 text-center text-sm">
                <div><dt className="text-teal-700">Good</dt><dd className="text-xl font-bold">{m.good}</dd></div>
                <div><dt className="text-amber-700">Average</dt><dd className="text-xl font-bold">{m.average}</dd></div>
                <div><dt className="text-red-700">Weak</dt><dd className="text-xl font-bold">{m.weak}</dd></div>
              </dl>
              {m.average_mastery !== null && <p className="mt-3 text-center text-xs text-navy-600">Average mastery across {m.tracked} concepts: {Math.round(m.average_mastery * 100)}%</p>}
            </>
          )}
        </section>

        <section className="card p-6" aria-labelledby="weak-h">
          <h2 id="weak-h" className="mb-4 font-semibold text-navy-900">Weak concepts needing revision</h2>
          {s.weak_concepts.length === 0 ? <EmptyState title="Nothing flagged">Concepts scoring below 50% mastery will appear here.</EmptyState> : (
            <ul className="divide-y divide-navy-100">
              {s.weak_concepts.map((w) => (
                <li key={w.concept_id} className="flex items-center justify-between gap-3 py-3">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-semibold text-navy-900">{w.concept_title === 'Overview' ? w.section_title : w.concept_title}</p>
                    <p className="truncate text-xs text-navy-600">Ch {w.chapter_number} · {w.section_title} · mastery {Math.round(w.mastery_score * 100)}%</p>
                  </div>
                  {w.remediation_status === 'exhausted'
                    ? <Link className="btn-secondary shrink-0" to={`/remediation/${w.concept_id}`}>See guidance</Link>
                    : <button className="btn-primary shrink-0" disabled={busyId === w.concept_id} onClick={() => revise(w.concept_id)}>{busyId === w.concept_id ? 'Preparing…' : 'Revise'}</button>}
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      <section className="card mt-6 p-6" aria-labelledby="recent-h">
        <h2 id="recent-h" className="mb-4 font-semibold text-navy-900">Recently studied topics</h2>
        {s.recent_topics.length === 0 ? <EmptyState title="You haven’t studied anything yet" action={<Link className="btn-primary" to="/topics">Pick your first topic</Link>} /> : (
          <ul className="divide-y divide-navy-100">
            {s.recent_topics.map((t) => (
              <li key={t.concept_id}>
                <Link to={`/learn/${t.concept_id}`} className="flex items-center justify-between gap-3 py-3 hover:bg-sky-25">
                  <span className="min-w-0"><span className="block truncate text-sm font-semibold text-navy-900">{t.concept_title === 'Overview' ? t.section_title : t.concept_title}</span>
                    <span className="block truncate text-xs text-navy-600">Ch {t.chapter_number}: {t.chapter_title} · {t.section_title}</span></span>
                  <span className="flex shrink-0 items-center gap-1 text-xs text-navy-600"><Clock className="h-3.5 w-3.5" aria-hidden="true" />{new Date(t.last_studied_at).toLocaleDateString()}</span>
                </Link>
              </li>
            ))}
          </ul>
        )}
      </section>
    </>
  )
}
