import { useEffect, useRef, useState } from 'react'
import type { Session } from '@supabase/supabase-js'
import { api } from '../../lib/api'
import { criterionLabel, parseSettings, type AssessmentSettings, type RubricEntry } from '../../lib/rubric'

type DraftEntry = Omit<RubricEntry, 'weight'> & { weight: string }

export function SettingsPanel({ session }: { session: Session }) {
  return <SettingsEditor key={session.user.id} session={session} />
}

function SettingsEditor({ session }: { session: Session }) {
  const [threshold, setThreshold] = useState('')
  const [version, setVersion] = useState<1 | 2>(1)
  const [rules, setRules] = useState<DraftEntry[]>([])
  const [saved, setSaved] = useState('')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const controller = useRef<AbortController | null>(null)
  function load(value: AssessmentSettings) {
    const nextRules = value.rubric.criteria.map(c => ({ ...c, weight: String(c.weight) }))
    setVersion(value.rubric.version ?? 1)
    setThreshold(String(value.valuable_threshold)); setRules(nextRules)
    setSaved(JSON.stringify([String(value.valuable_threshold), nextRules]))
  }
  useEffect(() => {
    const current = new AbortController()
    controller.current = current
    void api<unknown>('/v1/settings', session, { signal: current.signal })
      .then(value => { if (!current.signal.aborted) load(parseSettings(value)) })
      .catch(e => { if (!current.signal.aborted) setError(e instanceof Error ? e.message : 'Could not load settings.') })
    return () => current.abort()
  }, [session])
  const valid = threshold !== '' && Number(threshold) >= 40 && Number(threshold) <= 100 &&
    rules.length === 8 && rules.every(c => /^(?:[1-9]|10)$/.test(c.weight) && c.description.trim() !== '' &&
      c.description.length <= 1000 && !c.description.includes('\0'))
  const unchanged = saved === JSON.stringify([threshold, rules])
  function edit(index: number, update: Partial<DraftEntry>) {
    setRules(previous => previous.map((c, i) => i === index ? { ...c, ...update } : c)); setMessage(null)
  }
  return <form className="settings-form" onSubmit={event => {
    event.preventDefault()
    const current = controller.current
    if (!valid || busy || !saved || unchanged || !current || current.signal.aborted) return
    setBusy(true); setError(null); setMessage(null)
    void api<unknown>('/v1/settings', session, {
      method: 'PUT', signal: current.signal, body: JSON.stringify({ valuable_threshold: threshold,
        rubric: { version, criteria: rules.map(c => ({ ...c, weight: Number(c.weight) })) },
      }),
    }).then(value => {
      if (current.signal.aborted) return
      load(parseSettings(value)); setMessage('Settings saved. Existing assessments keep their original rules and verdict.')
    }).catch(e => { if (!current.signal.aborted) setError(e instanceof Error ? e.message : 'Could not save settings.') })
      .finally(() => { if (!current.signal.aborted) setBusy(false) })
  }}>
    <p className="eyebrow">SETTINGS</p><h1>Your triage rules.</h1>
    <label htmlFor="threshold">Valuable threshold (%)</label>
    <input id="threshold" type="number" min="40" max="100" step="0.01" required value={threshold}
      disabled={!saved || busy} onChange={event => { setThreshold(event.target.value); setMessage(null) }} />
    <p className="hint">40–100%. Saved rules apply to new analyses. Existing and interrupted analyses keep their original rules.</p>
    <h2>Assessment criteria</h2>
    <p className="hint">All eight criteria are explained. Assessed criteria receive 1–5 points; unavailable verification is marked Not verified, and unrelated replicability is Not applicable. Edit descriptions and weights (1–10).</p>
    <details className="rubric-help"><summary>How scoring works</summary>
    <p className="hint">{version === 2 ? 'Result = sum(points × weight) ÷ (5 × sum(weights of scored criteria)) × 100%. Unscored criteria are excluded; no scored criteria means no percentage. Valuable requires meeting the threshold and scores of at least 3 for support, credibility, usefulness and completeness. Other results need review. Hype requires specific cited evidence of exaggeration, regardless of the total score.' : 'Historical rules: all criteria receive 1–5 points. Below 40%: hype; below the valuable threshold: to review; at or above it: valuable.'}</p>
    <p className="hint">1 means a named substantive weakness; 3 means partial fulfilment with specific gaps; 5 means strong fulfilment for the material’s purpose. 2 and 4 are intermediate. Not verified is uncertainty, not a low score. Cross-source confirmation requires a specific comparison with another supplied source.</p></details>
    {!saved && !error && <p role="status">Loading your rules…</p>}
    {rules.map((rule, index) => <fieldset className="criterion-editor" key={rule.name} disabled={busy}>
      <legend>{criterionLabel(rule.name, version)}</legend>
      <div className="criterion-fields"><div>
        <label htmlFor={`description-${rule.name}`}>Description</label>
        <textarea id={`description-${rule.name}`} aria-label={`${criterionLabel(rule.name, version)} description`} required maxLength={1000} value={rule.description}
          onChange={event => edit(index, { description: event.target.value })} />
      </div><div>
        <label htmlFor={`weight-${rule.name}`}>Weight</label>
        <input id={`weight-${rule.name}`} aria-label={`${criterionLabel(rule.name, version)} weight`} type="number" required min="1" max="10" step="1" value={rule.weight}
          onChange={event => edit(index, { weight: event.target.value })} />
        <p className="hint">Integer, 1–10</p>
      </div></div>
    </fieldset>)}
    {saved && !valid && <p className="error" role="alert">Use a threshold of 40–100%, nonblank descriptions up to 1000 characters, and integer weights of 1–10.</p>}
    <button className="primary" disabled={busy || !valid || !saved || unchanged}>{busy ? 'Saving…' : 'Save settings'}</button>
    {message && <p role="status">{message}</p>}{error && <p className="error" role="alert">{error}</p>}
  </form>
}
