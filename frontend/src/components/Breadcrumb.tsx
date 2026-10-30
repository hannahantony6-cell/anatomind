import { ChevronRight } from 'lucide-react'
import type { ConceptDetail } from '../types'

export function Breadcrumb({ concept }: { concept: ConceptDetail }) {
  const crumbs = [concept.unit_title, `Ch ${concept.chapter_number}: ${concept.chapter_title}`,
    `${concept.section_number} ${concept.section_title}`, concept.title]
  return (
    <nav aria-label="Breadcrumb" className="mb-3">
      <ol className="flex flex-wrap items-center gap-1 text-xs text-navy-600">
        {crumbs.map((c, i) => (
          <li key={i} className="flex items-center gap-1">
            {i > 0 && <ChevronRight className="h-3 w-3 text-navy-600/50" aria-hidden="true" />}
            <span className={i === crumbs.length - 1 ? 'font-semibold text-navy-900' : ''} aria-current={i === crumbs.length - 1 ? 'page' : undefined}>{c}</span>
          </li>
        ))}
      </ol>
    </nav>
  )
}
