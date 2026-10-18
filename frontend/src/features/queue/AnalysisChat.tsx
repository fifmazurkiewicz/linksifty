import { useEffect, useRef, useState } from 'react'
import type { Session } from '@supabase/supabase-js'
import { api, money } from '../../lib/api'

type Citation = { passage_id: string; excerpt: string; source_url: string | null; label: string }
type Turn = {
  id: string; question: string; status: 'pending' | 'completed' | 'failed'
  answer: { text: string; citations: Citation[] }[]
  insufficient: boolean; search_status: string; error: string | null
}
type History = { turns: Turn[]; available: boolean; search_available: boolean; search_price_usd: string | null }

function safeSource(value: string | null): string | null {
  try {
    const url = new URL(value ?? '')
    return ['https:', 'http:'].includes(url.protocol) ? url.href : null
  } catch { return null }
}

function failureMessage(reason: string | null): string {
  if (reason === 'budget_exhausted') return 'Your monthly budget has insufficient available funds. Your question is saved.'
  if (reason === 'interrupted') return 'This answer was interrupted. No request was automatically repeated. You can submit the question again; uncertain charges remain reserved.'
  if (reason === 'invalid_evidence' || reason === 'invalid_answer') return 'The answer could not be verified against its sources. You can submit the question again.'
  if (reason === 'input_too_large') return 'This conversation is too large to answer safely. Try a shorter, more specific question.'
  return 'The answer could not be completed. You can submit the question again; any uncertain charge remains reserved.'
}

