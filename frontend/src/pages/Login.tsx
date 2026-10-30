import { Loader2 } from 'lucide-react'
import { useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { Alert, PasswordField, TextField } from '../components/ui'
import { useAuth } from '../hooks/useAuth'
import AuthLayout from '../layouts/AuthLayout'
import { errorMessage } from '../services/api'

export default function Login() {
  const { user, login } = useAuth()
  const nav = useNavigate()
  const loc = useLocation()
  const state = loc.state as { from?: string; signedUp?: boolean } | null
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  if (user) return <Navigate to="/dashboard" replace />

  const submit = async (e: FormEvent) => {
    e.preventDefault()
    setError(null); setBusy(true)
    try {
      await login(email.trim(), password)
      nav(state?.from && state.from !== '/login' ? state.from : '/dashboard', { replace: true })
    } catch (err) {
      setError(errorMessage(err))
    } finally { setBusy(false) }
  }

  return (
    <AuthLayout title="Welcome back" subtitle="Log in to continue learning.">
      <form onSubmit={submit} className="space-y-4" noValidate>
        {state?.signedUp && <Alert kind="success">Account created! Please log in.</Alert>}
        {error && <Alert kind="error">{error}</Alert>}
        <TextField label="Email" type="email" autoComplete="email" required value={email} onChange={(e) => setEmail(e.target.value)} />
        <PasswordField label="Password" autoComplete="current-password" required value={password} onChange={(e) => setPassword(e.target.value)} />
        <button className="btn-primary w-full" disabled={busy || !email || !password}>
          {busy && <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" />}{busy ? 'Logging in…' : 'Log in'}
        </button>
      </form>
      <p className="mt-5 text-center text-sm text-navy-700">New to Anatomind? <Link to="/signup" className="font-semibold text-teal-700 hover:underline">Create an account</Link></p>
    </AuthLayout>
  )
}
