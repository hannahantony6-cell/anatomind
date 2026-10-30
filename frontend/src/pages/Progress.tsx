import { useState } from 'react'
import { Link } from 'react-router-dom'
import { LEVEL_COLOR, MasteryBadge } from '../components/MasteryBadge'
import { MasteryBarChart, ScoreTrendChart } from '../components/ProgressCharts'
import { EmptyState, ErrorState, LoadingState, PageHeader } from '../components/ui'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'
import type { MasteryLevel } from '../types'

export default function Progress() {
  const topics = useAsync(() => api.progressTopics(), [])
  const hist = useAsync(() => api.history(100), [])
  const [filter, setFilter] = useState<MasteryLevel | 'all'>('all')

  if (topics.loading || hist.loading) return <LoadingState label="Loading your progress…" />
  if (topics.error || hist.error || !topics.data || !hist.data)
    return <ErrorState message={topics.error ?? hist.error ?? 'Could not load progress.'} onRetry={() => { topics.reload(); hist.reload() }} />
  const rows = topics.data.filter((t) => filter === 'all' || t.mastery_level === filter)

  return (
    <>
      <PageHeader title="My Progress" subtitle="Concept mastery is an exponential moving average of your quiz results (weight 0.6 on the latest quiz)." />
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="card p-5" aria-labelledby="trend-h"><h2 id="trend-h" className="mb-3 font-semibold">Quiz score over time</h2><ScoreTrendChart attempts={hist.data.attempts} /></section>
        <section className="card p-5" aria-labelledby="bar-h"><h2 id="bar-h" className="mb-3 font-semibold">Mastery by concept (lowest first)</h2><MasteryBarChart topics={topics.data} /></section>
      </div>
      <section className="card mt-6 p-5" aria-labelledby="tbl-h">
        <div className="mb-4 flex flex-wrap items-center justify-between gap-2">
          <h2 id="tbl-h" className="font-semibold">Topic mastery</h2>
          <div role="group" aria-label="Filter by mastery level" className="flex gap-1.5">
            {(['all', 'weak', 'average', 'good'] as const).map((f) => (
              <button key={f} onClick={() => setFilter(f)} aria-pressed={filter === f}
                className={`rounded-full border px-3 py-1 text-xs font-semibold capitalize ${filter === f ? 'border-navy-800 bg-navy-800 text-white' : 'border-navy-200 bg-white text-navy-700 hover:bg-navy-50'}`}>{f}</button>
            ))}
          </div>
        </div>
        {rows.length === 0 ? <EmptyState title={topics.data.length ? 'No concepts in this category' : 'No mastery data yet'} action={!topics.data.length ? <Link className="btn-primary" to="/topics">Start a topic</Link> : undefined} /> : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[640px] text-left text-sm">
              <thead className="text-xs uppercase text-navy-600"><tr><th className="py-2">Concept</th><th>Mastery</th><th>Previous → Latest</th><th>Quizzes</th><th>Last studied</th><th /></tr></thead>
              <tbody className="divide-y divide-navy-100">
                {rows.map((t) => (
                  <tr key={t.concept_id}>
                    <td className="py-3 pr-3"><p className="font-semibold text-navy-900">{t.concept_title === 'Overview' ? t.section_title : t.concept_title}</p><p className="text-xs text-navy-600">Ch {t.chapter_number} · {t.section_title}</p></td>
                    <td className="pr-3"><MasteryBadge level={t.mastery_level} score={t.mastery_score} /></td>
                    <td className="pr-3 tabular-nums" style={{ color: LEVEL_COLOR[t.mastery_level] }}>{t.previous_score === null ? '—' : `${Math.round(t.previous_score * 100)}%`} → {Math.round(t.latest_score * 100)}%</td>
                    <td className="pr-3">{t.attempts}</td>
                    <td className="pr-3 text-xs text-navy-600">{t.last_studied_at ? new Date(t.last_studied_at).toLocaleString() : '—'}</td>
                    <td className="text-right">{t.needs_revision && <Link className="text-xs font-semibold text-teal-700 hover:underline" to={t.mastery_level === 'weak' && t.remediation_status !== 'none' ? `/remediation/${t.concept_id}` : `/learn/${t.concept_id}`}>Revise</Link>}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  )
}
