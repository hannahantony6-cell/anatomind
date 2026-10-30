import { Link } from 'react-router-dom'

export function LogoMark({ size = 32 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="8" fill="#0d2038" />
      <path d="M16 6c-4 0-7 3-7 7 0 2 .8 3.7 2 5l-1 6h12l-1-6c1.2-1.3 2-3 2-5 0-4-3-7-7-7z" fill="none" stroke="#14a595" strokeWidth="2" strokeLinejoin="round" />
      <circle cx="16" cy="13" r="2" fill="#14a595" />
    </svg>
  )
}

export function Logo({ to = '/', light = false }: { to?: string; light?: boolean }) {
  return (
    <Link to={to} className="flex items-center gap-2.5" aria-label="Anatomind home">
      <LogoMark />
      <span className={`text-lg font-bold tracking-tight ${light ? 'text-white' : 'text-navy-900'}`}>Anatomind</span>
    </Link>
  )
}
