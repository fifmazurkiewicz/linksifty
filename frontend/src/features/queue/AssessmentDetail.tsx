import { useEffect, useState } from 'react'
import type { Session } from '@supabase/supabase-js'
import { api, type Assessment, type Item } from '../../lib/api'
import { isRubric, criterionLabel } from '../../lib/rubric'
import { AnalysisChat } from './AnalysisChat'

function sourceLink(value: string | null | undefined): URL | null {
  try {
    const url = new URL(value ?? '')
    return ['http:', 'https:'].includes(url.protocol) ? url : null
  } catch {
    return null
  }
}

function Evidence({ ids, citations, label = 'Source passage' }: {
  ids: string[]; citations: Assessment['citations']; label?: string
}) {
  return ids.map((id, index) => {
    const citation = citations.find(c => c.id === id)
    if (!citation) return null
    const source = sourceLink(citation.source_url)
    return <details className="assessment-evidence" key={id}>
      <summary>{label} {index + 1}{source && <span className="evidence-source"> · {source.hostname.replace(/^www\./, '')}</span>}</summary>
      <blockquote>
        <p>{citation.excerpt}</p>
        {source && <a href={source.href} target="_blank" rel="noopener noreferrer">Open original source ↗</a>}
      </blockquote>
    </details>
  })
}

export function AssessmentDetail({ id, item, session, onBack }: {
  id: string; item?: Pick<Item, 'title' | 'original_url'>; session: Session; onBack: () => void
}) {
  const [value, setValue] = useState<Assessment | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    const controller = new AbortController()
    void api<Assessment>(`/v1/items/${id}/assessment`, session, { signal: controller.signal })
      .then(result => { if (!controller.signal.aborted) setValue(result) })
      .catch(e => { if (!controller.signal.aborted) setError(e instanceof Error ? e.message : 'Could not load assessment.') })
    return () => controller.abort()
  }, [id, session])

  const source = sourceLink(item?.original_url)
  const scored = value?.criteria.filter(c => c.score !== null).length ?? 0
  const researchSources = value?.research_sources?.flatMap(s => {
    const url = sourceLink(s.url)
    return url ? [{ id: s.id, url }] : []
  }) ?? []
  const researchStatus = value?.research_status === 'ready'
    ? `${researchSources.length} ${researchSources.length === 1 ? 'page' : 'pages'} fetched`
    : value?.research_status === 'uncertain' ? 'Research outcome uncertain'
      : value?.research_status && value.research_status !== 'not_requested' ? 'Sources not verified' : 'Primary source only'

  return <div className="assessment-detail">
    <button className="secondary assessment-back" onClick={onBack}>Back to queue</button>
    {!value && !error && <p role="status">Loading your assessment…</p>}
    {error && <p className="error" role="alert">{error}</p>}
    {value && <>
      <div className="assessment-heading">
        <p className="eyebrow">YOUR ASSESSMENT</p>
        <h1>{item?.title || 'Saved assessment'}</h1>
        {source && <a className="assessment-origin" href={source.href} target="_blank" rel="noopener noreferrer">{source.hostname.replace(/^www\./, '')} · Open article ↗</a>}
      </div>
      <div className="assessment-verdict" role="group" aria-label="Assessment result">
        <strong className={`verdict-label verdict-${value.verdict}`}>{value.verdict === 'to_review' ? 'To review' : value.verdict === 'valuable' ? 'Valuable' : value.verdict === 'hype' ? 'Hype' : value.verdict.replaceAll('_', ' ')}</strong>
        <strong className="assessment-score">{value.score === null ? 'Not scored' : `${value.score}%`}</strong>
        <span className="assessment-threshold">Valuable threshold at analysis: {value.threshold_snapshot}%</span>
      </div>
      <div className="assessment-summary" role="region" aria-labelledby="assessment-summary-title">
        <h2 id="assessment-summary-title">Summary</h2>
        <p className="assessment-note">{value.note}</p>
      </div>
      {value.verdict_reason && <p className="assessment-reason"><strong>Why this verdict</strong> {value.verdict_reason}</p>}
      {value.hype_signals && value.hype_signals.length > 0 && <div className="assessment-hype" role="region" aria-label="Hype evidence">
        <h2>Evidence of hype</h2>
        {value.hype_signals.map((signal, i) => <div key={i}>
          <p>{signal.rationale}</p>
          <Evidence ids={signal.citation_ids} citations={value.citations} label="Hype evidence" />
        </div>)}
      </div>}
      <details className="assessment-panel">
        <summary><h2>Analysis</h2><span className="panel-status">{scored} of 8 criteria scored</span></summary>
        <div className="assessment-panel-body">
          {value.rubric_snapshot?.version === 2 ? <p className="hint assessment-coverage">
            The percentage covers only scored criteria; not applicable and not verified entries are excluded.
            Key gaps can still require review. This is not a probability of truth.
          </p> : <p className="hint assessment-coverage">Historical assessment using the original scoring rules.</p>}
          {value.criteria.map(criterion => <article className="assessment-criterion" key={criterion.name}>
            <div className="criterion-heading">
              <h3>{criterionLabel(criterion.name, value.rubric_snapshot?.version)}</h3>
              <strong className={`criterion-score${criterion.score === null ? ' criterion-unscored' : ''}`}>
                {criterion.status === 'not_applicable' ? 'Not applicable' : criterion.score === null ? 'Not verified' : `${criterion.score}/5`}
              </strong>
            </div>
            <p>{criterion.rationale}</p>
            <Evidence ids={criterion.citation_ids} citations={value.citations} />
            {isRubric(value.rubric_snapshot) && value.rubric_snapshot.criteria.filter(rule => rule.name === criterion.name).map(rule => <details className="assessment-rules" key={rule.name}>
              <summary>Scoring rules</summary>
              <div className="historical-rule"><p>{rule.description}</p><p>Weight at analysis: ×{rule.weight}</p></div>
            </details>)}
          </article>)}
        </div>
      </details>
      <details className="assessment-panel">
        <summary><h2>Source checking</h2><span className="panel-status">{researchStatus}</span></summary>
        <div className="assessment-panel-body assessment-research">
          <p>{value.research_status === 'ready' ? 'Additional pages were fetched; bounded excerpts were supplied for comparison. Their presence alone does not establish independence or confirm a claim.' : value.research_status === 'uncertain' ? 'A research call has an uncertain outcome; its charge remains reserved. Only the primary source was analyzed.' : value.research_status && value.research_status !== 'not_requested' ? 'Additional sources could not be verified. Only the primary source was analyzed.' : 'Only the submitted source was analyzed; independent sources were not searched.'}</p>
          {researchSources.length > 0 && <ul className="research-sources">{researchSources.map(s => <li key={s.id}>
            <a href={s.url.href} target="_blank" rel="noopener noreferrer">{s.url.hostname.replace(/^www\./, '')}</a>
            <small>{s.url.pathname}</small>
          </li>)}</ul>}
        </div>
      </details>
      <AnalysisChat key={`${session.user.id}:${id}`} id={id} session={session} />
    </>}
  </div>
}
