import { AlertTriangle, CheckCircle2, CircleDot } from 'lucide-react'
import type { MasteryLevel } from '../types'

const META: Record<MasteryLevel, { label: string; cls: string; Icon: typeof CheckCircle2 }> = {
  good: { label: 'Good / Mastered', cls: 'bg-teal-50 text-teal-700 border-teal-100', Icon: CheckCircle2 },
  average: { label: 'Average / Reinforce', cls: 'bg-amber-50 text-amber-800 border-amber-200', Icon: CircleDot },
  weak: { label: 'Weak / Remediate', cls: 'bg-red-50 text-red-700 border-red-200', Icon: AlertTriangle },
}
export const LEVEL_COLOR: Record<MasteryLevel, string> = { good: '#14a595', average: '#d99a1d', weak: '#dc4c4c' }

export function MasteryBadge({ level, score }: { level: MasteryLevel; score?: number }) {
  const { label, cls, Icon } = META[level]
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-xs font-semibold ${cls}`}>
      <Icon className="h-3.5 w-3.5" aria-hidden="true" />
      {label}{score !== undefined && ` · ${Math.round(score * 100)}%`}
    </span>
  )
}
