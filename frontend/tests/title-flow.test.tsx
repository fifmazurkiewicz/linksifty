import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import type { Session, SupabaseClient } from '@supabase/supabase-js'
import App from '../src/App'

afterEach(() => { cleanup(); vi.restoreAllMocks() })

it.each([true, false])('generates a title through the confirmed API action, success=%s', async success => {
  const session = { access_token: 'test-token', user: { id: 'reader' } } as Session
  const client = { auth: {
    getSession: vi.fn().mockResolvedValue({ data: { session }, error: null }),
    onAuthStateChange: vi.fn().mockReturnValue({ data: { subscription: { unsubscribe: vi.fn() } } }),
    signOut: vi.fn(),
  } } as unknown as SupabaseClient
  const url = 'https://example.test/article'
  const usage = { month: '2026-10-01', spent_usd: '0.01', reserved_usd: '0', limit_usd: '10', remaining_usd: '9.99', resets_at: '2026-11-01T00:00:00Z' }
  vi.spyOn(window, 'confirm').mockReturnValue(true)
  const fetch = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const path = String(input)
    if (path.endsWith('/v1/me')) return new Response(JSON.stringify({ user_id: 'reader', status: 'approved', role: 'user' }))
    if (path.endsWith('/v1/usage')) return new Response(JSON.stringify(usage))
    if (path.endsWith('/v1/capabilities')) return new Response(JSON.stringify({ web_search: false }))
    if (path.endsWith('/title')) {
      expect(init?.method).toBe('POST')
      expect(JSON.parse(String(init?.body))).toEqual({ confirmed: true })
      return new Response(JSON.stringify(success ? { title: 'Running small models locally' } : { detail: 'Title generation is unavailable.' }), { status: success ? 200 : 409 })
    }
    return new Response(JSON.stringify({ items: [{ id: 'saved', title: url, original_url: url, status: 'completed', score: 80, verdict: 'valuable' }] }))
  })
  render(<App client={client} />)
  fireEvent.click(await screen.findByRole('button', { name: 'Generate title' }))
  if (success) {
    expect(await screen.findByRole('heading', { name: 'Running small models locally' })).toBeVisible()
    expect(screen.getByRole('link', { name: `${url} ↗` })).toHaveAttribute('href', url)
    expect(screen.queryByRole('button', { name: 'Generate title' })).not.toBeInTheDocument()
  } else {
    expect(await screen.findByRole('alert')).toHaveTextContent('Title generation is unavailable.')
    await waitFor(() => expect(screen.getByRole('button', { name: 'Generate title' })).toBeEnabled())
  }
  expect(fetch).toHaveBeenCalledWith(expect.stringContaining('/v1/items/saved/title'), expect.objectContaining({ headers: expect.objectContaining({ Authorization: 'Bearer test-token' }) }))
})
