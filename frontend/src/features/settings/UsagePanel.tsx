import { money, type Usage } from '../../lib/api'

export function UsagePanel({ usage, error }: { usage: Usage | null; error?: string | null }) {
  return <div className="usage-panel" aria-label="Monthly OpenRouter usage">
    <p className="meta">MONTHLY USAGE · USD</p>
    {usage ? <>
      <dl><div><dt>Spent</dt><dd>{money(String(usage.spent_usd))}</dd></div>
        <div><dt>Reserved</dt><dd>{money(String(usage.reserved_usd))}</dd></div>
        <div><dt>Limit</dt><dd>{money(String(usage.limit_usd))}</dd></div>
        <div><dt>Available</dt><dd>{money(String(usage.remaining_usd))}</dd></div></dl>
      <p className="hint">Resets {new Date(usage.resets_at).toLocaleDateString()} (UTC). OpenRouter inference only.</p>
      {Number(usage.reserved_usd) > 0 && <p className="hint">Reservations include pending or unconfirmed calls.</p>}
    </> : <p className="hint">{error || 'Loading usage…'}</p>}
  </div>
}
