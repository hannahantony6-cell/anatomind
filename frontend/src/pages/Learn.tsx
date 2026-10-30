import { ArrowLeft, ClipboardList, RefreshCw, Sparkles } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Breadcrumb } from '../components/Breadcrumb'
import { Disclaimer } from '../components/Disclaimer'
import { StudyNotes } from '../components/StudyNotes'
import { Alert, ErrorState, LoadingState, PageHeader } from '../components/ui'
import { useAsync } from '../hooks/useAsync'
import { api, errorMessage } from '../services/api'
import type { NotesResponse } from '../types'

const cacheKey = (id: string) => `anatomind-notes-${id}`

export default function Learn() {
  const { conceptId = '' } = useParams()
  const nav = useNavigate()
  const concept = useAsync(() => api.concept(conceptId), [conceptId])
  const [notes, setNotes] = useState<NotesResponse | null>(null)
  const [busy, setBusy] = useState<'notes' | 'quiz' | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {                 // restore notes generated earlier in this browser session
    setNotes(null); setError(null)
    try { const raw = sessionStorage.getItem(cacheKey(conceptId)); if (raw) setNotes(JSON.parse(raw)) } catch { /* ignore */ }
  }, [conceptId])

  const generate = async (regenerate: boolean) => {
    setBusy('notes'); setError(null)
    try {
      const n = await api.notes(conceptId, regenerate)
      setNotes(n)
      try { sessionStorage.setItem(cacheKey(conceptId), JSON.stringify(n)) } catch { /* quota */ }
    } catch (e) { setError(errorMessage(e)) } finally { setBusy(null) }
  }
  const startQuiz = async () => {
    setBusy('quiz'); setError(null)
    try { nav(`/quiz/${(await api.createQuiz(conceptId)).id}`) }
    catch (e) { setError(errorMessage(e)); setBusy(null) }
  }

  if (concept.loading) return <LoadingState />
  if (concept.error || !concept.data) return <ErrorState message={concept.error ?? 'Topic not found.'} />
  const c = concept.data

  return (
    <>
      <Breadcrumb concept={c} />
      <PageHeader title={c.title === 'Overview' ? `${c.section_title} (overview)` : c.title}
        subtitle={`Chapter ${c.chapter_number}: ${c.chapter_title} · Section ${c.section_number} ${c.section_title}`}
        actions={<>
          <Link to="/topics" className="btn-secondary"><ArrowLeft className="h-4 w-4" aria-hidden="true" />Back to Topics</Link>
          {!notes
            ? <button className="btn-primary" disabled={!c.available || busy !== null} onClick={() => generate(false)}><Sparkles className="h-4 w-4" aria-hidden="true" />Generate Notes</button>
            : <button className="btn-secondary" disabled={busy !== null} onClick={() => generate(true)}><RefreshCw className="h-4 w-4" aria-hidden="true" />Regenerate Notes</button>}
          <button className="btn-navy" disabled={!c.available || busy !== null} onClick={startQuiz}><ClipboardList className="h-4 w-4" aria-hidden="true" />Start Five-Question Quiz</button>
        </>} />

      {!c.available && <Alert kind="warn">The indexed textbook has too little material for this topic, so notes and quizzes are disabled.</Alert>}
      {error && <div className="mb-4"><Alert kind="error">{error}</Alert></div>}
      {busy === 'notes' && <LoadingState label="Retrieving textbook passages and writing your notes…" hint="The local model runs on your machine, so this can take a minute." />}
      {busy === 'quiz' && <LoadingState label="Building your five-question quiz…" hint="Questions are generated from the retrieved textbook passages and validated before you see them." />}
      {busy === null && notes && (
        <>
          <StudyNotes markdown={notes.notes_markdown} evidence={notes.evidence} />
          <p className="mt-4 text-xs text-navy-600">Generated {new Date(notes.generated_at).toLocaleString()} by {notes.model}.</p>
        </>
      )}
      {busy === null && !notes && c.available && !error && (
        <div className="card p-10 text-center text-sm text-navy-700">Press <strong>Generate Notes</strong> to build study notes from the textbook passages for this topic,
          or jump straight to the quiz.</div>
      )}
      <div className="mt-6"><Disclaimer /></div>
    </>
  )
}
