import { ArrowRight, Search } from 'lucide-react'
import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Breadcrumb } from '../components/Breadcrumb'
import { TopicTree } from '../components/TopicTree'
import { Alert, EmptyState, ErrorState, LoadingState, PageHeader } from '../components/ui'
import { useAsync } from '../hooks/useAsync'
import { api, errorMessage } from '../services/api'
import type { ConceptDetail } from '../types'

export default function Topics() {
  const nav = useNavigate()
  const tree = useAsync(() => api.tree(), [])
  const [q, setQ] = useState('')
  const [results, setResults] = useState<ConceptDetail[] | null>(null)
  const [searchErr, setSearchErr] = useState<string | null>(null)
  const [selected, setSelected] = useState<ConceptDetail | null>(null)

  useEffect(() => {                       // debounced server-side search
    const term = q.trim()
    if (term.length < 2) { setResults(null); setSearchErr(null); return }
    const t = setTimeout(() => {
      api.search(term).then((r) => { setResults(r); setSearchErr(null) }).catch((e) => setSearchErr(errorMessage(e)))
    }, 300)
    return () => clearTimeout(t)
  }, [q])

  if (tree.loading) return <LoadingState label="Loading textbook syllabus…" />
  if (tree.error || !tree.data) return <ErrorState message={tree.error ?? 'Could not load topics.'} onRetry={tree.reload} />
  if (tree.data.length === 0) return (
    <EmptyState title="No textbook content has been indexed yet">
      Run <code className="rounded bg-navy-100 px-1">python scripts/seed_from_pdf.py</code> in the backend folder (see the README), then refresh.
    </EmptyState>
  )

  return (
    <>
      <PageHeader title="Textbook Topics" subtitle="Unit → Chapter → Section → Concept, exactly as indexed from the textbook." />
      <div className="grid gap-6 lg:grid-cols-[1fr_340px]">
        <div className="card p-4">
          <div className="relative mb-4">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-navy-600" aria-hidden="true" />
            <input aria-label="Search chapters, sections or concepts" className="input pl-9" placeholder="Search a chapter, section or concept (e.g. homeostasis)"
              value={q} onChange={(e) => setQ(e.target.value)} />
          </div>
          {searchErr && <Alert kind="error">{searchErr}</Alert>}
          {results !== null ? (
            results.length === 0 ? <EmptyState title="No matches in the textbook index" /> : (
              <ul className="divide-y divide-navy-100" aria-label="Search results">
                {results.map((c) => (
                  <li key={c.id}>
                    <button onClick={() => setSelected(c)} className={`w-full px-2 py-3 text-left hover:bg-sky-50 ${selected?.id === c.id ? 'bg-teal-50' : ''}`}>
                      <span className="block text-sm font-semibold text-navy-900">{c.title === 'Overview' ? c.section_title : c.title}</span>
                      <span className="block text-xs text-navy-600">Ch {c.chapter_number}: {c.chapter_title} · {c.section_number} {c.section_title}</span>
                    </button>
                  </li>
                ))}
              </ul>
            )
          ) : <TopicTree units={tree.data} selectedId={selected?.id ?? null} onSelect={setSelected} />}
        </div>

        <aside className="card h-fit p-5 lg:sticky lg:top-6" aria-live="polite">
          {!selected ? <p className="text-sm text-navy-600">Select a concept to see its details and start learning.</p> : (
            <>
              <Breadcrumb concept={selected} />
              <h2 className="text-lg font-bold text-navy-900">{selected.title === 'Overview' ? `${selected.section_title} (overview)` : selected.title}</h2>
              <dl className="mt-3 space-y-1 text-sm text-navy-700">
                <div className="flex justify-between"><dt>Unit</dt><dd className="text-right font-medium">{selected.unit_title}</dd></div>
                <div className="flex justify-between"><dt>Chapter</dt><dd className="text-right font-medium">{selected.chapter_number}. {selected.chapter_title}</dd></div>
                <div className="flex justify-between"><dt>Section</dt><dd className="text-right font-medium">{selected.section_number} {selected.section_title}</dd></div>
                <div className="flex justify-between"><dt>Indexed passages</dt><dd className="font-medium">{selected.chunk_count}</dd></div>
              </dl>
              {selected.available
                ? <button className="btn-primary mt-5 w-full" onClick={() => nav(`/learn/${selected.id}`)}>Start Learning <ArrowRight className="h-4 w-4" aria-hidden="true" /></button>
                : <div className="mt-5"><Alert kind="warn">This topic has too little indexed textbook content, so AI generation is disabled for it.</Alert></div>}
            </>
          )}
        </aside>
      </div>
    </>
  )
}
