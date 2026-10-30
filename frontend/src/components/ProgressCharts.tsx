import { Bar, BarChart, CartesianGrid, Cell, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import type { Attempt, TopicMastery } from '../types'
import { LEVEL_COLOR } from './MasteryBadge'
import { EmptyState } from './ui'

export function ScoreTrendChart({ attempts }: { attempts: Attempt[] }) {
  if (!attempts.length) return <EmptyState title="No quiz attempts yet">Complete a quiz to see your score trend.</EmptyState>
  const data = [...attempts].reverse().map((a, i) => ({
    n: i + 1, score: a.score, label: `${a.concept_title} (${new Date(a.created_at).toLocaleDateString()})`,
  }))
  return (
    <div role="img" aria-label="Line chart of quiz scores over time" className="h-64">
      <ResponsiveContainer>
        <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: -12 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e1eaf5" />
          <XAxis dataKey="n" tick={{ fontSize: 12 }} label={{ value: 'Attempt', position: 'insideBottom', offset: -2, fontSize: 12 }} />
          <YAxis domain={[0, 100]} tick={{ fontSize: 12 }} />
          <Tooltip formatter={(v: number) => [`${v}%`, 'Score']} labelFormatter={(_, p) => p?.[0]?.payload?.label ?? ''} />
          <Line type="monotone" dataKey="score" stroke="#0d8a7c" strokeWidth={2.5} dot={{ r: 3 }} />
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

export function MasteryBarChart({ topics }: { topics: TopicMastery[] }) {
  if (!topics.length) return <EmptyState title="No mastery data yet">Mastery appears after your first quiz.</EmptyState>
  const data = topics.slice(0, 12).map((t) => ({
    name: t.concept_title.length > 22 ? t.concept_title.slice(0, 21) + '…' : t.concept_title,
    full: `${t.section_title}: ${t.concept_title}`, pct: Math.round(t.mastery_score * 100), level: t.mastery_level,
  }))
  return (
    <div role="img" aria-label="Bar chart of mastery by concept" className="h-72">
      <ResponsiveContainer>
        <BarChart data={data} layout="vertical" margin={{ top: 4, right: 16, bottom: 0, left: 24 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e1eaf5" horizontal={false} />
          <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 12 }} />
          <YAxis type="category" dataKey="name" width={130} tick={{ fontSize: 11 }} />
          <Tooltip formatter={(v: number) => [`${v}%`, 'Mastery']} labelFormatter={(_, p) => p?.[0]?.payload?.full ?? ''} />
          <Bar dataKey="pct" radius={[0, 6, 6, 0]}>
            {data.map((d, i) => <Cell key={i} fill={LEVEL_COLOR[d.level]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
