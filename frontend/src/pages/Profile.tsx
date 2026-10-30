import { LogOut } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { Disclaimer } from '../components/Disclaimer'
import { PageHeader } from '../components/ui'
import { useAuth } from '../hooks/useAuth'

export default function Profile() {
  const { user, logout } = useAuth()
  const nav = useNavigate()
  if (!user) return null
  return (
    <>
      <PageHeader title="Profile" />
      <div className="card max-w-xl space-y-4 p-6">
        <dl className="space-y-3 text-sm">
          <div><dt className="text-xs uppercase text-navy-600">Name</dt><dd className="font-semibold">{user.full_name}</dd></div>
          <div><dt className="text-xs uppercase text-navy-600">Email</dt><dd className="font-semibold">{user.email}</dd></div>
          <div><dt className="text-xs uppercase text-navy-600">Member since</dt><dd className="font-semibold">{new Date(user.created_at).toLocaleDateString()}</dd></div>
        </dl>
        <Disclaimer />
        <button className="btn-secondary" onClick={async () => { await logout(); nav('/login', { replace: true }) }}><LogOut className="h-4 w-4" aria-hidden="true" />Log out</button>
      </div>
    </>
  )
}
