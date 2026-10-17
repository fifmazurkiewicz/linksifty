import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import type { Session } from '@supabase/supabase-js'
import { rubric } from './rubric-fixture'
import { AssessmentDetail } from '../src/features/queue/AssessmentDetail'

const names = ['novelty', 'evidence', 'practicality', 'source_credibility', 'replicability', 'independent_corroboration', 'absence_of_conflict_of_interest', 'concreteness']

afterEach(() => { cleanup(); vi.restoreAllMocks() })

it('opens the saved note, eight criteria and exact supporting passages', async () => {
  const value = { rubric_snapshot: { criteria: rubric.criteria.map(c => c.name === 'novelty' ? { ...c, description: 'Original historical rule', weight: 9 } : c) }, note: 'A practical, source-grounded note.', score: 75, verdict: 'valuable', threshold_snapshot: 60,
    criteria: names.map((name, i) => ({ name, score: 4, rationale: `Rationale ${i}`, citation_ids: [`citation-${i}`] })),
    citations: names.map((_name, i) => ({ id: `citation-${i}`, excerpt: `Supporting source passage ${i}`, source_url: 'https://example.test/article' })),
  }
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(value)))
  render(<AssessmentDetail id="saved" session={{ access_token: 'test-token', user: { id: 'reader' } } as Session} onBack={vi.fn()} />)
  expect(await screen.findByText('A practical, source-grounded note.')).toBeInTheDocument()
  expect(screen.getByText('Original historical rule')).toBeInTheDocument()
  expect(screen.getByText('Weight at analysis: ×9')).toBeInTheDocument()
  expect(screen.getAllByRole('heading', { level: 3 })).toHaveLength(8)
  expect(screen.getAllByRole('link', { name: 'Source passage 1' })).toHaveLength(8)
  expect(screen.getByText('Supporting source passage 7')).toBeInTheDocument()
  expect(screen.getAllByRole('link', { name: 'Open original source' })[0]).toHaveAttribute('rel', 'noopener noreferrer')
})

it('shows unscored criteria and coverage without fake zero scores', async () => {
  const value = { rubric_snapshot: { ...rubric, version: 2 }, note: 'Calibrated result', score: null, verdict: 'to_review', threshold_snapshot: 60,
    verdict_reason: 'Key evidence is unverified.', hype_signals: [],
    criteria: names.map(name => ({ name, score: null, status: name === 'replicability' ? 'not_applicable' : 'not_verified', rationale: 'Not established', citation_ids: ['c1'] })),
    citations: [{ id: 'c1', excerpt: 'The material inspected.', source_url: null }],
  }
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(value)))
  render(<AssessmentDetail id="new" session={{ access_token: 'test', user: { id: 'reader' } } as Session} onBack={vi.fn()} />)
  expect(await screen.findByText('Calibrated result')).toBeInTheDocument()
  expect(screen.getByText('to review · Not scored')).toBeInTheDocument()
  expect(screen.getByText('Replicability · Not applicable')).toBeInTheDocument()
  expect(screen.getByText('Learning value · Not verified')).toBeInTheDocument()
  expect(screen.getByText(/0 of 8 criteria scored/)).toBeInTheDocument()
  expect(screen.getByText('Key evidence is unverified.')).toBeInTheDocument()
  expect(screen.queryByText(/null%/)).not.toBeInTheDocument()
})

it('shows source evidence behind a hype verdict', async () => {
  const value = { rubric_snapshot: { ...rubric, version: 2 }, note: 'Hype result', score: 30, verdict: 'hype', threshold_snapshot: 60,
    hype_signals: [{ rationale: 'Promises guaranteed results without support.', citation_ids: ['h1'] }],
    criteria: [], citations: [{ id: 'h1', excerpt: 'Guaranteed success!', source_url: 'https://example.test' }],
  }
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(value)))
  render(<AssessmentDetail id="hype" session={{ access_token: 'test', user: { id: 'reader' } } as Session} onBack={vi.fn()} />)
  expect(await screen.findByText('Promises guaranteed results without support.')).toBeInTheDocument()
  expect(screen.getByRole('link', { name: 'Hype evidence 1' })).toHaveAttribute('href', '#citation-h1')
})
