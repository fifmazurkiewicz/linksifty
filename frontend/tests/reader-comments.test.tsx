import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { Session } from '@supabase/supabase-js'
import { ReaderComments } from '../src/features/queue/ReaderComments'

const session = { access_token: 'synthetic-token', user: { id: 'reader' } } as Session
const source = { source_id: 'primary', url: 'https://x.com/author/status/100', platform: 'x', status: 'not_requested', replies: [] }
const reply = { id: '101', author_id: '70', username: 'reader70', text: 'Actual reader opinion <script>untrusted()</script>', truncated: true, has_media: true }
const response = (body: unknown) => new Response(JSON.stringify(body), { headers: { 'content-type': 'application/json' } })
afterEach(() => { cleanup(); vi.restoreAllMocks() })

it('loads only cached status on expansion and requires the disclosed button for an X read', async () => {
  const fetch = vi.spyOn(globalThis, 'fetch').mockImplementation(async (_url, init) =>
    response(init?.method === 'POST' ? { ...source, status: 'ready', replies: [reply] } : { available: true, sources: [source] }))
  render(<ReaderComments id="item" session={session} />)
  const summary = screen.getByText('Reader comments').closest('summary')!
  expect(summary.parentElement).not.toHaveAttribute('open')
  expect(fetch).not.toHaveBeenCalled()
  fireEvent.click(summary)
  const load = await screen.findByRole('button', { name: /Load X replies/ })
  expect(fetch).toHaveBeenCalledTimes(1)
  expect(screen.getByText(/X may charge/)).toBeVisible()
  fireEvent.click(load)
  expect(await screen.findByText(reply.text)).toBeVisible()
  expect(screen.getByRole('status')).toHaveFocus()
  const post = fetch.mock.calls.find(([, init]) => init?.method === 'POST')!
  expect(JSON.parse(String(post[1]?.body))).toEqual({ source_id: 'primary', consent: true })
  expect(screen.getByRole('link', { name: /Open reply on X/ })).toHaveAttribute('href', 'https://x.com/i/web/status/101')
  expect(screen.getByText('@reader70')).toBeVisible()
  expect(screen.getByText(/truncated/i)).toBeVisible()
  expect(screen.getByText(/includes media/)).toBeVisible()
  expect(document.querySelector('script')).toBeNull()
  fireEvent.click(summary)
  fireEvent.click(summary)
  expect(fetch).toHaveBeenCalledTimes(2)
  expect(screen.queryByRole('button', { name: /Load X replies/ })).not.toBeInTheDocument()
})

it.each([
  ['ready', true, /no replies in this sample/],
  ['fetching', true, /running or its outcome is unknown/],
  ['unavailable', true, /could not be retrieved/],
  ['unsupported', true, /Reddit comments are not supported/],
  ['not_requested', false, /X replies are not configured/],
])('explains %s comment availability without automatically reading X', async (status, available, message) => {
  const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValue(response({ available, sources: [{ ...source, status, platform: status === 'unsupported' ? 'reddit' : 'x' }] }))
  render(<ReaderComments id="item" session={session} />)
  fireEvent.click(screen.getByText('Reader comments'))
  expect(await screen.findByText(message)).toBeVisible()
  expect(fetch).toHaveBeenCalledTimes(1)
  expect(screen.queryByRole('button', { name: /Load X replies/ })).not.toBeInTheDocument()
})

it('refreshes a saved uncertain attempt with GET and never resends POST automatically', async () => {
  let posts = 0
  const fetch = vi.spyOn(globalThis, 'fetch').mockImplementation(async (_url, init) => {
    if (init?.method === 'POST') { posts++; throw new Error('network lost') }
    return response({ available: true, sources: [{ ...source, status: posts ? 'fetching' : 'not_requested' }] })
  })
  render(<ReaderComments id="item" session={session} />)
  fireEvent.click(screen.getByText('Reader comments'))
  fireEvent.click(await screen.findByRole('button', { name: /Load X replies/ }))
  expect(await screen.findByRole('alert')).toHaveTextContent(/Check saved results/)
  fireEvent.click(screen.getByRole('button', { name: 'Check saved results' }))
  expect(await screen.findByText(/running or its outcome is unknown/)).toBeVisible()
  await waitFor(() => expect(fetch).toHaveBeenCalledTimes(3))
  expect(posts).toBe(1)
})

it('keeps empty and unsafe-source states explicit without rendering unsafe links', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(response({ available: true, sources: [{ ...source, url: 'javascript:alert(1)' }] }))
  render(<ReaderComments id="item" session={session} />)
  fireEvent.click(screen.getByText('Reader comments'))
  expect(await screen.findByText(/No X or Reddit discussions/)).toBeVisible()
  expect(screen.queryByRole('link')).not.toBeInTheDocument()
})
