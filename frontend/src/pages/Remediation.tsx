import { ArrowLeft, GraduationCap, RotateCcw } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Breadcrumb } from '../components/Breadcrumb'
import { MasteryBadge } from '../components/MasteryBadge'
import { RemedialContent } from '../components/RemedialContent'
import { Alert, ErrorState, LoadingState, PageHeader } from '../components/ui'
import { useAsync } from '../hooks/useAsync'
import { api, errorMessage } from '../services/api'

export default function Remediation() {
  const { conceptId = '' } = useParams()
  const nav = useNavigate()
  const { data: r, error, loading, reload } = useAsync(() => api.remediation(conceptId), [conceptId])
  const [busy, setBusy] = useState(false)
  const [err, setErr] = useState<string | null>(null)

  if (loading) return <LoadingState label="Loading your revision page…" />
  if (error || !r) return <ErrorState message={error ?? 'Revision not found.'} onRetry={reload} />

  const retry = async () => {
    setBusy(true); setErr(null)
    try { nav(`/quiz/${(await api.retryRemediation(conceptId)).id}`) }
    catch (e) { setErr(errorMessage(e)); setBusy(false) }
  }
  const regenerate = async () => {
    setBusy(true); setErr(null)
    try { await api.startRemediation(conceptId, true, true); reload() } catch (e) { setErr(errorMessage(e)) } finally { setBusy(false) }
  }
  const remaining = r.max_attempts - r.attempts_used

  return (
    <>
      <Breadcrumb concept={r.concept} />
      <PageHeader title={`Revision: ${r.concept.title === 'Overview' ? r.concept.section_title : r.concept.title}`}
        subtitle={<span className="flex flex-wrap items-center gap-2">{r.mastery_level && <MasteryBadge level={r.mastery_level} score={r.mastery_score ?? undefined} />}
          <span>Remediation quizzes used: {r.attempts_used} of {r.max_attempts}</span></span>}
        actions={<>
          <Link className="btn-secondary" to={`/learn/${conceptId}`}><ArrowLeft className="h-4 w-4" aria-hidden="true" />Original notes</Link>
          <button className="btn-primary" disabled={!r.can_retry || busy} onClick={retry}><RotateCcw className="h-4 w-4" aria-hidden="true" />{busy ? 'Working…' : 'Retry Focused Quiz'}</button>
        </>} />
      {err && <div className="mb-4"><Alert kind="error">{err}</Alert></div>}
      {r.status === 'exhausted' && (
        <div className="mb-4 flex items-start gap-3 rounded-2xl border border-amber-200 bg-amber-50 p-5 text-amber-900">
          <GraduationCap className="mt-0.5 h-6 w-6 shrink-0" aria-hidden="true" /><p className="text-sm">{r.message}</p>
        </div>
      )}
      {r.status === 'resolved' && r.message && <div className="mb-4"><Alert kind="success">{r.message}</Alert></div>}
      {r.status === 'active' && <p className="mb-4 text-sm text-navy-700">{remaining} remediation {remaining === 1 ? 'quiz' : 'quizzes'} remaining. Read the simplified explanation below, then retry the focused quiz.</p>}
      {r.content_markdown
        ? <RemedialContent markdown={r.content_markdown} evidence={r.evidence} />
        : <Alert kind="info">No revision content has been generated yet.</Alert>}
      {r.status !== 'resolved' && <button className="btn-ghost mt-4" disabled={busy} onClick={regenerate}>Regenerate this explanation</button>}
    </>
  )
}
