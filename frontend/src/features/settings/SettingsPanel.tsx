import { useEffect, useState } from 'react'
import type { Session } from '@supabase/supabase-js'
import { api } from '../../lib/api'

export function SettingsPanel({ session }: { session: Session }) {
  const [threshold, setThreshold] = useState('')
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    const controller = new AbortController()
    void api<{ valuable_threshold: string }>('/v1/settings', session, { signal: controller.signal })
      .then(value => {
        if (controller.signal.aborted) return
        if (value.valuable_threshold === undefined) throw new Error('Settings are unavailable.')
        setThreshold(String(value.valuable_threshold)); setSaved(String(value.valuable_threshold))
      }).catch(e => { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Could not load settings.') })
    return () => controller.abort()
  }, [session])
  const valid = threshold !== '' && Number(threshold) >= 40 && Number(threshold) <= 100
  return <form onSubmit={event => {
    event.preventDefault()
    if (!valid || busy) return
    setBusy(true); setError(null); setMessage(null)
    void api<{ valuable_threshold: string }>('/v1/settings', session, {
      method: 'PUT', body: JSON.stringify({ valuable_threshold: threshold }),
    }).then(value => {
      setThreshold(String(value.valuable_threshold)); setSaved(String(value.valuable_threshold))
      setMessage('Threshold saved. Existing assessments keep their original verdict.')
    }).catch(e => setError(e instanceof Error ? e.message : 'Could not save settings.')).finally(() => setBusy(false))
  }}>
    <p className="eyebrow">SETTINGS</p><h1>Your triage rules.</h1>
    <label htmlFor="threshold">Valuable threshold (%)</label>
    <input id="threshold" type="number" min="40" max="100" step="0.01" required value={threshold}
      disabled={saved === '' || busy} onChange={event => { setThreshold(event.target.value); setMessage(null) }} />
    <p className="hint">40–100%. Applies when a new analysis starts. Existing results stay unchanged.</p>
    <button className="primary" disabled={busy || !valid || saved === '' || threshold === saved}>{busy ? 'Saving…' : 'Save settings'}</button>
    {message && <p role="status">{message}</p>}{error && <p className="error" role="alert">{error}</p>}
  </form>
}
