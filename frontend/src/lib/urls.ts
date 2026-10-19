export function sourceLink(value: string | null | undefined): URL | null {
  try {
    const url = new URL(value ?? '')
    return ['http:', 'https:'].includes(url.protocol) ? url : null
  } catch {
    return null
  }
}

export function analysisUrl(value: string): string {
  try {
    const url = new URL(value.trim())
    url.hash = ''
    return url.href
  } catch {
    return value.trim()
  }
}
