import { useEffect, useState } from 'react'
import type { Session } from '@supabase/supabase-js'
import { api, isUsage, type Usage } from '../../lib/api'
import { UsagePanel } from '../settings/UsagePanel'

export function AccountBudget({ id, session, onSaved }: { id: string; session: Session; onSaved?: (usage: Usage) => void }) {
  const [usage, setUsage] = useState<Usage | null>(null)
  const [limit, setLimit] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [saved, setSaved] = useState(false)
  useEffect(() => {
    const controller = new AbortController()
    void api<Usage>(`/v1/admin/accounts/${id}/usage`, session, { signal: controller.signal }).then(value => {
      if (controller.signal.aborted) return
      if (!isUsage(value)) throw new Error('Account usage is unavailable.')
      setUsage(value); setLimit(String(value.limit_usd))
    }).catch(e => { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Could not load usage.') })
    return () => controller.abort()
  }, [id, session])
  return <form className="budget-form" onSubmit={event => {
    event.preventDefault()
    if (busy || limit === '' || Number(limit) < 0 || Number(limit) > 1000000) return
    setBusy(true); setError(null); setSaved(false)
    void api<Usage>(`/v1/admin/accounts/${id}/usage`, session, { method: 'PUT', body: JSON.stringify({ limit_usd: limit }) })
      .then(value => { setUsage(value); setLimit(String(value.limit_usd)); setSaved(true); onSaved?.(value) })
      .catch(e => setError(e instanceof Error ? e.message : 'Could not save limit.')).finally(() => setBusy(false))
  }}>
    <UsagePanel usage={usage} error={error} />
    <label htmlFor={`budget-${id}`}>Monthly limit (USD)</label>
    <input id={`budget-${id}`} type="number" min="0" max="1000000" step="0.00000001" value={limit} required
      disabled={!usage || busy} onChange={event => { setLimit(event.target.value); setSaved(false) }} />
    <button className="secondary" disabled={!usage || busy || limit === '' || Number(limit) < 0 || Number(limit) > 1000000}>{busy ? 'Saving…' : 'Save limit'}</button>
    {saved && <p role="status">Limit saved. New paid requests use this limit.</p>}
    {error && usage && <p className="error" role="alert">{error}</p>}
  </form>
}
