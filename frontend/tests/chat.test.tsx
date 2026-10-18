import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { Session } from '@supabase/supabase-js'
import { AnalysisChat } from '../src/features/queue/AnalysisChat'

const session = { access_token: 'test-token', user: { id: 'reader' } } as Session
const empty = { turns: [], available: true, search_available: true, search_price_usd: '0.005' }
const completed = { id: 'request-1', item_id: 'item', question: 'Explain the evidence', status: 'completed',
  search_status: 'ready', insufficient: false, error: null,
  answer: [{ text: 'A grounded explanation.', citations: [{ passage_id: 'chat1:1', label: 'Research source', excerpt: 'Exact supporting passage.', source_url: 'https://source.test/evidence' }] }] }

afterEach(() => { cleanup(); vi.restoreAllMocks() })

it('sends one question with a request ID and displays saved evidence', async () => {
  const fetch = vi.spyOn(globalThis, 'fetch')
    .mockResolvedValueOnce(new Response(JSON.stringify(empty)))
    .mockResolvedValueOnce(new Response(JSON.stringify(completed)))
  render(<AnalysisChat id="item" session={session} />)
  const input = await screen.findByRole('textbox', { name: 'Your question' })
  await waitFor(() => expect(input).toBeEnabled())
  fireEvent.change(input, { target: { value: 'Explain the evidence' } })
  fireEvent.click(screen.getByRole('button', { name: 'Send question' }))
  expect(await screen.findByText('A grounded explanation.')).toBeVisible()
  const init = fetch.mock.calls[1][1]!
  const body = JSON.parse(String(init.body))
  expect(body.question).toBe('Explain the evidence')
  expect(body.request_id).toMatch(/^[a-f\d-]{36}$/)
  expect(init.headers).toMatchObject({ Authorization: 'Bearer test-token' })
  expect(screen.getByText('Exact supporting passage.')).not.toBeVisible()
  fireEvent.click(screen.getByText(/Research source 1/))
  expect(screen.getByText('Exact supporting passage.')).toBeVisible()
  expect(screen.getByRole('link', { name: /Open source/ })).toHaveAttribute('rel', 'noopener noreferrer')
  expect(input).toHaveValue('')
})

it('preserves the question and reuses the same request ID after a network failure', async () => {
  const fetch = vi.spyOn(globalThis, 'fetch')
    .mockResolvedValueOnce(new Response(JSON.stringify(empty)))
    .mockRejectedValueOnce(new TypeError('Network failed'))
    .mockResolvedValueOnce(new Response(JSON.stringify(completed)))
  render(<AnalysisChat id="item" session={session} />)
  const input = await screen.findByRole('textbox', { name: 'Your question' })
  await waitFor(() => expect(input).toBeEnabled())
  fireEvent.change(input, { target: { value: 'Explain the evidence' } })
  fireEvent.keyDown(input, { key: 'Enter', ctrlKey: true })
  expect(await screen.findByRole('alert')).toHaveTextContent(/Network failed/)
  expect(input).toHaveValue('Explain the evidence')
  fireEvent.click(screen.getByRole('button', { name: 'Send question' }))
  await screen.findByText('A grounded explanation.')
  expect(JSON.parse(String(fetch.mock.calls[1][1]!.body)).request_id)
    .toBe(JSON.parse(String(fetch.mock.calls[2][1]!.body)).request_id)
})

it('restores conversation and explains insufficient evidence without unsafe links', async () => {
  const turn = { ...completed, insufficient: true, search_status: 'uncertain', answer: [{ ...completed.answer[0],
    citations: [{ ...completed.answer[0].citations[0], source_url: 'javascript:alert(1)' }] }] }
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ ...empty, turns: [turn] })))
  render(<AnalysisChat id="item" session={session} />)
  expect(await screen.findByText('A grounded explanation.')).toBeVisible()
  expect(screen.getByText(/not enough verified evidence/i)).toBeVisible()
  expect(screen.getByText(/search outcome is uncertain/i)).toBeVisible()
  expect(screen.queryByRole('link', { name: /Open source/ })).not.toBeInTheDocument()
})

it('disables submission for pending saved questions and cannot double-send', async () => {
  const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ ...empty,
    turns: [{ ...completed, status: 'pending', answer: [] }],
  })))
  render(<AnalysisChat id="item" session={session} />)
  expect(await screen.findByText('Explain the evidence')).toBeVisible()
  expect(screen.getByRole('button', { name: 'Working…' })).toBeDisabled()
  expect(screen.getByRole('status')).toHaveTextContent(/Preparing/)
  expect(fetch).toHaveBeenCalledTimes(1)
})

it('keeps the draft when a persisted provider failure returns', async () => {
  vi.spyOn(globalThis, 'fetch')
    .mockResolvedValueOnce(new Response(JSON.stringify(empty)))
    .mockResolvedValueOnce(new Response(JSON.stringify({ ...completed, status: 'failed', error: 'budget_exhausted', answer: [] })))
  render(<AnalysisChat id="item" session={session} />)
  const input = await screen.findByRole('textbox', { name: 'Your question' })
  await waitFor(() => expect(input).toBeEnabled())
  fireEvent.change(input, { target: { value: 'Explain the evidence' } })
  fireEvent.click(screen.getByRole('button', { name: 'Send question' }))
  expect(await screen.findByText(/monthly budget/i)).toBeVisible()
  expect(input).toHaveValue('Explain the evidence')
})
