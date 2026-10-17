import { useState } from 'react'
import type { Item } from '../../lib/api'

const stages: Record<string, string> = {
  queued: 'Waiting for processing', fetching: 'Fetching the page', checking_content: 'Checking readable content',
  searching_sources: 'Searching additional sources with Brave', checking_sources: 'Fetching and checking additional pages',
  waiting_analysis: 'Checking budget before analysis', analyzing: 'Analyzing information', saving: 'Saving your assessment',
  completed: 'Ready to read', cost_unknown: 'Waiting for the provider cost to be confirmed',
  budget_exhausted: 'Monthly budget reached', not_configured: 'Analysis is not configured',
  invalid_model_output: 'The model did not return a usable, source-backed result',
}
const reasons: Record<string, string> = {
  paywalled: 'The page requires a subscription.', login_required: 'The page requires sign-in.',
  partial_content: 'Only part of the page was available.', script_only: 'The page requires JavaScript.',
  unsupported: 'This source format is not supported.', too_large: 'The page exceeds the size limit.',
  too_short: 'Not enough readable text was available.', unsafe_url: 'The page cannot be safely fetched.',
  unavailable: 'The page could not be fetched.', blocked: 'The page blocked access.',
}
const modelReasons: Record<string, string> = {
  input_too_large: 'The source and assessment rules exceed the safe analysis size limit.',
  unknown_citation_source: 'The model cited a source that was not supplied for this analysis.',
  output_truncated: 'The model response reached the output limit.', invalid_schema: 'The response did not match the required assessment format.',
  invalid_criteria: 'The response omitted or repeated a scoring criterion.', invalid_citation: 'A quoted passage did not match its attributed source.',
  invalid_provider_response: 'The provider returned an unreadable response.', provider_rejected: 'The provider rejected the request.',
  provider_incomplete: 'The provider did not finish the response.', provider_unreachable: 'The provider could not be reached.',
}
const retryable = new Set(['budget_exhausted', 'not_configured', 'invalid_model_output', 'provider_rejected'])

export function Queue({ items, onOpen, onPaste, onResume, busy }: {
  items: Item[]; onOpen: (id: string) => void; onPaste: (id: string) => void;
  onResume: (id: string) => void; busy: boolean;
}) {
  const [filter, setFilter] = useState('All')
  const [verdict, setVerdict] = useState('all')
  const group = (item: Item) => item.status === 'completed' ? 'Ready' : ['queued', 'processing'].includes(item.status) ? 'In progress' : 'Needs action'
  const visible = items.filter(item => (filter === 'All' || group(item) === filter)
    && (verdict === 'all' || item.verdict === verdict))
  return <>
    <div className="filters" aria-label="Queue filters">
      {['All', 'In progress', 'Needs action', 'Ready'].map(value => <button key={value}
        className={filter === value ? 'active' : ''} aria-pressed={filter === value} onClick={() => setFilter(value)}>
        {value} <small>({items.filter(item => value === 'All' || group(item) === value).length})</small>
      </button>)}
    </div>
    <label className="compact-label" htmlFor="verdict-filter">Verdict</label>
    <select id="verdict-filter" value={verdict} onChange={event => setVerdict(event.target.value)}>
      <option value="all">All verdicts</option><option value="valuable">Valuable</option>
      <option value="to_review">To review</option><option value="hype">Hype</option>
    </select>
    {visible.map(item => {
      const stage = item.processing_stage === 'queued' && item.status !== 'queued' ? item.status : item.processing_stage || item.status
      const stageLabel = stages[stage] || (item.status === 'awaiting_manual_content' ? 'Paste readable content to continue' : stage.replaceAll('_', ' '))
      const paused = item.status === 'processing' && item.worker_active === false
      let host = ''
      try { host = new URL(item.original_url || item.title).hostname } catch { /* Pasted content has no URL. */ }
      return <article key={item.id} className="queue-item">
        <div>
          <p className="meta">{group(item)}</p><h2>{item.title}</h2>
          <p role={item.status === 'processing' ? 'status' : item.status === 'failed' ? 'alert' : undefined} aria-atomic="true">{paused ? 'Processing paused; waiting to resume' : stageLabel}{!paused && stage === 'fetching' && host ? ` from ${host}` : ''}.</p>
          {paused && <p>Last confirmed stage: {stageLabel}. Work resumes after the interrupted lease expires.</p>}
          {item.status === 'awaiting_manual_content' && <p>{reasons[item.failure_reason || ''] || 'The source could not be read completely.'}</p>}
          {item.updated_at && <p className="hint">Updated {new Date(item.updated_at).toLocaleTimeString()}</p>}
          {stage === 'invalid_model_output' && item.failure_reason && modelReasons[item.failure_reason] && <p>{modelReasons[item.failure_reason]}</p>}
          {stage === 'cost_unknown' && <p>The amount remains reserved. This paid request will not be repeated.</p>}
          {stage === 'budget_exhausted' && <p>Ask an administrator to raise your limit, or resume after the monthly reset.</p>}
        </div>
        <div className="item-actions">
          {item.status === 'completed' && <><strong>{item.score === null ? 'Not scored' : `${item.score}%`}</strong><small>{item.verdict?.replaceAll('_', ' ')}</small><button className="secondary" onClick={() => onOpen(item.id)}>Read assessment</button></>}
          {item.status === 'awaiting_manual_content' && <button className="secondary" disabled={busy} onClick={() => onPaste(item.id)}>Paste content</button>}
          {item.status === 'failed' && retryable.has(stage) && <button className="secondary" disabled={busy} onClick={() => onResume(item.id)}>Resume analysis</button>}
          {item.status === 'failed' && retryable.has(stage) && <small>Uses your monthly budget.</small>}
        </div>
      </article>
    })}
    {visible.length === 0 && <p className="empty-state">{items.length ? 'No links match these filters.' : 'Your queue is empty. Add a link or paste an article to get started.'}</p>}
  </>
}
