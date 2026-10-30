import type { EvidenceItem } from '../types'
import { StudyNotes } from './StudyNotes'

export function RemedialContent({ markdown, evidence }: { markdown: string; evidence: EvidenceItem[] }) {
  return <StudyNotes markdown={markdown} evidence={evidence} title="Simplified revision" />
}
