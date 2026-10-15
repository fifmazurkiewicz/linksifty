export function analysisUrl(value: string): string {
  try {
    const url = new URL(value.trim())
    url.hash = ''
    return url.href
  } catch {
    return value.trim()
  }
}
