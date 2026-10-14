import type { Session } from '@supabase/supabase-js'

const base = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'

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
    let message = 'The request could not be completed.'
    try {
      const body = await response.json() as { detail?: string }
      if (body.detail) message = body.detail
    } catch { /* Keep the safe fallback for non-JSON responses. */ }
    throw new ApiError(message, response.status)
  }
  return response.json() as Promise<T>
}