export function AnalysisChat({ id, session }: { id: string; session: Session }) {
  const [history, setHistory] = useState<History | null>(null)
  const [draft, setDraft] = useState('')
  const [loading, setLoading] = useState(true)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [refresh, setRefresh] = useState(0)
  const request = useRef<{ question: string; id: string } | null>(null)
  const controller = useRef<AbortController | null>(null)
  const inFlight = useRef(false)
  const active = useRef(true)
  const pending = history?.turns.some(turn => turn.status === 'pending') ?? false
  const busy = sending || pending
  const endpoint = `/v1/items/${id}/chat`

  useEffect(() => {
    active.current = true
    return () => { active.current = false; controller.current?.abort() }
  }, [])

  useEffect(() => {
    const abort = new AbortController()
    let timer: ReturnType<typeof setTimeout> | undefined
    async function load() {
      try {
        const result = await api<History>(endpoint, session, { signal: abort.signal })
        if (abort.signal.aborted) return
        if (!Array.isArray(result.turns)) throw new Error('Could not load chat history.')
        setHistory(result)
        setError(null)
        const current = request.current
        if (current && result.turns.some(turn => turn.id === current.id && turn.status === 'completed')) {
          setDraft(value => value.trim() === current.question ? '' : value)
          request.current = null
        }
        if (current && result.turns.some(turn => turn.id === current.id && turn.status === 'failed')) request.current = null
        if (result.turns.some(turn => turn.status === 'pending')) timer = setTimeout(() => { void load() }, 2000)
      } catch (failure) {
        if (!abort.signal.aborted) setError(failure instanceof Error ? failure.message : 'Could not load chat history.')
      } finally {
        if (!abort.signal.aborted) setLoading(false)
      }
    }
    void load()
    return () => { abort.abort(); clearTimeout(timer) }
  }, [endpoint, session, refresh])

  async function send() {
    const question = draft.trim()
    if (!question || busy || inFlight.current || !history?.available) return
    inFlight.current = true
    setSending(true)
    setError(null)
    // Keep the UUID after network uncertainty. Repeating it only reads saved work.
    if (!request.current || request.current.question !== question) request.current = { question, id: crypto.randomUUID() }
    const submitted = request.current
    const abort = new AbortController()
    controller.current = abort
    try {
      const turn = await api<Turn>(endpoint, session, {
        method: 'POST', signal: abort.signal,
        body: JSON.stringify({ request_id: submitted.id, question }),
      })
      if (!active.current || abort.signal.aborted) return
      setHistory(value => value && ({ ...value, turns: [...value.turns.filter(t => t.id !== turn.id), turn] }))
      if (turn.status === 'completed') { setDraft(''); request.current = null }
      else if (turn.status === 'failed') request.current = null
      else setRefresh(value => value + 1)
    } catch (failure) {
      if (active.current && !abort.signal.aborted) setError(`${failure instanceof Error ? failure.message : 'Could not send your question.'} Sending the same question again checks the original request.`)
    } finally {
      inFlight.current = false
      if (active.current && !abort.signal.aborted) setSending(false)
    }
  }

  return <section className="analysis-chat" aria-labelledby="analysis-chat-title">
    <h2 id="analysis-chat-title">Chat about this analysis</h2>
    <p className="hint" id="chat-disclosure">Ask about the analysis or investigate its topic. Uses your saved sources first; searches the web only when needed, at most once per question. Answers use your monthly AI budget.
      {history?.search_available && history.search_price_usd && <> A search sends a short public-topic query to Brave and costs {money(history.search_price_usd)}; AI charges apply separately.</>}
      {history && !history.search_available && <> Web search is currently unavailable; answers use saved material.</>}
    </p>
    {loading && <p role="status">Loading your conversation…</p>}
    {error && <div className="error" role="alert"><p>{error}</p><button type="button" className="secondary" onClick={() => setRefresh(value => value + 1)}>Reload chat</button></div>}
    {history && <div className="chat-history" aria-label="Conversation">
      {history.turns.length === 0 && <p className="hint">Try “Why this verdict?” or ask a follow-up about the topic.</p>}
      {history.turns.length >= 100 && <p className="hint">Showing the latest 100 questions. Answers use relevant excerpts and recent conversation.</p>}
      {history.turns.map(turn => <div className="chat-turn" key={turn.id}>
        <div className="chat-question"><strong>You</strong><p>{turn.question}</p></div>
        {turn.status === 'completed' && <div className="chat-answer">
          <strong>Linksifty</strong>
          {turn.answer.map((paragraph, i) => <div key={i}>
            <p>{paragraph.text}</p>
            {paragraph.citations.map((citation, j) => {
              const source = safeSource(citation.source_url)
              return <details className="assessment-evidence" key={`${citation.passage_id}-${j}`}>
                <summary>{citation.label} {j + 1}</summary>
                <blockquote><p>{citation.excerpt}</p>{source && <a href={source} target="_blank" rel="noopener noreferrer">Open source ↗</a>}</blockquote>
              </details>
            })}
          </div>)}
          {turn.insufficient && <p className="hint">There is not enough verified evidence to fully answer this question.</p>}
          {turn.search_status === 'ready' && <p className="chat-research-note">One web search · fetched source excerpts checked</p>}
          {turn.search_status === 'no_sources' && <p className="chat-research-note">One web search found no new readable sources. This answer uses saved evidence.</p>}
          {turn.search_status === 'uncertain' && <p className="chat-research-note">The search outcome is uncertain; it was not repeated. This answer uses saved evidence.</p>}
          {turn.search_status === 'budget_exhausted' && <p className="chat-research-note">Web research was blocked by your available budget.</p>}
        </div>}
        {turn.status === 'failed' && <p className="error">{failureMessage(turn.error)}</p>}
      </div>)}
    </div>}
    {busy && <p role="status" aria-live="polite">Preparing your answer and checking sources when needed…</p>}
    {history && !history.available && <p className="hint">Chat is unavailable until the model provider is configured.</p>}
    <form onSubmit={event => { event.preventDefault(); void send() }}>
      <label htmlFor="chat-question">Your question</label>
      <textarea id="chat-question" rows={3} maxLength={4000} value={draft}
        disabled={loading || busy || !history?.available} aria-describedby="chat-disclosure chat-keyboard"
        onChange={event => setDraft(event.target.value)}
        onKeyDown={event => { if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) { event.preventDefault(); void send() } }} />
      <div className="chat-actions"><small id="chat-keyboard">Ctrl/Cmd + Enter to send</small>
        <button type="submit" disabled={loading || busy || !history?.available || !draft.trim()}>{busy ? 'Working…' : 'Send question'}</button>
      </div>
    </form>
  </section>
}
