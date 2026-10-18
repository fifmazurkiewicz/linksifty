import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen } from '@testing-library/react'
import { Queue } from '../src/features/queue/Queue'

afterEach(cleanup)

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
