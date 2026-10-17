import { useCallback, useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import type { SupabaseClient } from '@supabase/supabase-js'
import { AuthProvider } from './auth/AuthProvider'
import { useAuth } from './auth/useAuth'
import { AccountStatusScreen } from './features/accounts/AccountStatusScreen'
import { AdminPanel } from './features/admin/AdminPanel'
import { LoginScreen } from './features/auth/LoginScreen'
import { Queue } from './features/queue/Queue'
import { AssessmentDetail } from './features/queue/AssessmentDetail'
import { SettingsPanel } from './features/settings/SettingsPanel'
import { UsagePanel } from './features/settings/UsagePanel'
import { api, ApiError, isUsage, watchActivity, type Account, type Item, type Usage } from './lib/api'
import { analysisUrl } from './lib/urls'
import { ThemeToggle } from './ThemeToggle'
import './App.css'

type Screen = 'Inbox' | 'Add' | 'Settings' | 'Admin'
type View = { kind: 'detail' | 'paste'; id: string } | null

function AuthenticatedApp() {
  const { session, loading: authLoading, signOut } = useAuth()
  const [account, setAccount] = useState<Account | null>(null)
  const [items, setItems] = useState<Item[]>([])
  const deletedIds = useRef(new Set<string>())
  const [usage, setUsage] = useState<Usage | null>(null)
  const [usageError, setUsageError] = useState<string | null>(null)
  const [screen, setScreen] = useState<Screen>('Inbox')
  const [view, setView] = useState<View>(null)
  const [state, setState] = useState<'loading' | 'ready' | 'error'>('loading')
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [links, setLinks] = useState('')
  const [text, setText] = useState('')
  const [inputMode, setInputMode] = useState<'links' | 'paste'>('links')
  const [webSearch, setWebSearch] = useState(false)
  const [searchPrice, setSearchPrice] = useState<string | null>(null)
  const [live, setLive] = useState('Connecting to live progress…')
  const urls = links.split('\n').map(value => value.trim()).filter(Boolean)
  const normalizedUrls = urls.map(analysisUrl)
  const knownUrls = new Set(items.filter(item => item.original_url).map(item => analysisUrl(item.original_url!)))
  const duplicateLinks = inputMode === 'links' && (new Set(normalizedUrls).size !== normalizedUrls.length || normalizedUrls.some(url => knownUrls.has(url)))
  const maxLinks = account?.status === 'pending' ? Math.min(5, account.trial_links_remaining) : 5
  const activeJobs = items.some(item => ['queued', 'processing'].includes(item.status) || item.processing_stage === 'cost_unknown')
  const validText = text.trim().replace(/\s+/g, ' ').length >= 200 && new TextEncoder().encode(text).length <= 100000

  const report = useCallback((error: unknown) => {
    return error instanceof Error ? error.message : 'The request could not be completed.'
  }, [])

  const loadItems = useCallback(async () => {
    if (!session) return
    try {
      const result = await api<{ items: Item[] }>('/v1/items', session)
      setItems(result.items.filter(item => !deletedIds.current.has(item.id)))
      setState('ready')
    } catch (error) {
      setMessage(report(error)); setState('error')
    }
  }, [session, report])

  useEffect(() => {
    if (!session) return
    let active = true
    void api<Account>('/v1/me', session).then(async value => {
      if (!active) return
      setAccount(value)
      if (value.status !== 'rejected') await loadItems()
      else setState('ready')
    }).catch(error => {
      if (!active) return
      setMessage(report(error)); setState('error')
    })
    return () => { active = false }
  }, [session, loadItems, report])

  useEffect(() => {
    if (!session || !account || account.status === 'rejected') return
    const controller = new AbortController()
    void api<Usage>('/v1/usage', session, { signal: controller.signal }).then(value => {
      if (controller.signal.aborted) return
      if (!isUsage(value)) throw new Error('Usage is unavailable.')
      setUsage(value); setUsageError(null)
    }).catch(error => { if (!controller.signal.aborted) setUsageError(report(error)) })
    return () => controller.abort()
  }, [session, account, report])

  useEffect(() => {
    if (!session || !activeJobs || account?.status === 'rejected') return
    const controller = new AbortController()
    let timer: ReturnType<typeof setTimeout> | undefined
    const connect = async () => {
      try {
        await watchActivity(session, controller.signal, (snapshot, updatedUsage) => {
          if (controller.signal.aborted) return
          setItems(snapshot.filter(item => !deletedIds.current.has(item.id))); setUsage(updatedUsage); setUsageError(null); setState('ready')
          setLive('Live progress connected')
        })
        if (!controller.signal.aborted) {
          setLive('Reconnecting… Showing the last confirmed progress.')
          timer = setTimeout(() => void connect(), 1000)
        }
      } catch (error) {
        if (controller.signal.aborted) return
        if (error instanceof ApiError && [401, 403].includes(error.status)) {
          setItems([]); setUsage(null); void signOut(); return
        }
        setLive('Reconnecting… Showing the last confirmed progress.')
        timer = setTimeout(() => void connect(), 3000)
      }
    }
    void connect()
    return () => { controller.abort(); if (timer) clearTimeout(timer) }
  }, [session, activeJobs, account?.status, signOut])

  useEffect(() => {
    if (!session || !account || account.status === 'rejected') return
    const controller = new AbortController()
    void api<{ web_search: boolean; search_price_usd: string | null }>('/v1/capabilities', session, { signal: controller.signal })
      .then(value => { if (!controller.signal.aborted) setSearchPrice(value.web_search ? value.search_price_usd : null) })
      .catch(() => { if (!controller.signal.aborted) setSearchPrice(null) })
    return () => controller.abort()
  }, [session, account])

  if (authLoading || (session && !account && state === 'loading')) {
    return <main className="auth-screen"><p role="status">Loading your account…</p></main>
  }
  if (!session) return <LoginScreen />
  if (account?.status === 'rejected') return <AccountStatusScreen account={account} />

  const refreshAccount = async () => {
    try { setAccount(await api<Account>('/v1/me', session)) }
    catch (error) { setMessage(report(error)) }
  }
  const submit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (busy || duplicateLinks || maxLinks === 0 || (inputMode === 'links' ? !urls.length || urls.length > maxLinks : !validText)) return
    setBusy(true); setMessage(null)
    try {
      await api(inputMode === 'links' ? '/v1/items' : '/v1/items/paste', session, {
        method: 'POST', body: JSON.stringify(inputMode === 'links' ? { sources: urls.map(url => ({ url })), web_search: webSearch && searchPrice !== null } : { text }),
      })
      setLinks(''); setText(''); setScreen('Inbox'); setView(null)
      await loadItems(); await refreshAccount()
    } catch (error) { setMessage(report(error)) }
    finally { setBusy(false) }
  }
  const submitContent = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (view?.kind !== 'paste' || !validText || busy) return
    setBusy(true); setMessage(null)
    try {
      await api(`/v1/items/${view.id}/content`, session, { method: 'PUT', body: JSON.stringify({ text }) })
      setText(''); setView(null); await loadItems()
    } catch (error) { setMessage(report(error)) }
    finally { setBusy(false) }
  }
  const resume = async (id: string) => {
    setBusy(true); setMessage(null)
    try { await api(`/v1/items/${id}/resume`, session, { method: 'POST' }); await loadItems() }
    catch (error) { setMessage(report(error)) }
    finally { setBusy(false) }
  }
  const deleteItems = async (ids: string[]): Promise<boolean> => {
    if (busy) return false
    setBusy(true); setMessage(null)
    try {
      const result = await api<{ deleted_ids: string[] }>('/v1/items/delete', session, {
        method: 'POST', body: JSON.stringify({ item_ids: ids, confirmed: true }),
      })
      if (!Array.isArray(result.deleted_ids) || result.deleted_ids.length !== ids.length
        || new Set(result.deleted_ids).size !== ids.length || result.deleted_ids.some(id => !ids.includes(id))) {
        throw new Error('Deletion could not be confirmed. Refresh your queue before trying again.')
      }
      result.deleted_ids.forEach(id => deletedIds.current.add(id))
      setItems(current => current.filter(item => !deletedIds.current.has(item.id)))
      return true
    } catch (error) { setMessage(report(error)); return false }
    finally { setBusy(false) }
  }

  return <main className="app">
    <aside>
      <b>linksifty<span>.</span></b>
      <p className="eyebrow">YOUR READING QUEUE</p>
      <nav aria-label="Main navigation">
        {(['Inbox', 'Add', 'Settings', ...(account?.role === 'admin' ? ['Admin'] : [])] as Screen[]).map(value =>
          <button className={screen === value ? 'active' : ''} aria-current={screen === value ? 'page' : undefined}
            onClick={() => { setScreen(value); setView(null); setMessage(null) }} key={value}>{value}</button>)}
      </nav>
      <UsagePanel usage={usage} error={usageError} />
      <button className="sign-out" onClick={() => void signOut()}>Sign out</button>
    </aside>
    <section>
      {account?.status === 'pending' && <div className="account-notice" role="status">
        Awaiting admin approval · {account.trial_links_remaining} trial links remaining
      </div>}
      {message && <p className="error" role="alert">{message}</p>}
      {screen === 'Admin' && account?.role === 'admin' && <AdminPanel session={session} onBudgetSaved={(id, updated) => { if (id === account.user_id) setUsage(updated) }} />}
      {screen === 'Inbox' && view?.kind === 'detail' && <AssessmentDetail key={view.id} id={view.id} session={session} onBack={() => setView(null)} />}
      {screen === 'Inbox' && view?.kind === 'paste' && <form onSubmit={event => void submitContent(event)}>
        <button type="button" className="secondary" onClick={() => setView(null)}>Back to queue</button>
        <h1>Paste the article.</h1><p>We could not read the page completely. Paste its full readable content to continue.</p>
        <label htmlFor="source-content">Full source text</label><textarea id="source-content" value={text} onChange={event => setText(event.target.value)} required />
        <p className="hint">At least 200 readable characters, up to 100 KB. Analysis uses your monthly budget.</p>
        <button className="primary" disabled={!validText || busy}>{busy ? 'Submitting…' : 'Analyze pasted content'}</button>
      </form>}
      {screen === 'Inbox' && !view && <>
        <header><div><p className="eyebrow">INBOX</p><h1>Your reading queue.</h1></div><button className="primary" onClick={() => setScreen('Add')}>Add links</button></header>
        <p className="queue-intro">Add links, follow their analysis, and decide what deserves your time.</p>
        {activeJobs && <p className="live-status" role="status">{live}</p>}
        {state === 'loading' && <p role="status">Loading your queue…</p>}
        {state === 'error' && <button className="secondary" onClick={() => void loadItems()}>Retry loading queue</button>}
        {state === 'ready' && <Queue items={items} onOpen={id => setView({ kind: 'detail', id })}
          onPaste={id => { setText(''); setView({ kind: 'paste', id }) }} onResume={id => void resume(id)} onDelete={deleteItems} busy={busy} />}
      </>}
      {screen === 'Add' && <form onSubmit={event => void submit(event)}>
        <p className="eyebrow">NEW ASSESSMENT</p><h1>{maxLinks > 0 ? `Add up to ${maxLinks} ${maxLinks === 1 ? 'link' : 'links'}.` : 'Your trial links are used.'}</h1>
        <div className="filters"><button type="button" aria-pressed={inputMode === 'links'} className={inputMode === 'links' ? 'active' : ''} onClick={() => setInputMode('links')}>Public links</button>
          <button type="button" aria-pressed={inputMode === 'paste'} className={inputMode === 'paste' ? 'active' : ''} onClick={() => setInputMode('paste')}>Paste an article</button></div>
        {inputMode === 'links' ? <>
          <label htmlFor="links">One public URL per line</label>
          <textarea id="links" value={links} onChange={event => setLinks(event.target.value)} placeholder="https://example.com/article" />
          <p className="hint">{urls.length}/{maxLinks} links{account?.status === 'pending' ? ` · ${account.trial_links_remaining} trial links remaining` : ''}</p>
          {duplicateLinks && <p className="error" role="alert">A link is already in your queue or repeated in this batch. Open or resume the existing item instead.</p>}
          {urls.length > maxLinks && <p className="error" role="alert">Submit no more than {maxLinks} links.</p>}
        </> : <>
          <label htmlFor="new-content">Full source text</label><textarea id="new-content" value={text} onChange={event => setText(event.target.value)} />
          <p className="hint">At least 200 readable characters, up to 100 KB. One article uses one trial link.</p>
        </>}
        {inputMode === 'links' && <>
          <label className="search-consent"><input type="checkbox" checked={webSearch && searchPrice !== null} disabled={searchPrice === null || busy} onChange={event => setWebSearch(event.target.checked)} /> Search additional sources with Brave</label>
          <p className="hint">{searchPrice !== null ? `One search per link (${searchPrice} USD at the configured plan rate), plus AI analysis, uses your monthly budget. A short query from this public article is sent to Brave. Up to 20 additional pages are checked; bounded excerpts are used for comparison.` : 'Brave search is not configured. Analysis uses only your submitted text.'}</p>
        </>}
        <p className="hint">Submitting starts analysis and uses your monthly budget.</p>
        <button className="primary" disabled={busy || duplicateLinks || maxLinks === 0 || (inputMode === 'links' ? !urls.length || urls.length > maxLinks : !validText)}>{busy ? 'Submitting…' : inputMode === 'links' ? 'Submit links' : 'Analyze pasted content'}</button>
      </form>}
      {screen === 'Settings' && <><SettingsPanel session={session} /><UsagePanel usage={usage} error={usageError} /></>}
      {screen === 'Admin' && account?.role !== 'admin' && <p className="error" role="alert">Administrator access required.</p>}
    </section>
  </main>
}

export default function App({ client }: { client?: SupabaseClient | null } = {}) {
  return <><ThemeToggle /><AuthProvider client={client}><SessionScope /></AuthProvider></>
}

function SessionScope() {
  const { session } = useAuth()
  return <AuthenticatedApp key={session?.user.id ?? 'signed-out'} />
}
