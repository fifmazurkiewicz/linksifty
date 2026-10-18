import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import type { Session, SupabaseClient } from '@supabase/supabase-js'
import App from '../src/App'

function renderApp(session: Session | null = null) {
  let listener: ((event: string, session: Session | null) => void) | undefined
  const signInWithOAuth = vi.fn().mockResolvedValue({ data: {}, error: null })
  const signOut = vi.fn().mockResolvedValue({ error: null })
  const client = { auth: {
    getSession: vi.fn().mockResolvedValue({ data: { session }, error: null }),
    onAuthStateChange: vi.fn((callback) => {
      listener = callback
      return { data: { subscription: { unsubscribe: vi.fn() } } }
    }),
    signInWithOAuth,
    signOut,
  } } as unknown as SupabaseClient
  const view = render(<App client={client} />)
  return { ...view, signInWithOAuth, signOut, emit: (value: Session | null) => listener?.('SIGNED_IN', value) }
}

afterEach(() => {
  cleanup()
  vi.restoreAllMocks()
})

it.each([true, false])('retries a fetch through the existing endpoint and handles success=%s', async (success) => {
  const session = { access_token: 'test-token', user: { id: 'reader' } } as Session
  let resumed = false
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const url = String(input)
    if (url.endsWith('/v1/me')) return new Response(JSON.stringify({ user_id: 'reader', status: 'approved', role: 'user' }))
    if (url.endsWith('/resume')) {
      expect(init?.method).toBe('POST')
      resumed = success
      return new Response(JSON.stringify(success ? {} : { detail: 'Retry is unavailable.' }), { status: success ? 202 : 409 })
    }
    if (url.endsWith('/v1/activity')) return new Response(new ReadableStream())
    return new Response(JSON.stringify({ items: [{ id: 'manual', title: 'Failed fetch', status: resumed ? 'queued' : 'awaiting_manual_content',
      score: null, verdict: null, failure_reason: resumed ? null : 'x_not_configured' }] }))
  })
  renderApp(session)
  fireEvent.click(await screen.findByRole('button', { name: 'Retry' }))
  if (success) {
    expect(await screen.findByText('Waiting for processing.')).toBeVisible()
    expect(screen.queryByRole('button', { name: 'Retry' })).not.toBeInTheDocument()
  } else {
    expect(await screen.findByRole('alert')).toHaveTextContent('Retry is unavailable.')
    expect(screen.getByRole('button', { name: 'Retry' })).toBeEnabled()
  }
  expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/v1/items/manual/resume'), expect.objectContaining({
    method: 'POST', headers: expect.objectContaining({ Authorization: 'Bearer test-token' }),
  }))
})

it('opens an assessment using its saved article title and source from the queue', async () => {
  const session = { access_token: 'test-token', user: { id: 'reader' } } as Session
  vi.spyOn(globalThis, 'fetch').mockImplementation(async input => {
    const url = String(input)
    if (url.endsWith('/v1/me')) return new Response(JSON.stringify({ user_id: 'reader', status: 'approved', role: 'user' }))
    if (url.endsWith('/assessment')) return new Response(JSON.stringify({ note: 'Article summary.', score: 62, verdict: 'valuable', threshold_snapshot: 60, criteria: [], citations: [] }))
    return new Response(JSON.stringify({ items: [{ id: 'ike', title: 'Understanding IKE', original_url: 'https://example.test/ike', status: 'completed', score: 62, verdict: 'valuable' }] }))
  })
  renderApp(session)
  fireEvent.click(await screen.findByRole('button', { name: 'Read assessment' }))
  expect(await screen.findByRole('heading', { level: 1, name: 'Understanding IKE' })).toBeVisible()
  expect(screen.getByRole('link', { name: /Open article/ })).toHaveAttribute('href', 'https://example.test/ike')
})

