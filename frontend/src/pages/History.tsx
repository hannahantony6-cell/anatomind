import { Link } from 'react-router-dom'
import { EmptyState, ErrorState, LoadingState, PageHeader } from '../components/ui'
import { useAsync } from '../hooks/useAsync'
import { api } from '../services/api'

export default function HistoryPage() {
  const { data, error, loading, reload } = useAsync(() => api.history(200), [])
  if (loading) return <LoadingState label="Loading quiz history…" />
  if (error || !data) return <ErrorState message={error ?? 'Could not load history.'} onRetry={reload} />
  return (
    <>
      <PageHeader title="Quiz History" subtitle={`${data.total} quiz ${data.total === 1 ? 'attempt' : 'attempts'} recorded`} />
      {data.attempts.length === 0 ? <EmptyState title="No quizzes yet" action={<Link className="btn-primary" to="/topics">Browse topics</Link>} /> : (
        <div className="card overflow-x-auto">
          <table className="w-full min-w-[600px] text-left text-sm">
            <thead className="bg-sky-50 text-xs uppercase text-navy-600"><tr><th className="px-4 py-3">Date</th><th>Topic</th><th>Type</th><th>Score</th><th /></tr></thead>
            <tbody className="divide-y divide-navy-100">
              {data.attempts.map((a) => (
                <tr key={a.attempt_id}>
                  <td className="px-4 py-3 text-xs text-navy-600">{new Date(a.created_at).toLocaleString()}</td>
                  <td><p className="font-semibold text-navy-900">{a.concept_title === 'Overview' ? a.section_title : a.concept_title}</p><p className="text-xs text-navy-600">Ch {a.chapter_number} · {a.section_title}</p></td>
                  <td className="capitalize">{a.attempt_type}</td>
                  <td className="font-semibold tabular-nums">{a.correct_count}/{a.total_questions} <span className="font-normal text-navy-600">({Math.round(a.score)}%)</span></td>
                  <td className="pr-4 text-right"><Link className="text-xs font-semibold text-teal-700 hover:underline" to={`/results/${a.quiz_id}`}>View</Link></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  )
}
