import { useState } from 'react'
import { api, type Account } from '../../lib/api'
import { useAuth } from '../../auth/useAuth'

export function AccountStatusScreen({ account, onRequested }: { account: Account; onRequested: (account: Account) => void }) {
  const { session, signOut } = useAuth()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pending = account.status === 'pending'
  const requestAgain = async () => {
    if (!session || busy) return
    setBusy(true); setError(null)
    try { onRequested(await api<Account>('/v1/me/access-request', session, { method: 'POST' })) }
    catch (e) { setError(e instanceof Error ? e.message : 'Could not request access.') }
    finally { setBusy(false) }
  }
  return <main className="auth-screen">
    <section className="auth-card" aria-labelledby="account-status-title">
      <p className="eyebrow">{account.email}</p>
      <h1 id="account-status-title">{pending ? 'Awaiting admin approval' : 'Account unavailable'}</h1>
      {pending
        ? <p>{account.trial_links_remaining} trial links remaining. You can use them while your account is pending.</p>
        : <p>This account has been declined or blocked. You can request access again, or contact the Linksifty administrator if you think this is a mistake.</p>}
      {error && <p className="error" role="alert">{error}</p>}
      {!pending && <button disabled={busy} onClick={() => void requestAgain()}>Request access again</button>}
      <button className="secondary" onClick={() => void signOut()}>Sign out</button>
    </section>
  </main>
}
