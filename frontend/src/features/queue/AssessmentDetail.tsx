import { useEffect, useState } from 'react'
import type { Session } from '@supabase/supabase-js'
import { api, type Assessment } from '../../lib/api'
import { isRubric, criterionLabel } from '../../lib/rubric'

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
      <h1>{value.verdict.replaceAll('_', ' ')} · {value.score === null ? 'Not scored' : `${value.score}%`}</h1>
      <p className="assessment-note">{value.note}</p>
      <p className="hint">Valuable threshold at analysis: {value.threshold_snapshot}%</p>
      <h2>Source checking</h2>
      <p>{value.research_status === 'ready' ? 'Additional pages were fetched; bounded excerpts were supplied for comparison. Their presence alone does not establish independence or confirm a claim.' : value.research_status === 'uncertain' ? 'The search outcome is uncertain; its charge remains reserved. Only the primary source was analyzed.' : value.research_status && value.research_status !== 'not_requested' ? 'Additional sources could not be verified. Only the primary source was analyzed.' : 'Only the submitted source was analyzed; independent sources were not searched.'}</p>
      {value.research_sources?.map(source => /^https?:\/\//.test(source.url) && <p key={source.id}><a href={source.url} target="_blank" rel="noopener noreferrer">{source.url}</a></p>)}
      <h2>Why this verdict</h2>
      {value.verdict_reason && <p>{value.verdict_reason}</p>}
      {value.rubric_snapshot?.version === 2 ? <p className="hint">
        {value.criteria.filter(c => c.score !== null).length} of 8 criteria scored. The percentage covers only scored criteria;
        not applicable and not verified entries are excluded. Key gaps can still require review. This is not a probability of truth.
      </p> : <p className="hint">Historical assessment using the original scoring rules.</p>}
      {value.hype_signals && value.hype_signals.length > 0 && <section aria-label="Hype evidence">
        <h3>Evidence of hype</h3>
        {value.hype_signals.map((signal, i) => <div key={i}><p>{signal.rationale}</p>
          {signal.citation_ids.map((citation, index) => <a key={citation} href={`#citation-${citation}`}>Hype evidence {index + 1}</a>)}
        </div>)}
      </section>}
      {value.criteria.map(criterion => <article key={criterion.name}><div>
        <h3>{criterionLabel(criterion.name, value.rubric_snapshot?.version)} · {criterion.status === 'not_applicable' ? 'Not applicable' : criterion.status === 'not_verified' ? 'Not verified' : `${criterion.score}/5`}</h3>
        {isRubric(value.rubric_snapshot) && value.rubric_snapshot.criteria.filter(rule => rule.name === criterion.name).map(rule => <div className="historical-rule" key={rule.name}><p>{rule.description}</p><p>Weight at analysis: ×{rule.weight}</p></div>)}
        <p>{criterion.rationale}</p>
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