it('deletes confirmed links through the API and ignores stale progress snapshots', async () => {
  const session = { access_token: 'test-token', user: { id: 'reader' } } as Session
  const items = [
    { id: 'delete-me', title: 'Delete this article', status: 'processing', score: null, verdict: null },
    { id: 'keep-me', title: 'Keep this article', status: 'processing', score: null, verdict: null },
  ]
  const usage = { spent_usd: '0.01', reserved_usd: '0.1', limit_usd: '10', remaining_usd: '9.89', resets_at: '2026-11-01T00:00:00Z' }
  let stream: ReadableStreamDefaultController<Uint8Array> | undefined
  vi.spyOn(window, 'confirm').mockReturnValue(true)
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const url = String(input)
    if (url.endsWith('/v1/me')) return new Response(JSON.stringify({ user_id: 'reader', status: 'approved', role: 'user', trial_links_remaining: 3 }))
    if (url.endsWith('/v1/items/delete')) {
      expect(init?.method).toBe('POST')
      expect(JSON.parse(String(init?.body))).toEqual({ item_ids: ['delete-me'], confirmed: true })
      return new Response(JSON.stringify({ deleted_ids: ['delete-me'] }))
    }
    if (url.endsWith('/v1/activity')) return new Response(new ReadableStream({ start(controller) { stream = controller } }), { headers: { 'Content-Type': 'text/event-stream' } })
    if (url.endsWith('/v1/usage')) return new Response(JSON.stringify(usage))
    if (url.endsWith('/v1/capabilities')) return new Response(JSON.stringify({ web_search: false }))
    return new Response(JSON.stringify({ items }))
  })
  renderApp(session)
  fireEvent.click(await screen.findByRole('button', { name: 'Delete Delete this article' }))
  await waitFor(() => expect(screen.queryByRole('heading', { name: 'Delete this article' })).not.toBeInTheDocument())
  expect(screen.getByRole('heading', { name: 'Keep this article' })).toBeInTheDocument()
  expect(await screen.findByText('Deleted 1 link.')).toBeInTheDocument()
  expect(stream).toBeDefined()
  stream!.enqueue(new TextEncoder().encode(`event: snapshot\ndata: ${JSON.stringify({ items, usage })}\n\n`))
  await screen.findByText('Live progress connected')
  expect(screen.queryByRole('heading', { name: 'Delete this article' })).not.toBeInTheDocument()
  expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/v1/items/delete'), expect.objectContaining({ headers: expect.objectContaining({ Authorization: 'Bearer test-token' }) }))
})

