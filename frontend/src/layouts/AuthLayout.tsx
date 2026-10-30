import type { ReactNode } from 'react'
import { Disclaimer } from '../components/Disclaimer'
import { Logo } from '../components/Logo'

export default function AuthLayout({ title, subtitle, children }: { title: string; subtitle: string; children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-gradient-to-b from-sky-50 to-white px-4 py-10">
      <div className="mb-6"><Logo /></div>
      <div className="card w-full max-w-md p-8">
        <h1 className="text-2xl font-bold text-navy-900">{title}</h1>
        <p className="mb-6 mt-1 text-sm text-navy-600">{subtitle}</p>
        {children}
      </div>
      <div className="mt-6 max-w-md"><Disclaimer compact /></div>
    </div>
  )
}
