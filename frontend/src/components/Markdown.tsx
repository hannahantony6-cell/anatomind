import { useMemo, type ReactNode } from 'react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/** Renders model Markdown. [E#] markers become clickable chips; "(Additional explanation)" is flagged. */
export function Markdown({ text, onEvidence }: { text: string; onEvidence?: (label: string) => void }) {
  const prepared = useMemo(() => text
    .replace(/\[(E\d+)\]/g, '[$1](#ev-$1)')
    .replace(/\(Additional explanation\)/gi, '*(Additional explanation)*'), [text])
  return (
    <div className="prose-notes text-sm">
      <ReactMarkdown remarkPlugins={[remarkGfm]} components={{
        a: ({ href, children }) => {
          if (href?.startsWith('#ev-')) {
            const label = href.slice(4)
            return (
              <button type="button" onClick={() => onEvidence?.(label)} aria-label={`Show textbook evidence ${label}`}
                className="mx-0.5 rounded bg-navy-100 px-1.5 py-0.5 align-baseline text-[11px] font-semibold text-navy-700 hover:bg-navy-200">
                {children}
              </button>
            )
          }
          return <a href={href} target="_blank" rel="noopener noreferrer" className="text-teal-700 underline">{children}</a>
        },
        em: ({ children }: { children?: ReactNode }) => {
          const t = String(children)
          return t.startsWith('(Additional')
            ? <span className="mr-1 rounded bg-amber-100 px-1.5 py-0.5 text-[11px] font-semibold not-italic text-amber-900">{t}</span>
            : <em>{children}</em>
        },
      }}>{prepared}</ReactMarkdown>
    </div>
  )
}

/** Split Markdown into "## " sections so each can be an expandable panel. */
export function splitSections(md: string): { title: string; body: string }[] {
  const parts = md.split(/^##\s+/m)
  const out: { title: string; body: string }[] = []
  parts.forEach((p, i) => {
    if (i === 0) { if (p.trim()) out.push({ title: 'Overview', body: p.trim() }); return }
    const nl = p.indexOf('\n')
    out.push({ title: (nl === -1 ? p : p.slice(0, nl)).trim(), body: nl === -1 ? '' : p.slice(nl + 1).trim() })
  })
  return out
}
