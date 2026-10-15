import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import type { Session } from '@supabase/supabase-js'
import { AssessmentDetail } from '../src/features/queue/AssessmentDetail'

const names = ['novelty', 'evidence', 'practicality', 'source_credibility', 'replicability', 'independent_corroboration', 'absence_of_conflict_of_interest', 'concreteness']

afterEach(() => { cleanup(); vi.restoreAllMocks() })

it('opens the saved note, eight criteria and exact supporting passages', async () => {
  const value = { note: 'A practical, source-grounded note.', score: 75, verdict: 'valuable', threshold_snapshot: 60,
    criteria: names.map((name, i) => ({ name, score: 4, rationale: `Rationale ${i}`, citation_ids: [`citation-${i}`] })),
    citations: names.map((_name, i) => ({ id: `citation-${i}`, excerpt: `Supporting source passage ${i}`, source_url: 'https://example.test/article' })),
  }
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(value)))
  render(<AssessmentDetail id="saved" session={{ access_token: 'test-token', user: { id: 'reader' } } as Session} onBack={vi.fn()} />)
  expect(await screen.findByText('A practical, source-grounded note.')).toBeInTheDocument()
  expect(screen.getAllByRole('heading', { level: 3 })).toHaveLength(8)
  expect(screen.getAllByRole('link', { name: 'Source passage 1' })).toHaveLength(8)
  expect(screen.getByText('Supporting source passage 7')).toBeInTheDocument()
  expect(screen.getAllByRole('link', { name: 'Open original source' })[0]).toHaveAttribute('rel', 'noopener noreferrer')
})
