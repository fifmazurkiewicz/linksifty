import { afterEach, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { Queue } from '../src/features/queue/Queue'

const items = [
  { id: 'ready', title: 'Ready article', status: 'completed', score: 80, verdict: 'valuable' },
  { id: 'active', title: 'Active article', status: 'processing', score: null, verdict: null },
]
const actions = { onOpen: vi.fn(), onPaste: vi.fn(), onResume: vi.fn() }
afterEach(() => { cleanup(); vi.restoreAllMocks() })

it('requires confirmation before deleting a single link, including active work', async () => {
  const onDelete = vi.fn().mockResolvedValue(true)
  const confirm = vi.spyOn(window, 'confirm').mockReturnValue(false)
  render(<Queue items={items} {...actions} onDelete={onDelete} busy={false} />)
  fireEvent.click(screen.getByRole('button', { name: 'Delete Active article' }))
  expect(onDelete).not.toHaveBeenCalled()
  expect(confirm).toHaveBeenCalledWith(expect.stringContaining('1 link'))
  confirm.mockReturnValue(true)
  fireEvent.click(screen.getByRole('button', { name: 'Delete Active article' }))
  await waitFor(() => expect(onDelete).toHaveBeenCalledWith(['active']))
  expect(await screen.findByText('Deleted 1 link.')).toBeInTheDocument()
})

it('selects only visible links and clears selection when filters change', async () => {
  const onDelete = vi.fn().mockResolvedValue(true)
  vi.spyOn(window, 'confirm').mockReturnValue(true)
  render(<Queue items={items} {...actions} onDelete={onDelete} busy={false} />)
  fireEvent.click(screen.getByRole('checkbox', { name: 'Select all visible links' }))
  expect(screen.getByRole('button', { name: 'Delete selected (2)' })).toBeEnabled()
  fireEvent.click(screen.getByRole('button', { name: /in progress/i }))
  expect(screen.getByRole('button', { name: 'Delete selected (0)' })).toBeDisabled()
  fireEvent.click(screen.getByRole('checkbox', { name: 'Select all visible links' }))
  fireEvent.click(screen.getByRole('button', { name: 'Delete selected (1)' }))
  await waitFor(() => expect(onDelete).toHaveBeenCalledWith(['active']))
  expect(screen.queryByRole('checkbox', { name: 'Select Ready article' })).not.toBeInTheDocument()
})

it('retains the selection after a server error and disables mutations while busy', async () => {
  const onDelete = vi.fn().mockResolvedValue(false)
  vi.spyOn(window, 'confirm').mockReturnValue(true)
  const { rerender } = render(<Queue items={items} {...actions} onDelete={onDelete} busy={false} />)
  fireEvent.click(screen.getByRole('checkbox', { name: 'Select Ready article' }))
  fireEvent.click(screen.getByRole('button', { name: 'Delete selected (1)' }))
  await waitFor(() => expect(onDelete).toHaveBeenCalledTimes(1))
  expect(screen.getByRole('checkbox', { name: 'Select Ready article' })).toBeChecked()
  expect(screen.queryByText(/Deleted \d+ link/)).not.toBeInTheDocument()
  rerender(<Queue items={items} {...actions} onDelete={onDelete} busy />)
  expect(screen.getByRole('button', { name: 'Delete selected (1)' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Delete Active article' })).toBeDisabled()
  expect(screen.getByRole('checkbox', { name: 'Select Ready article' })).toBeDisabled()
})
