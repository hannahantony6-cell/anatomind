import { Award } from 'lucide-react'
import type { QuizResult } from '../types'
import { ProgressBar } from './ui'

export function ScoreSummary({ result }: { result: QuizResult }) {
  const pct = result.score
  const tone = pct >= 80 ? 'teal' : pct >= 50 ? 'amber' : 'red'
  return (
    <div className="card flex flex-col items-center gap-3 p-8 text-center">
      <Award className="h-9 w-9 text-teal-600" aria-hidden="true" />
      <p className="text-5xl font-bold text-navy-900">{result.correct_count}<span className="text-2xl text-navy-600"> / {result.total_questions}</span></p>
      <p className="text-lg font-semibold text-navy-800">{Math.round(pct)}%</p>
      <div className="w-full max-w-xs"><ProgressBar value={pct} tone={tone} label="Quiz score" /></div>
      <p className="text-xs text-navy-600">Graded by deterministic backend code · {new Date(result.submitted_at).toLocaleString()}</p>
    </div>
  )
}