describe('account access', () => {
  it('shows Google sign in and requests identity scopes', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch')
    const { signInWithOAuth } = renderApp()
    const signIn = await screen.findByRole('button', { name: /continue with google/i })
    fireEvent.click(signIn)
    await waitFor(() => expect(signInWithOAuth).toHaveBeenCalledWith({
      provider: 'google', options: { scopes: 'openid email profile', redirectTo: `${window.location.origin}/` },
    }))
    expect(fetchMock).not.toHaveBeenCalled()
  })

  it('starts Google sign-in from the keyboard', async () => {
    const user = userEvent.setup()
    const { signInWithOAuth } = renderApp()
    await user.tab()
    expect(screen.getByRole('button', { name: 'Dark mode' })).toHaveFocus()
    await user.tab()
    expect(screen.getByRole('button', { name: /continue with google/i })).toHaveFocus()
    await user.keyboard('{Enter}')
    await waitFor(() => expect(signInWithOAuth).toHaveBeenCalledOnce())
  })

  it('shows pending status and remaining trial links for a signed-in account', async () => {
    const session = { access_token: 'test-token', user: { id: 'user-1' } } as Session
    vi.spyOn(globalThis, 'fetch').mockImplementation(async input => String(input).endsWith('/v1/me')
      ? new Response(JSON.stringify({ user_id: 'user-1', email: 'reader@example.com', status: 'pending', role: 'user', trial_links_used: 1, trial_links_remaining: 2 }), { status: 200 })
      : new Response(JSON.stringify({ items: [] }), { status: 200 }))
    renderApp(session)
    expect(await screen.findByText(/awaiting admin approval/i)).toBeInTheDocument()
    expect(screen.getByText(/2 trial links remaining/i)).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Add links' }))
    expect(screen.getByRole('heading', { name: /add up to 2 links/i })).toBeInTheDocument()
    fireEvent.change(screen.getByLabelText(/one public url per line/i), {
      target: { value: 'https://one.example\nhttps://two.example\nhttps://three.example' },
    })
    expect(screen.getByRole('button', { name: 'Submit links' })).toBeDisabled()
    expect(screen.queryByRole('button', { name: 'Admin' })).not.toBeInTheDocument()
  })

  it('shows rejected status without opening the inbox', async () => {
    const session = { access_token: 'test-token', user: { id: 'user-3' } } as Session
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({
      user_id: 'user-3', email: 'reader@example.com', status: 'rejected', role: 'user',
      trial_links_used: 0, trial_links_remaining: 3,
    }), { status: 200 }))
    renderApp(session)
    expect(await screen.findByRole('heading', { name: /account unavailable/i })).toBeInTheDocument()
    expect(globalThis.fetch).toHaveBeenCalledTimes(1)
  })

  it('signs out when the API rejects an expired bearer token', async () => {
    const session = { access_token: 'expired-token', user: { id: 'user-4' } } as Session
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('Unauthorized', { status: 401 }))
    const { signOut } = renderApp(session)
    await waitFor(() => expect(signOut).toHaveBeenCalledOnce())
  })

  it('shows admin controls only for an admin account and approves from the list', async () => {
    const session = { access_token: 'test-token', user: { id: 'admin-1' } } as Session
    vi.spyOn(globalThis, 'fetch').mockImplementation(async (input) => {
      const url = String(input)
      if (url.endsWith('/v1/me')) return new Response(JSON.stringify({
        user_id: 'admin-1', email: 'owner@example.com', status: 'approved',
        role: 'admin', trial_links_used: 0, trial_links_remaining: 3,
      }), { status: 200 })
      if (url.endsWith('/v1/admin/accounts')) return new Response(JSON.stringify([{
        user_id: 'user-2', email: 'reader@example.com', status: 'pending', role: 'user',
        trial_links_used: 2, trial_links_remaining: 1, created_at: '2026-10-14T00:00:00Z',
        approval_email_status: null, approval_email_failure_code: null,
      }]), { status: 200 })
      return new Response(JSON.stringify({ items: [] }), { status: 200 })
    })
    renderApp(session)
    fireEvent.click(await screen.findByRole('button', { name: 'Admin' }))
    expect(await screen.findByRole('heading', { name: /account approvals/i })).toBeInTheDocument()
    fireEvent.click(await screen.findByRole('button', { name: 'Approve' }))
    await waitFor(() => expect(globalThis.fetch).toHaveBeenCalledWith(
      expect.stringContaining('/v1/admin/accounts/user-2'),
      expect.objectContaining({ method: 'PATCH', headers: expect.objectContaining({ Authorization: 'Bearer test-token' }) }),
    ))
  })

  it('lets an admin retry a failed approval email', async () => {
    const session = { access_token: 'test-token', user: { id: 'admin-1' } } as Session
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async input => {
      const url = String(input)
      if (url.endsWith('/v1/me')) return new Response(JSON.stringify({
        user_id: 'admin-1', email: 'owner@example.com', status: 'approved',
        role: 'admin', trial_links_used: 0, trial_links_remaining: 3,
      }), { status: 200 })
      if (url.endsWith('/v1/admin/accounts')) return new Response(JSON.stringify([{
        user_id: 'user-5', email: 'reader@example.com', status: 'approved', role: 'user',
        trial_links_used: 3, trial_links_remaining: 0, created_at: '2026-10-14T00:00:00Z',
        approval_email_status: 'failed', approval_email_failure_code: 'timeout',
      }]), { status: 200 })
      return new Response(JSON.stringify({ items: [] }), { status: 200 })
    })
    renderApp(session)
    fireEvent.click(await screen.findByRole('button', { name: 'Admin' }))
    fireEvent.click(await screen.findByRole('button', { name: 'Retry email' }))
    await waitFor(() => expect(fetchMock).toHaveBeenCalledWith(
      expect.stringContaining('/v1/admin/accounts/user-5/approval-email/retry'),
      expect.objectContaining({ method: 'POST', headers: expect.objectContaining({ Authorization: 'Bearer test-token' }) }),
    ))
  })
})

