import type { Account } from '../../lib/api'
import { useAuth } from '../../auth/useAuth'

export function AccountStatusScreen({ account }: { account: Account }) {
  const { signOut } = useAuth()
  const pending = account.status === 'pending'
  return <main className="auth-screen">
    <section className="auth-card" aria-labelledby="account-status-title">
      <p className="eyebrow">{account.email}</p>
      <h1 id="account-status-title">{pending ? 'Awaiting admin approval' : 'Account unavailable'}</h1>
      {pending
        ? <p>{account.trial_links_remaining} trial links remaining. You can use them while your account is pending.</p>
        : <p>This account has been declined. Contact the Linksifty administrator if you think this is a mistake.</p>}
      <button className="secondary" onClick={() => void signOut()}>Sign out</button>
    </section>
  </main>
}
