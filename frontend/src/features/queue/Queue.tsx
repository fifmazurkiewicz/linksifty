import { useState } from 'react'
import type { Item } from '../../lib/api'

const stages: Record<string, string> = {
  queued: 'Waiting for processing', fetching: 'Fetching the page', checking_content: 'Checking readable content',
  searching_sources: 'Searching additional sources with Brave', checking_sources: 'Fetching and checking additional pages',
  waiting_analysis: 'Checking budget before analysis', analyzing: 'Analyzing information', saving: 'Saving your assessment',
  completed: 'Ready to read', cost_unknown: 'Waiting for the provider cost to be confirmed',
  waiting_image_budget: 'Checking budget before reading images', reading_images: 'Reading attached images and diagrams',
  budget_exhausted: 'Monthly budget reached', not_configured: 'Analysis is not configured',
  invalid_model_output: 'The model did not return a usable, source-backed result',
}
const reasons: Record<string, string> = {
  paywalled: 'The page requires a subscription.', login_required: 'The page requires sign-in.',
  partial_content: 'Only part of the page was available.', script_only: 'The page requires JavaScript.',
  unsupported: 'This source format is not supported.', too_large: 'The page exceeds the size limit.',
  too_short: 'Not enough readable text was available.', unsafe_url: 'The page cannot be safely fetched.',
  unavailable: 'The page could not be fetched.', blocked: 'The page blocked access.',
  x_not_configured: 'Automatic X fetching is not enabled. Paste the post or full thread to continue.',
  x_access_denied: 'X denied API access. The server token, credits, or full-archive search access may need attention.',
  x_not_found: 'X could not return this post. It may be deleted or unavailable to the API.',
  x_rate_limited: 'X has reached its API rate limit. Paste the full thread to continue.',
  x_attempt_uncertain: 'An earlier X fetch was interrupted. Paste the full thread to avoid repeating potentially billed reads.',
  x_article_incomplete: 'The X Article could not be read completely because of missing or unsupported content. Paste the complete article, including code and relevant image text.',
  x_media_unsupported: 'This source includes video, animation, a poll or another unsupported attachment. Paste its complete readable content.',
  x_media_unavailable: 'A required image could not be downloaded or validated. Paste the complete source, including image text.',
  image_reading_failed: 'The attached images could not be read completely. Paste the source text and all relevant image or diagram content.',
  image_reading_uncertain: 'An earlier image-reading charge is not confirmed. Funds remain reserved; paste complete content to continue without repeating that call.',
  image_reading_not_configured: 'Image reading is not configured for the selected model. Paste the source and relevant image text.',
  image_budget_exhausted: 'Your monthly budget cannot cover image reading. Increase the budget or paste complete readable content.',
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

export function Queue({ items, onOpen, onPaste, onResume, onDelete, busy }: {
  items: Item[]; onOpen: (id: string) => void; onPaste: (id: string) => void;
  onResume: (id: string) => void; onDelete: (ids: string[]) => Promise<boolean>; busy: boolean;
}) {
  const [filter, setFilter] = useState('All')
  const [verdict, setVerdict] = useState('all')
  const [selected, setSelected] = useState<string[]>([])
  const [deletedCount, setDeletedCount] = useState(0)
  const group = (item: Item) => item.status === 'completed' ? 'Ready' : ['queued', 'processing'].includes(item.status) ? 'In progress' : 'Needs action'
  const visible = items.filter(item => (filter === 'All' || group(item) === filter)
    && (verdict === 'all' || item.verdict === verdict))
  const selectedIds = visible.filter(item => selected.includes(item.id)).map(item => item.id)
  const remove = async (ids: string[]) => {
    if (busy || ids.length === 0) return
    const titles = visible.filter(item => ids.includes(item.id)).map(item => item.title)
    if (!window.confirm(`Permanently delete ${ids.length} ${ids.length === 1 ? 'link' : 'links'} and all related analyses, source text, citations and chats?\n\n${titles.slice(0, 3).join('\n')}${titles.length > 3 ? `\n…and ${titles.length - 3} more` : ''}\n\nThis cannot be undone. Existing charges and unresolved billing records remain.`)) return
    setDeletedCount(0)
    if (await onDelete(ids)) {
      setSelected(current => current.filter(id => !ids.includes(id)))
      setDeletedCount(ids.length)
    }
  }
  return <>
    <div className="filters" aria-label="Queue filters">
      {['All', 'In progress', 'Needs action', 'Ready'].map(value => <button key={value}
        className={filter === value ? 'active' : ''} aria-pressed={filter === value} onClick={() => { setFilter(value); setSelected([]) }}>
        {value} <small>({items.filter(item => value === 'All' || group(item) === value).length})</small>
      </button>)}
    </div>
    <label className="compact-label" htmlFor="verdict-filter">Verdict</label>
    <select id="verdict-filter" value={verdict} onChange={event => { setVerdict(event.target.value); setSelected([]) }}>
      <option value="all">All verdicts</option><option value="valuable">Valuable</option>
      <option value="to_review">To review</option><option value="hype">Hype</option>
    </select>
    {visible.length > 0 && <div className="queue-selection">
      <label><input type="checkbox" checked={selectedIds.length === visible.length} disabled={busy}
        onChange={event => setSelected(event.target.checked ? visible.map(item => item.id) : [])} /> Select all visible links</label>
      <button className="secondary delete-button" disabled={busy || selectedIds.length === 0}
        onClick={() => void remove(selectedIds)}>Delete selected ({selectedIds.length})</button>
    </div>}
    {deletedCount > 0 && <p role="status">Deleted {deletedCount} {deletedCount === 1 ? 'link' : 'links'}.</p>}
    {busy && <p role="status">Updating your queue…</p>}
    {visible.map(item => {
      const stage = item.processing_stage === 'queued' && item.status !== 'queued' ? item.status : item.processing_stage || item.status
      const stageLabel = stages[stage] || (item.status === 'awaiting_manual_content' ? 'Paste readable content to continue' : stage.replaceAll('_', ' '))
      const paused = item.status === 'processing' && item.worker_active === false
      const uncertainFetch = ['x_attempt_uncertain', 'image_reading_uncertain'].includes(item.failure_reason || '') || ['x_attempt_uncertain', 'image_reading_uncertain'].includes(stage)
      const canRetryFetch = item.status === 'awaiting_manual_content' && !uncertainFetch
      let host = ''
      try { host = new URL(item.original_url || item.title).hostname } catch { /* Pasted content has no URL. */ }
      return <article key={item.id} className="queue-item">
        <div>
          <label className="item-selection"><input type="checkbox" aria-label={`Select ${item.title}`}
            checked={selectedIds.includes(item.id)} disabled={busy}
            onChange={event => setSelected(current => event.target.checked ? [...current, item.id] : current.filter(id => id !== item.id))} /> Select</label>
          <p className="meta">{group(item)}</p><h2>{item.title}</h2>
          <p role={item.status === 'processing' ? 'status' : item.status === 'failed' ? 'alert' : undefined} aria-atomic="true">{paused ? 'Processing paused; waiting to resume' : stageLabel}{!paused && stage === 'fetching' && host ? ` from ${host}` : ''}.</p>
          {paused && <p>Last confirmed stage: {stageLabel}. Work resumes after the interrupted lease expires.</p>}
          {item.status === 'awaiting_manual_content' && <p>{reasons[item.failure_reason || ''] || 'The source could not be read completely.'}</p>}
          {canRetryFetch && <p className="hint" id={`retry-cost-${item.id}`}>Retry fetches the source again, reads attached images and starts analysis using your monthly budget. X reads may incur separate charges.</p>}
          {item.updated_at && <p className="hint">Updated {new Date(item.updated_at).toLocaleTimeString()}</p>}
          {stage === 'invalid_model_output' && item.failure_reason && modelReasons[item.failure_reason] && <p>{modelReasons[item.failure_reason]}</p>}
          {stage === 'cost_unknown' && <p>The amount remains reserved. This paid request will not be repeated.</p>}
          {stage === 'budget_exhausted' && <p>Ask an administrator to raise your limit, or resume after the monthly reset.</p>}
        </div>
        <div className="item-actions">
          {item.status === 'completed' && <><strong>{item.score === null ? 'Not scored' : `${item.score}%`}</strong><small>{item.verdict?.replaceAll('_', ' ')}</small><button className="secondary" onClick={() => onOpen(item.id)}>Read assessment</button></>}
          {canRetryFetch && <button className="secondary" disabled={busy} aria-describedby={`retry-cost-${item.id}`} onClick={() => onResume(item.id)}>Retry</button>}
          {item.status === 'awaiting_manual_content' && <button className="secondary" disabled={busy} onClick={() => onPaste(item.id)}>Paste content</button>}
          {item.status === 'failed' && retryable.has(stage) && <button className="secondary" disabled={busy} onClick={() => onResume(item.id)}>Resume analysis</button>}
          {item.status === 'failed' && retryable.has(stage) && <small>Uses your monthly budget.</small>}
          <button className="secondary delete-button" aria-label={`Delete ${item.title}`} disabled={busy}
            onClick={() => void remove([item.id])}>Delete</button>
        </div>
      </article>
    })}
    {visible.length === 0 && <p className="empty-state">{items.length ? 'No links match these filters.' : 'Your queue is empty. Add a link or paste an article to get started.'}</p>}
  </>
}
