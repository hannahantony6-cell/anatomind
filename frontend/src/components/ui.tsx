import { AlertCircle, Eye, EyeOff, Inbox, Loader2 } from 'lucide-react'
import { useId, useState, type InputHTMLAttributes, type ReactNode } from 'react'

export function Spinner({ className = '' }: { className?: string }) {
  return <Loader2 className={`animate-spin ${className}`} aria-hidden="true" />
}

export function LoadingState({ label = 'Loading…', hint }: { label?: string; hint?: string }) {
  return (
    <div role="status" aria-live="polite" className="flex flex-col items-center justify-center gap-3 py-16 text-center text-navy-700">
      <Spinner className="h-8 w-8 text-teal-600" />
      <p className="font-medium">{label}</p>
      {hint && <p className="max-w-md text-sm text-navy-600/80">{hint}</p>}
    </div>
  )
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div role="alert" className="flex flex-col items-center gap-3 rounded-2xl border border-red-200 bg-red-50 p-8 text-center">
      <AlertCircle className="h-8 w-8 text-red-600" aria-hidden="true" />
      <p className="max-w-lg text-sm text-red-800">{message}</p>
      {onRetry && <button className="btn-secondary" onClick={onRetry}>Try again</button>}
    </div>
  )
}

export function EmptyState({ title, children, action }: { title: string; children?: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex flex-col items-center gap-2 rounded-2xl border border-dashed border-navy-200 bg-white/60 p-8 text-center">
      <Inbox className="h-8 w-8 text-navy-600/60" aria-hidden="true" />
      <p className="font-semibold text-navy-800">{title}</p>
      {children && <div className="max-w-md text-sm text-navy-600">{children}</div>}
      {action}
    </div>
  )
}

export function Alert({ kind, children }: { kind: 'error' | 'success' | 'info' | 'warn'; children: ReactNode }) {
  const styles = {
    error: 'border-red-200 bg-red-50 text-red-800', success: 'border-teal-100 bg-teal-50 text-teal-700',
    info: 'border-navy-100 bg-sky-50 text-navy-800', warn: 'border-amber-200 bg-amber-50 text-amber-900',
  }[kind]
  return <div role={kind === 'error' ? 'alert' : 'status'} className={`rounded-xl border px-4 py-3 text-sm ${styles}`}>{children}</div>
}

interface FieldProps extends InputHTMLAttributes<HTMLInputElement> { label: string; error?: string; hint?: string }

export function TextField({ label, error, hint, id, ...rest }: FieldProps) {
  const auto = useId()
  const fid = id ?? auto
  return (
    <div>
      <label htmlFor={fid} className="mb-1.5 block text-sm font-medium text-navy-800">{label}</label>
      <input id={fid} className={`input ${error ? 'border-red-400' : ''}`} aria-invalid={!!error}
        aria-describedby={error ? `${fid}-err` : hint ? `${fid}-hint` : undefined} {...rest} />
      {error && <p id={`${fid}-err`} className="mt-1 text-xs text-red-600">{error}</p>}
      {!error && hint && <p id={`${fid}-hint`} className="mt-1 text-xs text-navy-600/70">{hint}</p>}
    </div>
  )
}

export function PasswordField({ label, error, hint, id, ...rest }: FieldProps) {
  const auto = useId()
  const fid = id ?? auto
  const [show, setShow] = useState(false)
  return (
    <div>
      <label htmlFor={fid} className="mb-1.5 block text-sm font-medium text-navy-800">{label}</label>
      <div className="relative">
        <input id={fid} type={show ? 'text' : 'password'} className={`input pr-11 ${error ? 'border-red-400' : ''}`}
          aria-invalid={!!error} aria-describedby={error ? `${fid}-err` : hint ? `${fid}-hint` : undefined} {...rest} />
        <button type="button" onClick={() => setShow((s) => !s)} aria-label={show ? 'Hide password' : 'Show password'}
          className="absolute inset-y-0 right-0 flex w-10 items-center justify-center text-navy-600 hover:text-navy-900">
          {show ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
        </button>
      </div>
      {error && <p id={`${fid}-err`} className="mt-1 text-xs text-red-600">{error}</p>}
      {!error && hint && <p id={`${fid}-hint`} className="mt-1 text-xs text-navy-600/70">{hint}</p>}
    </div>
  )
}

export function ProgressBar({ value, label, tone = 'teal' }: { value: number; label?: string; tone?: 'teal' | 'amber' | 'red' }) {
  const pct = Math.max(0, Math.min(100, value))
  const color = { teal: 'bg-teal-500', amber: 'bg-amber-500', red: 'bg-red-500' }[tone]
  return (
    <div role="progressbar" aria-valuenow={Math.round(pct)} aria-valuemin={0} aria-valuemax={100} aria-label={label}
      className="h-2 w-full overflow-hidden rounded-full bg-navy-100">
      <div className={`h-full rounded-full transition-all ${color}`} style={{ width: `${pct}%` }} />
    </div>
  )
}

export function PageHeader({ title, subtitle, actions }: { title: string; subtitle?: ReactNode; actions?: ReactNode }) {
  return (
    <div className="mb-6 flex flex-wrap items-start justify-between gap-3">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-navy-900">{title}</h1>
        {subtitle && <p className="mt-1 text-sm text-navy-600">{subtitle}</p>}
      </div>
      {actions && <div className="flex flex-wrap gap-2">{actions}</div>}
    </div>
  )
}
