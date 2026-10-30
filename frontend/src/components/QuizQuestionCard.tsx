import type { QuizQuestion } from '../types'

interface Props {
  question: QuizQuestion
  index: number
  total: number
  selected: string | undefined
  onSelect: (optionId: string) => void
}

export function QuizQuestionCard({ question, index, total, selected, onSelect }: Props) {
  return (
    <fieldset className="card p-6">
      <legend className="sr-only">Question {index + 1} of {total}</legend>
      <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-teal-700">Question {index + 1} of {total}</p>
      <p className="mb-5 text-lg font-semibold leading-snug text-navy-900">{question.question}</p>
      <div role="radiogroup" aria-label={`Answer options for question ${index + 1}`} className="space-y-2.5">
        {question.options.map((o) => {
          const active = selected === o.id
          return (
            <label key={o.id} className={`flex cursor-pointer items-start gap-3 rounded-xl border px-4 py-3 transition focus-within:ring-2 focus-within:ring-teal-500 ${active ? 'border-teal-500 bg-teal-50' : 'border-navy-100 hover:bg-sky-50'}`}>
              <input type="radio" name={question.id} value={o.id} checked={active} onChange={() => onSelect(o.id)} className="sr-only" />
              <span className={`mt-0.5 flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-xs font-bold ${active ? 'bg-teal-600 text-white' : 'bg-navy-100 text-navy-800'}`}>{o.id}</span>
              <span className="text-sm text-navy-900">{o.text}</span>
            </label>
          )
        })}
      </div>
    </fieldset>
  )
}
