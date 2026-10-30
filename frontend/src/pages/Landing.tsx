import { BookMarked, BrainCircuit, LineChart, Lock, Target } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Disclaimer } from '../components/Disclaimer'
import { Logo } from '../components/Logo'

const FEATURES = [
  { Icon: BookMarked, title: 'Grounded in your textbook', text: 'Every note and quiz is retrieved from OpenStax Anatomy & Physiology 2e, with traceable excerpts and page references. No invented citations.' },
  { Icon: Target, title: 'Five-question quizzes', text: 'Textbook-based MCQs for each concept, graded by deterministic code, so your score is never up to an AI’s opinion.' },
  { Icon: LineChart, title: 'Concept-level mastery', text: 'An exponential moving average tracks each concept separately and flags what is Good, Average or Weak.' },
  { Icon: BrainCircuit, title: 'Adaptive remediation', text: 'Weak concepts trigger a simpler re-explanation from the same chapter, then a focused re-quiz, up to three rounds.' },
]

export default function Landing() {
  return (
    <div className="min-h-screen bg-white">
      <header className="mx-auto flex max-w-6xl items-center justify-between px-4 py-5 sm:px-8">
        <Logo />
        <div className="flex gap-2">
          <Link to="/login" className="btn-secondary">Log in</Link>
          <Link to="/signup" className="btn-primary">Sign up</Link>
        </div>
      </header>
      <section className="bg-gradient-to-b from-sky-50 to-white">
        <div className="mx-auto max-w-4xl px-4 py-20 text-center sm:px-8">
          <p className="mb-3 inline-block rounded-full bg-teal-100 px-3 py-1 text-xs font-semibold text-teal-700">For first-year MBBS students</p>
          <h1 className="text-4xl font-extrabold tracking-tight text-navy-900 sm:text-6xl">Understand. Practise. Improve.</h1>
          <p className="mx-auto mt-5 max-w-2xl text-lg text-navy-700">Anatomind turns the Anatomy &amp; Physiology textbook into structured study notes, quizzes and
            personalised revision, then adapts to the concepts you find hardest.</p>
          <div className="mt-8 flex flex-wrap justify-center gap-3">
            <Link to="/signup" className="btn-primary px-6 py-3 text-base">Create free account</Link>
            <Link to="/login" className="btn-secondary px-6 py-3 text-base">Log in</Link>
          </div>
        </div>
      </section>
      <section className="mx-auto max-w-6xl px-4 py-16 sm:px-8" aria-labelledby="features-h">
        <h2 id="features-h" className="mb-8 text-center text-2xl font-bold text-navy-900">How Anatomind helps you learn</h2>
        <div className="grid gap-5 sm:grid-cols-2">
          {FEATURES.map(({ Icon, title, text }) => (
            <div key={title} className="card p-6">
              <span className="mb-3 flex h-10 w-10 items-center justify-center rounded-xl bg-teal-50 text-teal-600"><Icon className="h-5 w-5" aria-hidden="true" /></span>
              <h3 className="mb-1 font-semibold text-navy-900">{title}</h3>
              <p className="text-sm text-navy-700">{text}</p>
            </div>
          ))}
        </div>
      </section>
      <section className="bg-navy-900 text-white">
        <div className="mx-auto flex max-w-4xl flex-col items-center gap-3 px-4 py-14 text-center sm:px-8">
          <Lock className="h-8 w-8 text-teal-500" aria-hidden="true" />
          <h2 className="text-2xl font-bold">Privacy-first, local AI</h2>
          <p className="max-w-2xl text-navy-100">The language model (Llama 3.2 3B) and the embedding model run on the same machine through Ollama.
            Your study activity and quiz answers are stored in a local database and are never sent to a cloud AI service.</p>
        </div>
      </section>
      <footer className="mx-auto max-w-4xl px-4 py-8 sm:px-8"><Disclaimer /></footer>
    </div>
  )
}
