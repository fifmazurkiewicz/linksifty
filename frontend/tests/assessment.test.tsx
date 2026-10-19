import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import type { Session } from '@supabase/supabase-js'
import { rubric } from './rubric-fixture'
import { AssessmentDetail } from '../src/features/queue/AssessmentDetail'

const names = ['novelty', 'evidence', 'practicality', 'source_credibility', 'replicability', 'independent_corroboration', 'absence_of_conflict_of_interest', 'concreteness']
const session = { access_token: 'test-token', user: { id: 'reader' } } as Session
const saved = {
  rubric_snapshot: { ...rubric, version: 2 }, note: 'A practical, source-grounded note.', score: 75,
  verdict: 'valuable', threshold_snapshot: 60, verdict_reason: 'The key claims are sufficiently supported.',
  research_status: 'ready', research_sources: [{ id: 'source-1', url: 'https://example.test/comparison' }],
  criteria: names.map((name, i) => ({ name, score: 4, rationale: `Rationale ${i}`, citation_ids: [`citation-${i}`] })),
  citations: names.map((_name, i) => ({ id: `citation-${i}`, excerpt: `Supporting source passage ${i}`, source_url: 'https://example.test/article' })),
}

afterEach(() => { cleanup(); vi.restoreAllMocks() })

it('keeps the summary visible and reveals analysis, exact evidence and rules independently', async () => {
  const value = { ...saved, rubric_snapshot: { ...saved.rubric_snapshot, criteria: rubric.criteria.map(c => c.name === 'novelty' ? { ...c, description: 'Original historical rule', weight: 9 } : c) } }
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(value)))
  render(<AssessmentDetail id="saved" item={{ title: 'Understanding IKE', original_url: 'https://example.test/article' }} session={session} onBack={vi.fn()} />)
  expect(await screen.findByText(saved.note)).toBeVisible()
  expect(screen.getByRole('heading', { level: 1, name: 'Understanding IKE' })).toBeVisible()
  expect(screen.getByText('Valuable')).toBeVisible()
  expect(screen.getByText('75%')).toBeVisible()
  expect(screen.getByText(saved.verdict_reason)).toBeVisible()
  const analysis = screen.getByText('Analysis').closest('summary')!
  const sources = screen.getByText('Source checking').closest('summary')!
  expect(analysis.parentElement).not.toHaveAttribute('open')
  expect(sources.parentElement).not.toHaveAttribute('open')
  expect(screen.getByText('Rationale 0')).not.toBeVisible()
  fireEvent.click(analysis)
  expect(screen.getByText('Rationale 0')).toBeVisible()
  expect(screen.getAllByRole('heading', { level: 3 })).toHaveLength(8)
  expect(screen.getByText('Supporting source passage 0')).not.toBeVisible()
  const criterion = screen.getByText('Rationale 0').closest('article')!
  fireEvent.click(within(criterion).getByText(/Source passage 1/))
  expect(within(criterion).getByText('Supporting source passage 0')).toBeVisible()
  expect(within(criterion).getByRole('link', { name: /Open original source/ })).toHaveAttribute('rel', 'noopener noreferrer')
  expect(screen.getByText('Original historical rule')).not.toBeVisible()
  fireEvent.click(within(criterion).getByText('Scoring rules'))
  expect(screen.getByText('Original historical rule')).toBeVisible()
  expect(screen.getByText('Weight at analysis: ×9')).toBeVisible()
  fireEvent.click(sources)
  expect(analysis.parentElement).toHaveAttribute('open')
  expect(screen.getByRole('link', { name: 'example.test' })).toHaveAttribute('href', 'https://example.test/comparison')
  fireEvent.click(analysis)
  expect(screen.getByText('Rationale 0')).not.toBeVisible()
  expect(sources.parentElement).toHaveAttribute('open')
  expect(screen.getByText(saved.note)).toBeVisible()
})

it('shows unscored criteria and coverage without fake zero scores', async () => {
  const value = { ...saved, note: 'Calibrated result', score: null, verdict: 'to_review',
    verdict_reason: 'Key evidence is unverified.', hype_signals: [],
    criteria: names.map(name => ({ name, score: null, status: name === 'replicability' ? 'not_applicable' : 'not_verified', rationale: 'Not established', citation_ids: ['c1'] })),
    citations: [{ id: 'c1', excerpt: 'The material inspected.', source_url: null }],
  }
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(value)))
  render(<AssessmentDetail id="new" session={session} onBack={vi.fn()} />)
  expect(await screen.findByText('Calibrated result')).toBeVisible()
  expect(screen.getByText('To review')).toBeVisible()
  expect(screen.getByText('Not scored')).toBeVisible()
  expect(screen.getByText(/0 of 8 criteria scored/)).toBeVisible()
  fireEvent.click(screen.getByText('Analysis'))
  expect(screen.getByRole('heading', { name: 'Replicability' }).closest('article')).toHaveTextContent('Not applicable')
  expect(screen.getByRole('heading', { name: 'Learning value' }).closest('article')).toHaveTextContent('Not verified')
  expect(screen.getByText('Key evidence is unverified.')).toBeVisible()
  expect(screen.queryByText(/null%|null\/5|0\/5/)).not.toBeInTheDocument()
})

