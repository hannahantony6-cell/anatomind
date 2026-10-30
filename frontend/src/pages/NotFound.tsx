import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="flex min-h-[60vh] flex-col items-center justify-center gap-3 text-center">
      <p className="text-5xl font-bold text-navy-800">404</p>
      <p className="text-navy-600">That page doesn’t exist.</p>
      <Link to="/dashboard" className="btn-primary">Go to dashboard</Link>
    </div>
  )
}
