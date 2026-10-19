import { cleanup, fireEvent, render, screen, within } from '@testing-library/react'
import { afterEach, vi, it, expect } from 'vitest'
import { Queue } from '../src/features/queue/Queue'

const url = 'https://x.com/example/status/123'
const props = { onOpen: vi.fn(), onPaste: vi.fn(), onResume: vi.fn(), onDelete: vi.fn(), busy: false }
afterEach(cleanup)

it('shows topic headings and clickable original URLs in Needs action and Ready', () => {
  render(<Queue {...props} items={[
    { id: 'failed', title: 'Running models locally', original_url: url, status: 'failed', score: null, verdict: null },
    { id: 'ready', title: 'Choosing a small language model', original_url: 'https://example.com/article', status: 'completed', score: 80, verdict: 'valuable' },
  ]} />)
  fireEvent.click(screen.getByRole('button', { name: /Needs action/ }))
  expect(screen.getByRole('heading', { name: 'Running models locally' })).toBeInTheDocument()
  const link = screen.getByRole('link', { name: `${url} ↗` })
  expect(link).toHaveAttribute('href', url)
  expect(link).toHaveAttribute('target', '_blank')
  expect(link).toHaveAttribute('rel', 'noopener noreferrer')
  fireEvent.click(screen.getByRole('button', { name: /Ready/ }))
  expect(screen.getByRole('heading', { name: 'Choosing a small language model' })).toBeInTheDocument()
  expect(screen.getByRole('link', { name: /https:\/\/example.com\/article/ })).toHaveAttribute('href', 'https://example.com/article')
})

it('confirms budget use before requesting a missing title and disables while busy', () => {
  const generate = vi.fn()
  const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
  const items = [{ id: 'old', title: url, original_url: url, status: 'completed', score: 80, verdict: 'valuable' }]
  const { rerender } = render(<Queue {...props} items={items} onGenerateTitle={generate} />)
  fireEvent.click(screen.getByRole('button', { name: 'Generate title' }))
  expect(confirm).toHaveBeenCalledWith(expect.stringContaining('monthly AI budget'))
  expect(generate).not.toHaveBeenCalled()
  confirm.mockReturnValue(true)
  fireEvent.click(screen.getByRole('button', { name: 'Generate title' }))
  expect(generate).toHaveBeenCalledWith('old')
  rerender(<Queue {...props} busy items={items} onGenerateTitle={generate} />)
  expect(screen.getByRole('button', { name: 'Generate title' })).toBeDisabled()
  confirm.mockRestore()
})

it('keeps URL fallbacks clickable and refuses unsafe protocols', () => {
  render(<Queue {...props} items={[
    { id: 'url', title: url, status: 'queued', score: null, verdict: null },
    { id: 'unsafe', title: 'Saved topic', original_url: 'javascript:alert(1)', status: 'completed', score: null, verdict: null },
  ]} />)
  expect(screen.getByRole('link', { name: url })).toHaveAttribute('href', url)
  const unsafe = screen.getByRole('heading', { name: 'Saved topic' }).closest('article')!
  expect(within(unsafe).queryByRole('link')).not.toBeInTheDocument()
})
