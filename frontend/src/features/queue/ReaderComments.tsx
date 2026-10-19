import { useEffect, useRef, useState } from 'react'
import type { Session } from '@supabase/supabase-js'
import { api } from '../../lib/api'
import './ReaderComments.css'

type Reply = { id: string; author_id: string; username: string | null; text: string; truncated: boolean; has_media: boolean }
type Discussion = { source_id: string; url: string; platform: 'x' | 'reddit'; status: 'not_requested' | 'fetching' | 'ready' | 'unavailable' | 'unsupported'; replies: Reply[] }
type History = { available: boolean; sources: Discussion[] }

function sourceUrl(value: string): URL | null {
  try {
    const url = new URL(value)
    return ['http:', 'https:'].includes(url.protocol) && !url.username && !url.password
      && ['x.com', 'www.x.com', 'mobile.x.com', 'twitter.com', 'www.twitter.com', 'mobile.twitter.com', 'm.twitter.com', 'reddit.com', 'www.reddit.com', 'old.reddit.com', 'new.reddit.com'].includes(url.hostname)
      ? url : null
  } catch { return null }
}

export function ReaderComments({ id, session }: { id: string; session: Session }) {
  const [history, setHistory] = useState<History | null>(null)
  const [checking, setChecking] = useState(false)
  const [busy, setBusy] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [notice, setNotice] = useState('')
  const status = useRef<HTMLParagraphElement | null>(null)
  const controller = useRef<AbortController | null>(null)
  const inFlight = useRef(false)
  const endpoint = `/v1/items/${id}/discussions`
  useEffect(() => () => { controller.current?.abort() }, [])

  async function refresh() {
    if (inFlight.current) return
    inFlight.current = true
    const abort = new AbortController()
    controller.current = abort
    setChecking(true)
    setError(null)
    setNotice('')
    try {
      const result = await api<History>(endpoint, session, { signal: abort.signal })
      if (!abort.signal.aborted) setHistory(result)
    } catch {
      if (!abort.signal.aborted) setError('Could not read saved comments. Check saved results to try again.')
    } finally {
      inFlight.current = false
      if (!abort.signal.aborted) setChecking(false)
    }
  }

  async function load(source: Discussion) {
    if (inFlight.current) return
    inFlight.current = true
    const abort = new AbortController()
    controller.current = abort
    setBusy(source.source_id)
    setError(null)
    setNotice('')
    try {
      const result = await api<Discussion>(endpoint, session, {
        method: 'POST', signal: abort.signal,
        body: JSON.stringify({ source_id: source.source_id, consent: true }),
      })
      if (!abort.signal.aborted) {
        setHistory(value => value && ({ ...value, sources: value.sources.map(s => s.source_id === source.source_id ? result : s) }))
        setNotice(result.status === 'ready' ? `${result.replies.length} reader ${result.replies.length === 1 ? 'reply' : 'replies'} saved.` : 'Reply request finished. See the saved status below.')
        status.current?.focus()
      }
    } catch {
      if (!abort.signal.aborted) {
        setHistory(value => value && ({ ...value, sources: value.sources.map(s => s.source_id === source.source_id ? { ...s, status: 'fetching' } : s) }))
        setError('Could not load replies. Check saved results to read the saved attempt.')
      }
    } finally {
      inFlight.current = false
      if (!abort.signal.aborted) setBusy(null)
    }
  }

  const sources = history?.sources.flatMap(source => {
    const url = sourceUrl(source.url)
    return url ? [{ ...source, url }] : []
  }) ?? []

  return <details className="assessment-panel reader-comments" onToggle={event => {
    if (event.currentTarget.open && !history && !checking && !error) void refresh()
  }}>
    <summary><h2>Reader comments</h2><span className="panel-status">X and Reddit availability</span></summary>
    <div className="assessment-panel-body assessment-research">
      <p>X may charge separately when you select Load X replies. Each post gets one saved attempt: up to two API reads and twenty replies. Opening this panel reads saved results only.</p>
      <p className="hint">Replies are a limited snapshot of reader opinions and stay separate from your assessment. Media in replies is not analyzed.</p>
      <p ref={status} role="status" tabIndex={-1} hidden={!checking && busy === null && !notice}>
        {checking ? 'Reading saved comments…' : busy !== null ? 'Fetching reader replies…' : notice}
      </p>
      {error && <p role="alert" className="error">{error}</p>}
      {history && sources.length === 0 && <p>No X or Reddit discussions are available for this analysis.</p>}
      {sources.map(source => <article className="assessment-criterion" key={source.source_id}>
        <div className="criterion-heading"><h3>{source.source_id === 'primary' ? 'Submitted link' : 'Search result'} · {source.platform === 'reddit' ? 'Reddit' : 'X'}</h3></div>
        <p><a href={source.url.href} target="_blank" rel="noopener noreferrer">{source.url.hostname}{source.url.pathname}</a></p>
        {busy === source.source_id ? null
          : source.status === 'unsupported' ? <p>Reddit comments are not supported.</p>
            : source.status === 'fetching' ? <p>A reply request is running or its outcome is unknown. Check saved results; this request will not be repeated.</p>
              : source.status === 'unavailable' ? <p>Replies could not be retrieved. This attempt is saved and will not be retried automatically.</p>
                : source.status === 'not_requested' ? history?.available
                  ? <button className="secondary" disabled={checking || busy !== null} onClick={() => { void load({ ...source, url: source.url.href }) }}>Load X replies</button>
                  : <p>X replies are not configured.</p>
                  : source.replies.length === 0 ? <p>X returned no replies in this sample.</p>
                    : <ol>{source.replies.map(reply => <li key={reply.id}>
                      <strong>{reply.username ? `@${reply.username}` : `X user ${reply.author_id}`}</strong>
                      <p>{reply.text}</p>
                      {reply.truncated && <p className="hint">Reply text is truncated.</p>}
                      {reply.has_media && <p className="hint">Reply includes media; only its text is shown.</p>}
                      {/^[0-9]{1,19}$/.test(reply.id) && <a href={`https://x.com/i/web/status/${reply.id}`} target="_blank" rel="noopener noreferrer">Open reply on X ↗</a>}
                    </li>)}</ol>}
      </article>)}
      {(history || error) && <button className="secondary" disabled={checking || busy !== null} onClick={() => { void refresh() }}>Check saved results</button>}
    </div>
  </details>
}
