import { BookOpen, ChevronDown, ChevronRight, Lock } from 'lucide-react'
import { useState } from 'react'
import type { ChapterOut, ConceptDetail, ConceptOut, SectionOut, UnitOut } from '../types'

export interface SelectedTopic { concept: ConceptDetail }

interface Props { units: UnitOut[]; selectedId: string | null; onSelect: (c: ConceptDetail) => void }

function Toggle({ open, onClick, children, level }: { open: boolean; onClick: () => void; children: React.ReactNode; level: 0 | 1 | 2 }) {
  const Icon = open ? ChevronDown : ChevronRight
  const style = ['font-bold text-navy-900', 'font-semibold text-navy-800', 'font-medium text-navy-700'][level]
  return (
    <button type="button" onClick={onClick} aria-expanded={open}
      className={`flex w-full items-center gap-2 rounded-lg px-2 py-2 text-left text-sm hover:bg-sky-50 ${style}`}>
      <Icon className="h-4 w-4 shrink-0 text-navy-600" aria-hidden="true" />{children}
    </button>
  )
}

export function TopicTree({ units, selectedId, onSelect }: Props) {
  const [open, setOpen] = useState<Record<string, boolean>>({})
  const flip = (id: string) => setOpen((o) => ({ ...o, [id]: !o[id] }))

  const detail = (u: UnitOut, ch: ChapterOut, s: SectionOut, c: ConceptOut): ConceptDetail => ({
    id: c.id, title: c.title, unit_id: u.id, unit_title: u.title, chapter_id: ch.id, chapter_number: ch.number,
    chapter_title: ch.title, section_id: s.id, section_number: s.number, section_title: s.title,
    page_start: null, page_end: null, chunk_count: c.chunk_count, available: c.available,
  })

  return (
    <div className="space-y-1" role="tree" aria-label="Textbook syllabus">
      {units.map((u) => (
        <div key={u.id} role="treeitem" aria-expanded={!!open[u.id]}>
          <Toggle open={!!open[u.id]} onClick={() => flip(u.id)} level={0}>
            <span>Unit {u.number}: {u.title}</span>
          </Toggle>
          {open[u.id] && (
            <div className="ml-3 border-l border-navy-100 pl-2">
              {u.chapters.map((ch) => (
                <div key={ch.id} role="treeitem" aria-expanded={!!open[ch.id]}>
                  <Toggle open={!!open[ch.id]} onClick={() => flip(ch.id)} level={1}>
                    <span>Chapter {ch.number}: {ch.title}</span>
                  </Toggle>
                  {open[ch.id] && (
                    <div className="ml-3 border-l border-navy-100 pl-2">
                      {ch.sections.map((s) => (
                        <div key={s.id} role="treeitem" aria-expanded={!!open[s.id]}>
                          <Toggle open={!!open[s.id]} onClick={() => flip(s.id)} level={2}>
                            <span>{s.number} {s.title}</span>
                          </Toggle>
                          {open[s.id] && (
                            <ul className="ml-6 space-y-0.5 pb-1" role="group">
                              {s.concepts.map((c) => (
                                <li key={c.id}>
                                  <button type="button" onClick={() => onSelect(detail(u, ch, s, c))} aria-current={selectedId === c.id}
                                    className={`flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm ${selectedId === c.id ? 'bg-teal-50 font-semibold text-teal-700' : 'text-navy-800 hover:bg-sky-50'}`}>
                                    {c.available ? <BookOpen className="h-3.5 w-3.5 shrink-0 text-teal-600" aria-hidden="true" /> : <Lock className="h-3.5 w-3.5 shrink-0 text-navy-600/50" aria-hidden="true" />}
                                    <span className="flex-1">{c.title}</span>
                                    {!c.available && <span className="text-[10px] text-navy-600">not enough content</span>}
                                  </button>
                                </li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  )
}
