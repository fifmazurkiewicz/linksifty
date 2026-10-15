import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { Session } from '@supabase/supabase-js'
import { SettingsPanel } from '../src/features/settings/SettingsPanel'
import { AccountBudget } from '../src/features/admin/AccountBudget'
import { money, watchActivity } from '../src/lib/api'

const session = { access_token: 'test-token', user: { id: 'reader' } } as Session
const usage = { month: '2026-10-01', spent_usd: '0.00001234', reserved_usd: '0.2', limit_usd: '10', remaining_usd: '9.79998766', resets_at: '2026-11-01T00:00:00Z' }

afterEach(() => { cleanup(); vi.restoreAllMocks() })

it('saves an edited threshold using the authenticated API', async () => {
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ valuable_threshold: '60' })))
  render(<SettingsPanel session={session} />)
  const input = await screen.findByLabelText('Valuable threshold (%)')
  await waitFor(() => expect(input).toHaveValue(60))
  fireEvent.change(input, { target: { value: '75' } })
  fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ valuable_threshold: '75' })))
  fireEvent.click(screen.getByRole('button', { name: 'Save settings' }))
  expect(await screen.findByText(/threshold saved/i)).toBeInTheDocument()
  expect(fetchMock).toHaveBeenLastCalledWith(expect.stringContaining('/v1/settings'), expect.objectContaining({
    method: 'PUT', body: JSON.stringify({ valuable_threshold: '75' }),
    headers: expect.objectContaining({ Authorization: 'Bearer test-token' }),
  }))
})

it('lets the administrator save a zero USD cap and retains actual spend', async () => {
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(usage)))
  render(<AccountBudget id="reader" session={session} />)
  const input = await screen.findByLabelText('Monthly limit (USD)')
  await waitFor(() => expect(input).toHaveValue(10))
  fireEvent.change(input, { target: { value: '0' } })
  fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ ...usage, limit_usd: '0', remaining_usd: '0' })))
  fireEvent.click(screen.getByRole('button', { name: 'Save limit' }))
  expect(await screen.findByText(/limit saved/i)).toBeInTheDocument()
  expect(fetchMock).toHaveBeenLastCalledWith(expect.stringContaining('/v1/admin/accounts/reader/usage'), expect.objectContaining({ method: 'PUT', body: '{"limit_usd":"0"}' }))
  expect(screen.getByText('0.000012 USD')).toBeInTheDocument()
})

it('never rounds a small positive cost to zero', () => {
  expect(money('0.00000001')).toBe('<0.000001 USD')
  expect(money('0')).toBe('0.00 USD')
})

it('decodes an authenticated SSE snapshot split across network chunks', async () => {
  const bytes = new TextEncoder().encode(`event: snapshot\ndata: ${JSON.stringify({ items: [{ id: 'one', title: null, original_url: 'https://example.com', status: 'queued' }], usage })}\n\n`)
  const body = new ReadableStream<Uint8Array>({ start(controller) {
    controller.enqueue(bytes.slice(0, 35)); controller.enqueue(bytes.slice(35)); controller.close()
  } })
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(body, { headers: { 'Content-Type': 'text/event-stream' } }))
  const update = vi.fn()
  await watchActivity(session, new AbortController().signal, update)
  expect(update).toHaveBeenCalledWith([expect.objectContaining({ title: 'https://example.com', status: 'queued' })], usage)
  expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/v1/activity'), expect.objectContaining({ headers: { Authorization: 'Bearer test-token' } }))
})