it('clears private data when a settings request reports an expired session', async () => {
  const session = { access_token: 'test-token', user: { id: 'reader' } } as Session
  vi.spyOn(globalThis, 'fetch').mockImplementation(async input => {
    const url = String(input)
    if (url.endsWith('/v1/me')) return new Response(JSON.stringify({
      user_id: 'reader', email: 'reader@example.test', status: 'approved', role: 'user', trial_links_used: 0, trial_links_remaining: 3,
    }))
    if (url.endsWith('/v1/settings')) return new Response('Expired', { status: 401 })
    if (url.endsWith('/v1/usage')) return new Response(JSON.stringify({ month: '2026-10-01', spent_usd: '0.01', reserved_usd: '0', limit_usd: '10', remaining_usd: '9.99', resets_at: '2026-11-01T00:00:00Z' }))
    return new Response(JSON.stringify({ items: [{ id: 'private', title: 'Private reading item', status: 'completed', score: 80, verdict: 'valuable' }] }))
  })
  const { signOut } = renderApp(session)
  expect(await screen.findByText('Private reading item')).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Settings' }))
  expect(await screen.findByRole('button', { name: /continue with google/i })).toBeInTheDocument()
  expect(screen.queryByText('Private reading item')).not.toBeInTheDocument()
  expect(screen.queryByText('0.01 USD')).not.toBeInTheDocument()
  expect(signOut).toHaveBeenCalledOnce()
})

it('keeps earlier links after submission and refreshes the remaining trial allowance', async () => {
  let accepted = false
  const session = { access_token: 'test-token', user: { id: 'reader' } } as Session
  const old = { id: 'old', title: 'Earlier saved article', status: 'completed', score: 70, verdict: 'valuable' }
  const added = { id: 'new', title: 'New submitted article', status: 'queued', score: null, verdict: null }
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const url = String(input)
    if (url.endsWith('/v1/me')) return new Response(JSON.stringify({ user_id: 'reader', email: 'reader@example.test', status: 'pending', role: 'user', trial_links_used: accepted ? 1 : 0, trial_links_remaining: accepted ? 2 : 3 }))
    if (url.endsWith('/v1/items') && init?.method === 'POST') {
      accepted = true
      return new Response(JSON.stringify({ items: [added] }), { status: 202 })
    }
    return new Response(JSON.stringify({ items: accepted ? [added, old] : [old] }))
  })
  renderApp(session)
  expect(await screen.findByText('Earlier saved article')).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Add links' }))
  fireEvent.change(screen.getByLabelText('One public URL per line'), { target: { value: 'https://example.test/article' } })
  fireEvent.click(screen.getByRole('button', { name: 'Submit links' }))
  expect(await screen.findByText('New submitted article')).toBeInTheDocument()
  expect(screen.getByText('Earlier saved article')).toBeInTheDocument()
  expect(await screen.findByText(/awaiting admin approval · 2 trial links remaining/i)).toBeInTheDocument()
})

