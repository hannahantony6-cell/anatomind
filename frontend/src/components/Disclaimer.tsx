import { ShieldCheck } from 'lucide-react'

export function Disclaimer({ compact = false }: { compact?: boolean }) {
  return (
    <p className={`flex items-start gap-2 text-navy-600 ${compact ? 'text-xs' : 'text-sm'}`}>
      <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-teal-600" aria-hidden="true" />
      <span>Educational tool only: not a clinical, diagnostic or treatment system. Content is generated locally from the
        OpenStax <em>Anatomy &amp; Physiology 2e</em> textbook.</span>
    </p>
  )
}
