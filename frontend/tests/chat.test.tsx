import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
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
  expect(screen.getByText(/at most twice per question/)).toHaveTextContent(/up to three AI calls/)
  expect(screen.getByText(/A search sends/)).toHaveTextContent(/each search/)
  expect(screen.getByText(/Web research · fetched/)).toBeVisible()
  const init = fetch.mock.calls[1][1]!
  const body = JSON.parse(String(init.body))
  expect(body.question).toBe('Explain the evidence')
  expect(body.max_searches).toBe(2)
  expect(body.request_id).toMatch(/^[a-f\d-]{36}$/)
  expect(init.headers).toMatchObject({ Authorization: 'Bearer test-token' })
  expect(screen.getByText('Exact supporting passage.')).not.toBeVisible()
  fireEvent.click(screen.getByText(/Quoted passages/))
  expect(screen.getByText('Exact supporting passage.')).toBeVisible()
  expect(screen.getByRole('link', { name: /https:\/\/source.test\/evidence/ })).toHaveAttribute('rel', 'noopener noreferrer')
  expect(input).toHaveValue('')
})

it('numbers inline references consistently and lists each source link once below the answer', async () => {
  const first = completed.answer[0].citations[0]
  const second = { ...first, passage_id: 'chat1:2', excerpt: 'Another exact passage.' }
  const other = { ...first, passage_id: 'chat2:1', source_url: 'https://other.test/article', excerpt: 'Independent passage.' }
  const turn = { ...completed, answer: [
    { text: 'First claim.', citations: [first, first] },
    { text: 'Second claim.', citations: [second, other] },
    { text: 'Third claim.', citations: [other, first] },
  ] }
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ ...empty, turns: [turn] })))
  render(<AnalysisChat id="item" session={session} />)
  const paragraph = await screen.findByText('First claim.')
  expect(within(paragraph).getAllByRole('link')).toHaveLength(1)
  const sourceOne = within(paragraph).getByRole('link', { name: 'Source 1' })
  expect(sourceOne).toHaveTextContent('[1]')
  expect(within(screen.getByText('Second claim.')).getByRole('link', { name: 'Source 1' })).toHaveAttribute('href', sourceOne.getAttribute('href'))
  expect(within(screen.getByText('Second claim.')).getByRole('link', { name: 'Source 2' })).toHaveTextContent('[2]')
  const sources = screen.getByRole('list', { name: 'Sources' })
  const entries = within(sources).getAllByRole('listitem')
  expect(entries).toHaveLength(2)
  expect(within(sources).getAllByRole('link')).toHaveLength(2)
  expect(document.getElementById(sourceOne.getAttribute('href')!.slice(1))).toBe(entries[0])
  expect(within(entries[0]).getByRole('link')).toHaveAttribute('href', first.source_url)
  expect(within(entries[1]).getByRole('link')).toHaveAttribute('href', other.source_url)
  expect(screen.getByText('Third claim.').compareDocumentPosition(sources) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
  fireEvent.click(within(entries[0]).getByText(/Quoted passages/))
  expect(screen.getAllByText(first.excerpt)).toHaveLength(1)
  expect(screen.getByText(first.excerpt)).toBeVisible()
  expect(screen.getByText(second.excerpt)).toBeVisible()
})

it('keeps reference destinations separate for each saved answer and retains evidence without URLs', async () => {
  const saved = { ...completed, id: 'request-2', answer: [{ text: 'Saved context.', citations: [
    { passage_id: 'analysis:1', label: 'Saved analysis', excerpt: 'Saved analysis passage.', source_url: null },
    { passage_id: 'analysis:2', label: 'Saved analysis', excerpt: 'Second saved passage.', source_url: null },
  ] }] }
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ ...empty, turns: [completed, saved] })))
  render(<AnalysisChat id="item" session={session} />)
  await screen.findByText('Saved context.')
  const references = screen.getAllByRole('link', { name: 'Source 1' })
  expect(references).toHaveLength(2)
  expect(references[0].getAttribute('href')).not.toBe(references[1].getAttribute('href'))
  const lists = screen.getAllByRole('list', { name: 'Sources' })
  expect(within(lists[1]).getAllByRole('listitem')).toHaveLength(1)
  expect(within(lists[1]).queryByRole('link')).not.toBeInTheDocument()
  fireEvent.click(within(lists[1]).getByText(/Quoted passages/))
  expect(screen.getByText('Saved analysis passage.')).toBeVisible()
  expect(screen.getByText('Second saved passage.')).toBeVisible()
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
  expect(screen.queryByRole('link', { name: /javascript:/ })).not.toBeInTheDocument()
  expect(screen.getAllByRole('link').every(link => link.getAttribute('href')?.startsWith('#'))).toBe(true)
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

it('explains historical uncertain relevance failures without encouraging an unchanged retry', async () => {
  const turn = { ...completed, status: 'failed', answer: [], error: 'classification_uncertain' }
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ ...empty, turns: [turn] })))
  render(<AnalysisChat id="item" session={session} />)
  expect(await screen.findByText(/stopped by the relevance check/i)).toBeVisible()
  expect(screen.getByText(/before an answer or search could run/i)).toBeVisible()
  expect(screen.queryByText(/submit the question again|charge remains reserved/i)).not.toBeInTheDocument()
})

it('restores a clarification and lets the reader send a more specific follow-up', async () => {
  const clarification = 'Jakiego tematu dotyczy Twoje pytanie?'
  const turn = { ...completed, search_status: 'not_needed', answer: [{ text: clarification, citations: [] }] }
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ ...empty, turns: [turn] })))
  render(<AnalysisChat id="item" session={session} />)
  expect(await screen.findByText(clarification)).toBeVisible()
  expect(screen.queryByText(/Web research|not enough verified|could not be completed/)).not.toBeInTheDocument()
  const input = screen.getByRole('textbox', { name: 'Your question' })
  fireEvent.change(input, { target: { value: 'Pytam o limit wpłat na IKE.' } })
  expect(screen.getByRole('button', { name: 'Send question' })).toBeEnabled()
})

it('renders and restores a polite refusal without source or research badges', async () => {
  const refusal = 'Chętnie pomogę z pytaniem dotyczącym tej analizy lub jej tematu.'
  const turn = { ...completed, question: 'siema', search_status: 'not_needed',
    answer: [{ text: refusal, citations: [] }] }
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ ...empty, turns: [turn] })))
  render(<AnalysisChat id="item" session={session} />)
  expect(await screen.findByText(refusal)).toBeVisible()
  expect(screen.getByText('siema')).toBeVisible()
  expect(screen.queryByText(/Original source|Research source|One web search|not enough verified/)).not.toBeInTheDocument()
  expect(screen.queryByRole('list', { name: 'Sources' })).not.toBeInTheDocument()
  const input = screen.getByRole('textbox', { name: 'Your question' })
  expect(input).toBeEnabled()
  fireEvent.change(input, { target: { value: 'Why this verdict?' } })
  expect(screen.getByRole('button', { name: 'Send question' })).toBeEnabled()
})
