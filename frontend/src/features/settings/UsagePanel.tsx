import { money, type Usage } from '../../lib/api'

export function UsagePanel({ usage, error, collapsible = false }: {
  usage: Usage | null; error?: string | null; collapsible?: boolean
}) {
  const content = <>
    <p className="meta">MONTHLY USAGE · USD</p>
    {usage ? <>
      <dl><div><dt>Spent</dt><dd>{money(String(usage.spent_usd))}</dd></div>
        <div><dt>Reserved</dt><dd>{money(String(usage.reserved_usd))}</dd></div>
        <div><dt>Limit</dt><dd>{money(String(usage.limit_usd))}</dd></div>
        <div><dt>Available</dt><dd>{money(String(usage.remaining_usd))}</dd></div></dl>
      <p className="hint">Resets {new Date(usage.resets_at).toLocaleDateString()} (UTC). OpenRouter actual costs + Brave searches at the configured plan rate.</p>
      {Number(usage.reserved_usd) > 0 && <p className="hint">Reservations include pending or unconfirmed calls.</p>}
    </> : <p className="hint">{error || 'Loading usage…'}</p>}
  </>
  return <div className="usage-panel" aria-label="Monthly usage">
    {collapsible ? <details className="usage-disclosure">
      <summary><strong>Monthly budget</strong>{' '}
        <span>{usage ? `${money(String(usage.remaining_usd))} available` : error ? 'Usage unavailable' : 'Loading usage…'}</span>
        {usage && Number(usage.reserved_usd) > 0 && <>{' '}<small>Funds reserved</small></>}
      </summary>
      {content}
    </details> : content}
  </div>
}
