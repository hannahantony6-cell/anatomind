import axios, { AxiosError } from 'axios'
import type {
  ConceptDetail, History, NotesResponse, Quiz, QuizResult, Remediation, SourceOut, Summary, TopicMastery, UnitOut, User,
} from '../types'

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '/api',
  withCredentials: true,          // httpOnly session cookie
  timeout: 600_000,               // local-LLM generation can take a while
})

http.interceptors.response.use(
  (r) => r,
  (err: AxiosError) => {
    const url = String(err.config?.url ?? '')
    if (err.response?.status === 401 && !url.startsWith('/auth/')) window.dispatchEvent(new Event('auth:expired'))
    return Promise.reject(err)
  },
)

interface ApiErrorBody { error?: { code?: string; message?: string } }

export function errorMessage(e: unknown): string {
  if (axios.isAxiosError(e)) {
    const body = e.response?.data as ApiErrorBody | undefined
    if (body?.error?.message) return body.error.message
    if (e.code === 'ECONNABORTED') return 'The request timed out. Please try again.'
    if (!e.response) return 'Cannot reach the Anatomind server. Is the backend running?'
  }
  return 'Something went wrong. Please try again.'
}
export function errorCode(e: unknown): string | undefined {
  return axios.isAxiosError(e) ? (e.response?.data as ApiErrorBody | undefined)?.error?.code : undefined
}

export const api = {
  signup: (b: { full_name: string; email: string; password: string; confirm_password: string }) =>
    http.post<User>('/auth/signup', b).then((r) => r.data),
  login: (email: string, password: string) =>
    http.post<{ user: User }>('/auth/login', { email, password }).then((r) => r.data.user),
  logout: () => http.post('/auth/logout'),
  me: () => http.get<User>('/auth/me').then((r) => r.data),

  tree: () => http.get<UnitOut[]>('/topics/tree').then((r) => r.data),
  search: (q: string) => http.get<ConceptDetail[]>('/topics/search', { params: { q } }).then((r) => r.data),
  concept: (id: string) => http.get<ConceptDetail>(`/topics/concepts/${id}`).then((r) => r.data),

  notes: (concept_id: string, regenerate = false) =>
    http.post<NotesResponse>('/learning/notes', { concept_id, regenerate }).then((r) => r.data),
  createQuiz: (concept_id: string, quiz_type: 'standard' | 'review' = 'standard', force_new = false) =>
    http.post<Quiz>('/learning/quiz', { concept_id, quiz_type, force_new }).then((r) => r.data),
  sources: (ids: string[]) =>
    http.get<SourceOut[]>('/learning/sources', { params: { chunk_id: ids }, paramsSerializer: { indexes: null } }).then((r) => r.data),

  quiz: (id: number) => http.get<Quiz>(`/quizzes/${id}`).then((r) => r.data),
  submitQuiz: (id: number, answers: Record<string, string>) =>
    http.post<QuizResult>(`/quizzes/${id}/submit`, { answers }).then((r) => r.data),
  results: (id: number) => http.get<QuizResult>(`/quizzes/${id}/results`).then((r) => r.data),

  summary: () => http.get<Summary>('/progress/summary').then((r) => r.data),
  progressTopics: () => http.get<TopicMastery[]>('/progress/topics').then((r) => r.data),
  history: (limit = 100) => http.get<History>('/progress/history', { params: { limit } }).then((r) => r.data),

  startRemediation: (concept_id: string, include_practice_questions = false, regenerate = false) =>
    http.post<Remediation>('/remediation/start', { concept_id, include_practice_questions, regenerate }).then((r) => r.data),
  remediation: (concept_id: string) => http.get<Remediation>(`/remediation/${concept_id}`).then((r) => r.data),
  retryRemediation: (concept_id: string) => http.post<Quiz>(`/remediation/${concept_id}/retry`).then((r) => r.data),
}
