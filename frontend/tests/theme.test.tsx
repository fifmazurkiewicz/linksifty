import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../src/App'

afterEach(() => {
  cleanup()
  localStorage.clear()
  delete document.documentElement.dataset.theme
  vi.restoreAllMocks()
  vi.unstubAllGlobals()
})

describe('appearance', () => {
  it('switches with the keyboard and remembers the choice after remounting', async () => {
    const user = userEvent.setup()
    const view = render(<App client={null} />)
    await user.tab()
    expect(screen.getByRole('button', { name: 'Dark mode' })).toHaveFocus()
    await user.keyboard('{Enter}')
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
    expect(screen.getByRole('button', { name: 'Dark mode' })).toHaveAttribute('aria-pressed', 'true')
    view.unmount()
    render(<App client={null} />)
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
    await user.click(screen.getByRole('button', { name: 'Dark mode' }))
    expect(document.documentElement).toHaveAttribute('data-theme', 'light')
    expect(localStorage.getItem('linksifty-theme')).toBe('light')
  })

  it('uses the system dark preference when no choice is saved', () => {
    vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({ matches: true, addEventListener: vi.fn(), removeEventListener: vi.fn() }))
    render(<App client={null} />)
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
  })

  it('keeps an explicit light choice when the system prefers dark', () => {
    localStorage.setItem('linksifty-theme', 'light')
    vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({ matches: true }))
    render(<App client={null} />)
    expect(document.documentElement).toHaveAttribute('data-theme', 'light')
  })

  it('still switches when browser storage is unavailable', async () => {
    vi.spyOn(Storage.prototype, 'getItem').mockImplementation(() => { throw new Error('Storage blocked') })
    vi.spyOn(Storage.prototype, 'setItem').mockImplementation(() => { throw new Error('Storage blocked') })
    render(<App client={null} />)
    await userEvent.click(screen.getByRole('button', { name: 'Dark mode' }))
    expect(document.documentElement).toHaveAttribute('data-theme', 'dark')
  })
})
