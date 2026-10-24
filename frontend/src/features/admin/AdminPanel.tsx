import { useCallback, useEffect, useState } from 'react'
import type { Session } from '@supabase/supabase-js'
import { api, type AdminAccount, type Usage } from '../../lib/api'
import { AccountBudget } from './AccountBudget'

export function AdminPanel({ session, onBudgetSaved, onPendingCountChange }: { session: Session; onBudgetSaved?: (id: string, usage: Usage) => void; onPendingCountChange?: (count: number | null) => void }) {
  const [accounts, setAccounts] = useState<AdminAccount[]>([])
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const load = useCallback(async () => {
    try {
      const result = await api<AdminAccount[]>('/v1/admin/accounts', session)
      setAccounts(result); setError(null)
      onPendingCountChange?.(result.filter(account => account.status === 'pending').length)
    }
    catch (e) { setError(e instanceof Error ? e.message : 'Could not load accounts.'); onPendingCountChange?.(null) }
  }, [session, onPendingCountChange])
  useEffect(() => {
    let active = true
    void api<AdminAccount[]>('/v1/admin/accounts', session).then(result => {
      if (active) {
        setAccounts(result)
        onPendingCountChange?.(result.filter(account => account.status === 'pending').length)
      }
    }).catch(e => {
      if (active) { setError(e instanceof Error ? e.message : 'Could not load accounts.'); onPendingCountChange?.(null) }
    }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [session, onPendingCountChange])

  const update = async (id: string, status: 'approved' | 'rejected') => {
    setBusy(id)
    try {
      await api(`/v1/admin/accounts/${id}`, session, { method: 'PATCH', body: JSON.stringify({ status }) })
      await load()
    } catch (e) { setError(e instanceof Error ? e.message : 'Could not update account.') }
    finally { setBusy(null) }
  }
  const retryEmail = async (id: string) => {
    setBusy(id)
    try {
      await api(`/v1/admin/accounts/${id}/approval-email/retry`, session, { method: 'POST' })
      await load()
    } catch (e) { setError(e instanceof Error ? e.message : 'Could not retry email.') }
    finally { setBusy(null) }
  }

  return <section className="admin-panel" aria-labelledby="admin-title">
    <p className="eyebrow">ADMIN</p><h1 id="admin-title">Account approvals &amp; budgets</h1>
    <p>Manage access, monthly USD limits and approval emails.</p>
    {error && <p className="error" role="alert">{error}</p>}
    {loading && <p role="status">Loading accounts…</p>}
    {accounts.map(account => <article key={account.user_id} className="admin-account">
      <div><h2>{account.email}</h2><p>{account.status} · {account.trial_links_used} trial links used</p>
        {account.approval_email_status && <p>Approval email: {account.approval_email_status}{account.approval_email_failure_code ? ` (${account.approval_email_failure_code})` : ''}</p>}
        <AccountBudget id={account.user_id} session={session} onSaved={usage => onBudgetSaved?.(account.user_id, usage)} />
      </div>
      <div className="admin-actions">
        {account.status !== 'approved' && <button className="secondary" disabled={busy === account.user_id} onClick={() => void update(account.user_id, 'approved')}>Approve</button>}
        {account.status !== 'rejected' && account.user_id !== session.user.id && <button className="secondary" disabled={busy === account.user_id} onClick={() => void update(account.user_id, 'rejected')}>Reject</button>}
        {account.status === 'approved' && account.approval_email_status === 'failed' && <button className="secondary" disabled={busy === account.user_id} onClick={() => void retryEmail(account.user_id)}>Retry email</button>}
      </div>
    </article>)}
    {accounts.length === 0 && !error && !loading && <p>No accounts to review.</p>}
  </section>
}
