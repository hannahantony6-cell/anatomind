import { Loader2 } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { Alert, PasswordField, TextField } from '../components/ui'
import { useAuth } from '../hooks/useAuth'
import AuthLayout from '../layouts/AuthLayout'
import { api, errorMessage } from '../services/api'

type Errors = Partial<Record<'full_name' | 'email' | 'password' | 'confirm', string>>

function validate(f: { full_name: string; email: string; password: string; confirm: string }): Errors {
  const e: Errors = {}
  if (f.full_name.trim().length < 2) e.full_name = 'Please enter your full name.'
  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(f.email.trim())) e.email = 'Enter a valid email address.'
  if (f.password.length < 8) e.password = 'Use at least 8 characters.'
  else if (!/[a-z]/.test(f.password) || !/[A-Z]/.test(f.password) || !/\d/.test(f.password))
    e.password = 'Include a lowercase letter, an uppercase letter and a number.'
  if (f.confirm !== f.password) e.confirm = 'Passwords do not match.'
  return e
}

export default function Signup() {
  const { user } = useAuth()
  const nav = useNavigate()
  const [f, setF] = useState({ full_name: '', email: '', password: '', confirm: '' })
  const [errors, setErrors] = useState<Errors>({})
  const [serverError, setServerError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  if (user) return <Navigate to="/dashboard" replace />
  const set = (k: keyof typeof f) => (e: React.ChangeEvent<HTMLInputElement>) => setF((p) => ({ ...p, [k]: e.target.value }))

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setServerError(null)
    const v = validate(f)
    setErrors(v)
    if (Object.keys(v).length) return
    setBusy(true)
    try {
      await api.signup({ full_name: f.full_name.trim(), email: f.email.trim(), password: f.password, confirm_password: f.confirm })
      nav('/login', { replace: true, state: { signedUp: true } })
    } catch (err) {
      setServerError(errorMessage(err))
    } finally { setBusy(false) }
  }

  return (
    <AuthLayout title="Create your account" subtitle="Start studying from your textbook in minutes.">
      <form onSubmit={submit} className="space-y-4" noValidate>
        {serverError && <Alert kind="error">{serverError}</Alert>}
        <TextField label="Full name" autoComplete="name" value={f.full_name} onChange={set('full_name')} error={errors.full_name} />
        <TextField label="Email address" type="email" autoComplete="email" value={f.email} onChange={set('email')} error={errors.email} />
        <PasswordField label="Password" autoComplete="new-password" value={f.password} onChange={set('password')} error={errors.password}
          hint="At least 8 characters with upper-case, lower-case and a number." />
        <PasswordField label="Confirm password" autoComplete="new-password" value={f.confirm} onChange={set('confirm')} error={errors.confirm} />
        <button className="btn-primary w-full" disabled={busy}>
          {busy && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}{busy ? 'Creating account…' : 'Create Account'}
        </button>
      </form>
      <p className="mt-5 text-center text-sm text-navy-700">Already have an account? <Link to="/login" className="font-semibold text-teal-700 hover:underline">Log in</Link></p>
    </AuthLayout>
  )
}
