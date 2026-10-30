import { BookOpenCheck, ChevronDown, Quote } from 'lucide-react'
import { useRef, useState } from 'react'
import type { EvidenceItem } from '../types'
import { Markdown, splitSections } from './Markdown'

export function SectionPanels({ markdown, onEvidence }: { markdown: string; onEvidence?: (l: string) => void }) {
  const sections = splitSections(markdown)
  return (
    <div className="space-y-3">
      {sections.map((s, i) => (
        <details key={s.title + i} open className="group card overflow-hidden">
          <summary className="flex cursor-pointer list-none items-center justify-between gap-2 bg-sky-50 px-5 py-3 font-semibold text-navy-800">
            <span>{s.title}</span>
            <ChevronDown className="h-4 w-4 transition group-open:rotate-180" aria-hidden="true" />
          </summary>
          <div className="px-5 py-3"><Markdown text={s.body} onEvidence={onEvidence} /></div>
        </details>
      ))}
    </div>
  )
}

export function EvidencePanel({ evidence, openLabel }: { evidence: EvidenceItem[]; openLabel: string | null }) {
  return (
    <section aria-labelledby="evidence-h" className="card p-5">
      <h2 id="evidence-h" className="mb-1 flex items-center gap-2 text-base font-semibold text-navy-800">
        <Quote className="h-4 w-4 text-teal-600" aria-hidden="true" /> Retrieved textbook evidence
      </h2>
      <p className="mb-3 text-xs text-navy-600">Verbatim excerpts retrieved for this topic. Statements marked [E#] above come from
        these. Anything labelled “Additional explanation” is the AI’s own wording, not the textbook’s.</p>
      <div className="space-y-2">
        {evidence.map((e) => (
          <details key={e.chunk_id} id={`ev-${e.label}`} open={openLabel === e.label} className="rounded-xl border border-navy-100">
            <summary className="flex cursor-pointer flex-wrap items-center gap-2 px-3 py-2 text-sm">
              <span className="rounded bg-navy-800 px-1.5 py-0.5 text-[11px] font-bold text-white">{e.label}</span>
              <span className="font-medium text-navy-800">{e.section_title}</span>
              <span className="text-xs text-navy-600">· PDF p. {e.pdf_pages.join('–')} · similarity {e.score.toFixed(2)}</span>
              <span className="ml-auto font-mono text-[10px] text-navy-600/60">{e.chunk_id}</span>
            </summary>
            <blockquote className="whitespace-pre-line border-t border-navy-100 bg-sky-25 px-4 py-3 text-sm leading-relaxed text-navy-800">{e.text}</blockquote>
          </details>
        ))}
      </div>
    </section>
  )
}

export function StudyNotes({ markdown, evidence, title = 'Study notes' }: { markdown: string; evidence: EvidenceItem[]; title?: string }) {
  const [open, setOpen] = useState<string | null>(null)
  const ref = useRef<HTMLDivElement>(null)
  const jump = (label: string) => {
    setOpen(label)
    setTimeout(() => document.getElementById(`ev-${label}`)?.scrollIntoView({ behavior: 'smooth', block: 'center' }), 50)
  }
  return (
    <div ref={ref} className="space-y-4">
      <h2 className="flex items-center gap-2 text-lg font-semibold text-navy-900">
        <BookOpenCheck className="h-5 w-5 text-teal-600" aria-hidden="true" />{title}
      </h2>
      <SectionPanels markdown={markdown} onEvidence={jump} />
      <EvidencePanel evidence={evidence} openLabel={open} />
    </div>
  )
}
