import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { Queue } from '../src/features/queue/Queue'

afterEach(cleanup)

it.each(['x_not_configured', 'unsupported', 'unavailable', 'x_access_denied'])('retries %s only on request and disables retry while busy', (reason) => {
  const resume = vi.fn()
  const props = { items: [{ id: 'retry-me', title: 'Unread source', status: 'awaiting_manual_content',
    score: null, verdict: null, failure_reason: reason }], onOpen: vi.fn(), onPaste: vi.fn(),
    onResume: resume, onDelete: vi.fn().mockResolvedValue(true) }
  const { rerender } = render(<Queue {...props} busy={false} />)
  expect(resume).not.toHaveBeenCalled()
  expect(screen.getByRole('button', { name: 'Paste content' })).toBeEnabled()
  fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
  expect(resume).toHaveBeenCalledExactlyOnceWith('retry-me')
  rerender(<Queue {...props} busy />)
  expect(screen.getByRole('button', { name: 'Retry' })).toBeDisabled()
  fireEvent.click(screen.getByRole('button', { name: 'Retry' }))
  expect(resume).toHaveBeenCalledTimes(1)
})

it('does not offer retry for an uncertain X attempt', () => {
  render(<Queue items={[{ id: 'uncertain', title: 'Interrupted X read', status: 'awaiting_manual_content',
    score: null, verdict: null, failure_reason: 'x_attempt_uncertain' }]} onOpen={vi.fn()} onPaste={vi.fn()}
    onResume={vi.fn()} onDelete={vi.fn()} busy={false} />)
  expect(screen.queryByRole('button', { name: 'Retry' })).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Paste content' })).toBeEnabled()
})

it('shows truthful waiting copy and no ready assessment for a queued link', () => {
  render(<Queue items={[{ id: 'one', title: 'https://example.com/article', status: 'queued',
    score: null, verdict: null, processing_stage: 'queued' }]} onOpen={vi.fn()} onPaste={vi.fn()} onResume={vi.fn()} onDelete={vi.fn().mockResolvedValue(true)} busy={false} />)
  expect(screen.getByText(/waiting for processing/i)).toBeInTheDocument()
  expect(screen.queryByText(/assessment is ready/i)).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: /paste content/i })).not.toBeInTheDocument()
})

it('filters actionable links and offers pasted content only for fetch failure', () => {
  const paste = vi.fn()
  render(<Queue items={[
    { id: 'one', title: 'Ready article', status: 'completed', score: 80, verdict: 'valuable' },
    { id: 'two', title: 'Blocked article', status: 'awaiting_manual_content', score: null, verdict: null, failure_reason: 'paywalled' },
  ]} onOpen={vi.fn()} onPaste={paste} onResume={vi.fn()} onDelete={vi.fn().mockResolvedValue(true)} busy={false} />)
  fireEvent.click(screen.getByRole('button', { name: /needs action/i }))
  expect(screen.queryByText('Ready article')).not.toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: /paste content/i }))
  expect(paste).toHaveBeenCalledWith('two')
})

it.each([
  ['x_not_configured', /automatic X fetching is not enabled/i],
  ['x_access_denied', /X denied API access/i],
  ['x_not_found', /X could not return this post/i],
  ['x_rate_limited', /X has reached its API rate limit/i],
  ['x_attempt_uncertain', /earlier X fetch was interrupted/i],
])('explains %s and offers paste without an automatic paid retry', (reason, message) => {
  const paste = vi.fn()
  render(<Queue items={[{ id: 'x-post', title: 'X thread', status: 'awaiting_manual_content',
    score: null, verdict: null, failure_reason: reason }]} onOpen={vi.fn()} onPaste={paste}
    onResume={vi.fn()} onDelete={vi.fn().mockResolvedValue(true)} busy={false} />)
  expect(screen.getByText(message)).toBeInTheDocument()
  expect(screen.queryByRole('button', { name: /resume analysis/i })).not.toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: /paste content/i }))
  expect(paste).toHaveBeenCalledWith('x-post')
})

it('labels a stale worker as paused instead of claiming active analysis', () => {
  render(<Queue items={[{ id: 'stale', title: 'Interrupted article', status: 'processing',
    score: null, verdict: null, processing_stage: 'analyzing', worker_active: false }]} onOpen={vi.fn()} onPaste={vi.fn()} onResume={vi.fn()} onDelete={vi.fn().mockResolvedValue(true)} busy={false} />)
  expect(screen.getByText(/processing paused/i)).toBeInTheDocument()
  expect(screen.getByText(/last confirmed stage: analyzing information/i)).toBeInTheDocument()
})

it('offers explicit paid resume after a budget block but never for an unknown call', () => {
  const resume = vi.fn()
  render(<Queue items={[
    { id: 'cap', title: 'Budget blocked article', status: 'failed', processing_stage: 'budget_exhausted', score: null, verdict: null },
    { id: 'unknown', title: 'Unconfirmed call', status: 'failed', processing_stage: 'cost_unknown', score: null, verdict: null },
  ]} onOpen={vi.fn()} onPaste={vi.fn()} onResume={resume} onDelete={vi.fn().mockResolvedValue(true)} busy={false} />)
  expect(screen.getAllByRole('button', { name: 'Resume analysis' })).toHaveLength(1)
  expect(screen.getByText('Uses your monthly budget.')).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Resume analysis' }))
  expect(resume).toHaveBeenCalledWith('cap')
  expect(screen.getByText(/paid request will not be repeated/i)).toBeInTheDocument()
})

it('explains rich X failures and never retries uncertain image reading', () => {
  render(<Queue items={[
    { id: 'article', title: 'Missing article body', status: 'awaiting_manual_content', failure_reason: 'x_article_incomplete', score: null, verdict: null },
    { id: 'media', title: 'Unreadable media', status: 'awaiting_manual_content', failure_reason: 'image_reading_failed', score: null, verdict: null },
    { id: 'uncertain-image', title: 'Unknown image cost', status: 'awaiting_manual_content', failure_reason: 'image_reading_uncertain', score: null, verdict: null },
  ]} onOpen={vi.fn()} onPaste={vi.fn()} onResume={vi.fn()} onDelete={vi.fn()} busy={false} />)
  expect(screen.getByText(/X Article could not be read completely.*missing or unsupported content/i)).toBeInTheDocument()
  expect(screen.getByText(/attached images could not be read completely/i)).toBeInTheDocument()
  expect(screen.getByText(/image-reading charge is not confirmed/i)).toBeInTheDocument()
  expect(screen.getAllByRole('button', { name: 'Retry' })).toHaveLength(2)
  expect(screen.getAllByText(/reads attached images.*monthly budget/i)).toHaveLength(2)
})
