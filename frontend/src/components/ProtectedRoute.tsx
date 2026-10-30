import { Navigate, Outlet, useLocation } from 'react-router-dom'
import { useAuth } from '../hooks/useAuth'
import { LoadingState } from './ui'

export function ProtectedRoute() {
  const { user, loading } = useAuth()
  const loc = useLocation()
  if (loading) return <LoadingState label="Checking your session…" />
  if (!user) return <Navigate to="/login" replace state={{ from: loc.pathname }} />
  return <Outlet />
}