it('keeps hype warnings visible and reveals their exact source evidence inline', async () => {
  const value = { ...saved, note: 'Hype result', score: 30, verdict: 'hype',
    hype_signals: [{ rationale: 'Promises guaranteed results without support.', citation_ids: ['h1'] }],
    criteria: [], citations: [{ id: 'h1', excerpt: 'Guaranteed success!', source_url: 'https://example.test' }],
  }
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(value)))
  render(<AssessmentDetail id="hype" session={session} onBack={vi.fn()} />)
  expect(await screen.findByText('Promises guaranteed results without support.')).toBeVisible()
  expect(screen.getByText('Guaranteed success!')).not.toBeVisible()
  fireEvent.click(screen.getByText(/Hype evidence 1/))
  expect(screen.getByText('Guaranteed success!')).toBeVisible()
})

it.each([
  ['ready', '1 page fetched', /presence alone does not/],
  ['uncertain', 'Research outcome uncertain', /charge remains reserved/],
  ['failed', 'Sources not verified', /could not be verified/],
  ['not_requested', 'Primary source only', /independent sources were not searched/],
])('keeps %s research status visible and explains its limitations when opened', async (status, label, explanation) => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ ...saved, research_status: status })))
  render(<AssessmentDetail id="research" session={session} onBack={vi.fn()} />)
  await screen.findByText(saved.note)
  expect(screen.getByText(label)).toBeVisible()
  fireEvent.click(screen.getByText('Source checking'))
  expect(screen.getByText(explanation)).toBeVisible()
})

it('preserves legacy rules and prevents unsafe source links', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ ...saved,
    rubric_snapshot: rubric,
    research_sources: [{ id: 'bad', url: 'javascript:alert(1)' }, { id: 'invalid', url: 'https://' }],
    citations: saved.citations.map(c => ({ ...c, source_url: 'javascript:alert(1)' })),
  })))
  render(<AssessmentDetail id="legacy" item={{ title: 'Pasted article', original_url: 'javascript:alert(1)' }} session={session} onBack={vi.fn()} />)
  await screen.findByText(saved.note)
  fireEvent.click(screen.getByText('Analysis'))
  expect(screen.getByText(/Historical assessment/)).toBeVisible()
  fireEvent.click(screen.getByText('Source checking'))
  fireEvent.click(screen.getAllByText(/Source passage 1/)[0])
  expect(screen.queryByRole('link')).not.toBeInTheDocument()
  expect(screen.getByText('Supporting source passage 0')).toBeVisible()
})

it('announces loading and errors and retains navigation back to the queue', async () => {
  vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('Could not load assessment.'))
  const onBack = vi.fn()
  render(<AssessmentDetail id="failed" session={session} onBack={onBack} />)
  expect(screen.getByRole('status')).toHaveTextContent('Loading your assessment')
  expect(await screen.findByRole('alert')).toHaveTextContent('Could not load assessment.')
  fireEvent.click(screen.getByRole('button', { name: 'Back to queue' }))
  expect(onBack).toHaveBeenCalledOnce()
})

it('shows text-only scope and omitted media before the summary without relabeling history', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ ...saved, omitted_media: ['image', 'video', 'gif'] })))
  render(<AssessmentDetail id="text-only" session={session} onBack={vi.fn()} />)
  const scope = await screen.findByRole('region', { name: 'Analysis scope' })
  expect(scope).toBeVisible()
  expect(scope).toHaveTextContent('Text-only analysis')
  expect(scope).toHaveTextContent('Images, Video, GIFs')
  expect(scope).toHaveTextContent('not analyzed')
  expect(screen.getByText('Analysis').closest('details')).not.toHaveAttribute('open')
})

it.each([[], null, undefined])('distinguishes known text-only scope from unknown historical scope: %j', async omitted_media => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ ...saved, omitted_media })))
  render(<AssessmentDetail id="scope" session={session} onBack={vi.fn()} />)
  await screen.findByText(saved.note)
  const scope = screen.queryByRole('region', { name: 'Analysis scope' })
  if (Array.isArray(omitted_media)) {
    expect(scope).toBeVisible()
    expect(scope).not.toHaveTextContent('Available in this source:')
  } else expect(scope).not.toBeInTheDocument()
})
