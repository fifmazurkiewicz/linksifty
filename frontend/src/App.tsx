import { useCallback, useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import type { SupabaseClient } from '@supabase/supabase-js'
import { AuthProvider } from './auth/AuthProvider'
import { useAuth } from './auth/useAuth'
import { AccountStatusScreen } from './features/accounts/AccountStatusScreen'
import { AdminPanel } from './features/admin/AdminPanel'
import { LoginScreen } from './features/auth/LoginScreen'
import { api, ApiError, type Account } from './lib/api'
import './App.css'

type Screen = 'Inbox' | 'Add' | 'Settings' | 'Admin'
type Item = { id: string; title: string; status: string; score: number | null; verdict: string | null }

function AuthenticatedApp() {
  const { session, loading: authLoading, signOut } = useAuth()
  const [account, setAccount] = useState<Account | null>(null)
  const [items, setItems] = useState<Item[]>([])
  const [screen, setScreen] = useState<Screen>('Inbox')
  const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading')
  const [message, setMessage] = useState<string | null>(null)
  const [links, setLinks] = useState('')
  const urls = links.split('\n').map(value => value.trim()).filter(Boolean)
  const maxLinks = account?.status === 'pending' ? Math.min(5, account.trial_links_remaining) : 5

  const loadItems = useCallback(async () => {
    if (!session) return
    try {
      const result = await api<{ items: Item[] }>('/v1/items', session)
      setItems(result.items)
      setState('ready')
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) await signOut()
      setMessage(error instanceof Error ? error.message : 'Could not load your links.')
      setState('error')
    }
  }, [session, signOut])

  useEffect(() => {
    if (!session) return
    let active = true
    void api<Account>('/v1/me', session).then(async value => {
      if (!active) return
      setAccount(value)
      if (value.status !== 'rejected') await loadItems()
      else setState('ready')
    }).catch(async error => {
      if (!active) return
      if (error instanceof ApiError && error.status === 401) await signOut()
      setMessage(error instanceof Error ? error.message : 'Could not load your account.')
      setState('error')
    })
    return () => { active = false }
  }, [session, loadItems, signOut])

  if (authLoading || (session && !account && state === 'loading')) {
    return <main className="auth-screen"><p role="status">Loading your account…</p></main>
  }
  if (!session) return <LoginScreen />
  if (account?.status === 'rejected') return <AccountStatusScreen account={account} />

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!session || !urls.length || urls.length > 5) return
    setState('loading')
    setMessage(null)
    void api<{ items: Item[] }>('/v1/items', session, {
      method: 'POST',
      body: JSON.stringify({ sources: urls.map(url => ({ url })) }),
    }).then(result => {
      setItems(result.items)
      setLinks('')
      setScreen('Inbox')
      setState('ready')
    }).catch(error => {
      if (error instanceof ApiError && error.status === 401) void signOut()
      setMessage(error instanceof Error ? error.message : 'Could not submit these links.')
      setState('error')
    })
  }

  return <main className="app">
    <aside>
      <b>linksifty<span>.</span></b>
      <p className="eyebrow">YOUR READING QUEUE</p>
      <nav aria-label="Main navigation">
        {(['Inbox', 'Add', 'Settings', ...(account?.role === 'admin' ? ['Admin'] : [])] as Screen[]).map(value =>
          <button className={screen === value ? 'active' : ''} onClick={() => setScreen(value)} key={value}>{value}</button>)}
      </nav>
      <button className="sign-out" onClick={() => void signOut()}>Sign out</button>
    </aside>
    <section>
      {account?.status === 'pending' && <div className="account-notice" role="status">
        Awaiting admin approval · {account.trial_links_remaining} trial links remaining
      </div>}
      {screen === 'Admin' && account?.role === 'admin' && <AdminPanel session={session} />}
      {screen === 'Inbox' && <>
        <header><div><p className="eyebrow">INBOX</p><h1>Make room for what matters.</h1></div><button className="primary" onClick={() => setScreen('Add')}>Add links</button></header>
        {state === 'loading' && <p role="status">Loading your inbox…</p>}
        {state === 'error' && <p className="error" role="alert">{message ?? 'Could not load your inbox.'}</p>}
        {state === 'ready' && items.map(item => <article key={item.id}><div><p className="meta">{item.status.replaceAll('_', ' ')}</p><h2>{item.title}</h2><p>{item.status === 'awaiting_manual_content' ? 'Paste readable content to continue.' : 'Evidence-backed assessment is ready.'}</p></div><div><strong>{item.score === null ? '—' : `${item.score}%`}</strong><br /><small>{item.verdict ?? 'Paste content'}</small></div></article>)}
        {state === 'ready' && items.length === 0 && <p>Your reading queue is empty.</p>}
      </>}
      {screen === 'Add' && <form onSubmit={submit}>
        <p className="eyebrow">NEW ASSESSMENT</p><h1>{maxLinks > 0 ? `Add up to ${maxLinks} ${maxLinks === 1 ? 'link' : 'links'}.` : 'Your trial links are used.'}</h1>
        <label htmlFor="links">One public URL per line</label>
        <textarea id="links" value={links} onChange={event => setLinks(event.target.value)} placeholder="https://example.com/article" />
        <p className="hint">{urls.length}/{maxLinks} links{account?.status === 'pending' ? ` · ${account.trial_links_remaining} trial links remaining` : ''}</p>
        {urls.length > maxLinks && <p className="error" role="alert">Submit no more than {maxLinks} links.</p>}
        {state === 'error' && message && <p className="error" role="alert">{message}</p>}
        <button className="primary" disabled={state === 'loading' || !urls.length || urls.length > maxLinks}>Submit links</button>
      </form>}
      {screen === 'Settings' && <><p className="eyebrow">SETTINGS</p><h1>Your triage rules.</h1><article><div><h2>Valuable threshold</h2><p>Applies only to future assessments.</p></div><strong>60%</strong></article></>}
      {screen === 'Admin' && account?.role !== 'admin' && <p className="error" role="alert">Administrator access required.</p>}
    </section>
  </main>
}

export default function App({ client }: { client?: SupabaseClient | null } = {}) {
  return <AuthProvider client={client}><SessionScope /></AuthProvider>
}

function SessionScope() {
  const { session } = useAuth()
  return <AuthenticatedApp key={session?.user.id ?? 'signed-out'} />
}
