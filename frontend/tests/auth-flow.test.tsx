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
