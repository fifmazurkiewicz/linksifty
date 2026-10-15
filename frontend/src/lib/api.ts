import type { Session } from '@supabase/supabase-js'

const base = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
export const AUTH_EXPIRED_EVENT = 'linksifty:session-expired'

export type Account = {
  user_id: string
  email: string
  status: 'pending' | 'approved' | 'rejected'
  role: 'user' | 'admin'
  trial_links_used: number
  trial_links_remaining: number
}

export type AdminAccount = Account & {
  approval_email_status: 'pending' | 'sending' | 'sent' | 'failed' | null
  approval_email_failure_code: string | null
  created_at: string
}

export class ApiError extends Error {
  readonly status: number

  constructor(message: string, status: number) {
    super(message)
    this.status = status
  }
}

export async function api<T>(path: string, session: Session, init: RequestInit = {}): Promise<T> {
  const response = await fetch(`${base}${path}`, {
    ...init,
    headers: {
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...init.headers,
      Authorization: `Bearer ${session.access_token}`,
    },
  })
  if (!response.ok) {
    if (response.status === 401) window.dispatchEvent(new CustomEvent(AUTH_EXPIRED_EVENT, { detail: session.user.id }))
    let message = 'The request could not be completed.'
    try {
      const body = await response.json() as { detail?: string }
      if (typeof body.detail === 'string') message = body.detail
    } catch { /* Keep the safe fallback for non-JSON responses. */ }
    throw new ApiError(message, response.status)
  }
  return response.json() as Promise<T>
}

export type Item = {
  id: string
  title: string
  status: string
  score: number | null
  verdict: string | null
  processing_stage?: string
  failure_reason?: string | null
  original_url?: string | null
  updated_at?: string | null
  worker_active?: boolean | null
}

export type Usage = {
  month: string
  spent_usd: string
  reserved_usd: string
  limit_usd: string
  remaining_usd: string
  resets_at: string
}

export type Assessment = {
  research_status?: string
  research_sources?: { id: string; url: string }[]
  note: string
  score: number
  verdict: string
  threshold_snapshot: number
  criteria: { name: string; score: number; rationale: string; citation_ids: string[] }[]
  citations: { id: string; excerpt: string; source_url: string | null }[]
}

export function money(value: string): string {
  const amount = Number(value)
  if (!Number.isFinite(amount)) return 'Unavailable'
  if (amount > 0 && amount < 0.000001) return '<0.000001 USD'
  return `${amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 6 })} USD`
}

export function isUsage(value: unknown): value is Usage {
  if (!value || typeof value !== 'object') return false
  const usage = value as Record<string, unknown>
  return ['spent_usd', 'reserved_usd', 'limit_usd', 'remaining_usd'].every(key =>
    (typeof usage[key] === 'string' || typeof usage[key] === 'number') && Number.isFinite(Number(usage[key])))
    && typeof usage.resets_at === 'string'
}

export async function watchActivity(session: Session, signal: AbortSignal,
  onSnapshot: (items: Item[], usage: Usage) => void): Promise<void> {
  const response = await fetch(`${base}/v1/activity`, {
    headers: { Authorization: `Bearer ${session.access_token}` }, signal,
  })
  if (!response.ok) throw new ApiError('Live progress is unavailable.', response.status)
  if (!response.headers.get('Content-Type')?.includes('text/event-stream') || !response.body) {
    throw new Error('Live progress is unavailable.')
  }
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  try {
    while (!signal.aborted) {
      const { done, value } = await reader.read()
      if (done) return
      buffer += decoder.decode(value, { stream: true })
      buffer = buffer.replaceAll('\r\n', '\n')
      let boundary: number
      while ((boundary = buffer.indexOf('\n\n')) >= 0) {
        const frame = buffer.slice(0, boundary)
        buffer = buffer.slice(boundary + 2)
        if (frame.includes('event: denied')) throw new ApiError('Account access changed.', 403)
        const payload = frame.split('\n').filter(line => line.startsWith('data:')).map(line => line.slice(5).trimStart()).join('\n')
        if (!payload || !frame.includes('event: snapshot')) continue
        const snapshot = JSON.parse(payload) as { items: (Item & { title: string | null })[]; usage: Usage }
        if (!Array.isArray(snapshot.items) || !isUsage(snapshot.usage)) throw new Error('Invalid progress snapshot.')
        onSnapshot(snapshot.items.map(item => ({ ...item, title: item.title || item.original_url || 'Pasted content' })), snapshot.usage)
      }
    }
  } finally {
    await reader.cancel().catch(() => {})
    reader.releaseLock()
  }
}