it('allows pasted recovery of an accepted trial link even after trial links are used', async () => {
  let pasted = false
  const session = { access_token: 'test-token', user: { id: 'reader' } } as Session
  const fetchMock = vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const url = String(input)
    if (url.endsWith('/v1/me')) return new Response(JSON.stringify({ user_id: 'reader', email: 'reader@example.test', status: 'pending', role: 'user', trial_links_used: 3, trial_links_remaining: 0 }))
    if (url.endsWith('/v1/items/manual/content') && init?.method === 'PUT') {
      pasted = true
      return new Response(JSON.stringify({ id: 'manual' }), { status: 202 })
    }
    return new Response(JSON.stringify({ items: [{ id: 'manual', title: 'Blocked source', status: pasted ? 'queued' : 'awaiting_manual_content', score: null, verdict: null }] }))
  })
  renderApp(session)
  fireEvent.click(await screen.findByRole('button', { name: 'Paste content' }))
  fireEvent.change(screen.getByLabelText('Full source text'), { target: { value: 'Complete readable source with testable supporting evidence. '.repeat(10) } })
  fireEvent.click(screen.getByRole('button', { name: 'Analyze pasted content' }))
  await waitFor(() => expect(pasted).toBe(true))
  expect(fetchMock).toHaveBeenCalledWith(expect.stringContaining('/v1/items/manual/content'), expect.objectContaining({ method: 'PUT' }))
  expect(await screen.findByText(/waiting for processing/i)).toBeInTheDocument()
})

it('requires explicit consent and shows the Brave plan charge before submitting', async () => {
  const session = { access_token: 'test-token', user: { id: 'reader' } } as Session
  let submitted: Record<string, unknown> | undefined
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    const url = String(input)
    if (url.endsWith('/v1/me')) return new Response(JSON.stringify({ user_id: 'reader', email: 'reader@example.test', status: 'approved', role: 'user', trial_links_remaining: 3 }))
    if (url.endsWith('/v1/capabilities')) return new Response(JSON.stringify({ web_search: true, search_price_usd: '0.005' }))
    if (url.endsWith('/v1/items') && init?.method === 'POST') submitted = JSON.parse(String(init.body))
    return new Response(JSON.stringify({ items: [] }))
  })
  renderApp(session)
  fireEvent.click(await screen.findByRole('button', { name: 'Add links' }))
  const checkbox = await screen.findByRole('checkbox', { name: /search additional sources with brave/i })
  await waitFor(() => expect(checkbox).toBeEnabled())
  expect(checkbox).not.toBeChecked()
  expect(screen.getByText(/0.005 USD at the configured plan rate/)).toBeInTheDocument()
  fireEvent.click(checkbox)
  fireEvent.change(screen.getByLabelText(/one public url per line/i), { target: { value: 'https://public.example/article' } })
  fireEvent.click(screen.getByRole('button', { name: 'Submit links' }))
  await waitFor(() => expect(submitted?.web_search).toBe(true))
})

it('blocks an existing URL and fragment variations before another submission', async () => {
  const session = { access_token: 'test-token', user: { id: 'reader' } } as Session
  let submits = 0
  vi.spyOn(globalThis, 'fetch').mockImplementation(async (input, init) => {
    if (init?.method === 'POST') submits++
    if (String(input).endsWith('/v1/me')) return new Response(JSON.stringify({ user_id: 'reader', status: 'approved', role: 'user', trial_links_remaining: 3 }))
    return new Response(JSON.stringify({ items: [{ id: 'saved', original_url: 'https://example.test/article#old', title: 'Saved article', status: 'failed', processing_stage: 'invalid_model_output' }] }))
  })
  renderApp(session)
  expect(await screen.findByText('Saved article')).toBeInTheDocument()
  fireEvent.click(screen.getByRole('button', { name: 'Add links' }))
  fireEvent.change(screen.getByLabelText(/one public url per line/i), { target: { value: 'https://EXAMPLE.test:443/article#new' } })
  expect(screen.getByRole('button', { name: 'Submit links' })).toBeDisabled()
  expect(screen.getByText(/already in your queue or repeated in this batch/)).toBeInTheDocument()
  expect(submits).toBe(0)
})
