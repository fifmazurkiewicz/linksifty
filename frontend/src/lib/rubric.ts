export const legacyCriterionLabels = {
  novelty: 'Novelty', evidence: 'Evidence', practicality: 'Practicality',
  source_credibility: 'Source credibility', replicability: 'Replicability',
  independent_corroboration: 'Independent corroboration',
  absence_of_conflict_of_interest: 'Absence of conflict of interest', concreteness: 'Concreteness',
} as const
export const criterionLabels = {
  novelty: 'Learning value', evidence: 'Support for claims', practicality: 'Usefulness',
  source_credibility: 'Topic-specific credibility', replicability: 'Replicability',
  independent_corroboration: 'Cross-source confirmation',
  absence_of_conflict_of_interest: 'Fair presentation and interests',
  concreteness: 'Specificity and completeness',
} as const

export function criterionLabel(name: string, version = 1): string {
  const labels = version === 2 ? criterionLabels : legacyCriterionLabels
  return Object.hasOwn(labels, name) ? labels[name as keyof typeof labels] : name.replaceAll('_', ' ')
}

export type RubricEntry = { name: keyof typeof criterionLabels; description: string; weight: number }
export type RubricConfig = { version?: 1 | 2; criteria: RubricEntry[] }
export type AssessmentSettings = { valuable_threshold: string | number; rubric: RubricConfig }

export function isRubric(value: unknown): value is RubricConfig {
  if (!value || typeof value !== 'object') return false
  const version = (value as { version?: unknown }).version
  if (version !== undefined && version !== 1 && version !== 2) return false
  const entries = (value as { criteria?: unknown }).criteria
  if (!Array.isArray(entries) || entries.length !== 8) return false
  return new Set(entries.map(c => c?.name)).size === 8 && entries.every(c => c &&
    Object.hasOwn(criterionLabels, c.name) && typeof c.description === 'string' &&
    c.description.length >= 1 && c.description.length <= 1000 && c.description.trim() !== '' &&
    !c.description.includes('\0') && typeof c.weight === 'number' && Number.isInteger(c.weight) && c.weight >= 1 && c.weight <= 10)
}

export function parseSettings(value: unknown): AssessmentSettings {
  if (!value || typeof value !== 'object') throw new Error('Settings are unavailable. Please reload after the backend is updated.')
  const settings = value as Partial<AssessmentSettings>
  if (!['string', 'number'].includes(typeof settings.valuable_threshold) ||
    !Number.isFinite(Number(settings.valuable_threshold)) || Number(settings.valuable_threshold) < 40 ||
    Number(settings.valuable_threshold) > 100 || !isRubric(settings.rubric)) {
    throw new Error('Settings are unavailable. Please reload after the backend is updated.')
  }
  return { valuable_threshold: settings.valuable_threshold!, rubric: { version: settings.rubric.version ?? 1, criteria:
    (Object.keys(criterionLabels) as RubricEntry['name'][]).map(name => settings.rubric!.criteria.find(c => c.name === name)!),
  } }
}
