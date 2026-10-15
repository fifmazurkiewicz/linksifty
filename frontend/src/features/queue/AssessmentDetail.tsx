import { useEffect, useState } from 'react'
import type { Session } from '@supabase/supabase-js'
import { api, type Assessment } from '../../lib/api'

export function AssessmentDetail({ id, session, onBack }: { id: string; session: Session; onBack: () => void }) {
  const [value, setValue] = useState<Assessment | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    const controller = new AbortController()
    void api<Assessment>(`/v1/items/${id}/assessment`, session, { signal: controller.signal })
      .then(result => { if (!controller.signal.aborted) setValue(result) })
      .catch(e => { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Could not load assessment.') })
    return () => controller.abort()
  }, [id, session])
  return <div className="assessment-detail">
    <button className="secondary" onClick={onBack}>Back to queue</button>
    <p className="eyebrow">ASSESSMENT</p>
    {!value && !error && <p role="status">Loading your assessment…</p>}
    {error && <p className="error" role="alert">{error}</p>}
    {value && <>
      <h1>{value.verdict.replaceAll('_', ' ')} · {value.score}%</h1>
      <p className="assessment-note">{value.note}</p>
      <p className="hint">Valuable threshold at analysis: {value.threshold_snapshot}%</p>
      <h2>Source checking</h2>
      <p>{value.research_status === 'ready' ? 'Additional pages were fetched and supplied for comparison. Their presence alone does not establish independence or confirm a claim.' : value.research_status === 'uncertain' ? 'The search outcome is uncertain; its charge remains reserved. Only the primary source was analyzed.' : value.research_status && value.research_status !== 'not_requested' ? 'Additional sources could not be verified. Only the primary source was analyzed.' : 'Only the submitted source was analyzed; independent sources were not searched.'}</p>
      {value.research_sources?.map(source => /^https?:\/\//.test(source.url) && <p key={source.id}><a href={source.url} target="_blank" rel="noopener noreferrer">{source.url}</a></p>)}
      <h2>Why this verdict</h2>
      {value.criteria.map(criterion => <article key={criterion.name}><div>
        <h3>{criterion.name.replaceAll('_', ' ')} · {criterion.score}/5</h3><p>{criterion.rationale}</p>
        {criterion.citation_ids.map((citation, index) => <a key={citation} href={`#citation-${citation}`}>Source passage {index + 1}</a>)}
      </div></article>)}
      <h2>Source passages</h2>
      {value.citations.map(citation => <blockquote id={`citation-${citation.id}`} key={citation.id} tabIndex={-1}>
        <p>{citation.excerpt}</p>
        {citation.source_url && /^https?:\/\//.test(citation.source_url) && <a href={citation.source_url} target="_blank" rel="noopener noreferrer">Open original source</a>}
      </blockquote>)}
    </>}
  </div>
}
