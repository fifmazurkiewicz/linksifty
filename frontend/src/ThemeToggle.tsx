import { useEffect, useState } from 'react'

export function ThemeToggle() {
  const [dark, setDark] = useState(() => {
    try {
      const saved = localStorage.getItem('linksifty-theme')
      if (saved === 'dark' || saved === 'light') return saved === 'dark'
    } catch { /* Storage may be disabled; appearance still works for this visit. */ }
    return window.matchMedia?.('(prefers-color-scheme: dark)').matches ?? false
  })

  useEffect(() => {
    document.documentElement.dataset.theme = dark ? 'dark' : 'light'
  }, [dark])

  const toggle = () => {
    const next = !dark
    setDark(next)
    try { localStorage.setItem('linksifty-theme', next ? 'dark' : 'light') }
    catch { /* Keep the selected appearance even when storage is unavailable. */ }
  }

  return <button type="button" className="theme-toggle secondary" aria-label="Dark mode" aria-pressed={dark} onClick={toggle}>
    <span aria-hidden="true">{dark ? '☀' : '☾'}</span> {dark ? 'Light mode' : 'Dark mode'}
  </button>
}
