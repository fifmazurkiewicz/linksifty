import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { Queue } from '../src/features/queue/Queue'

afterEach(cleanup)
const props={onOpen:vi.fn(),onPaste:vi.fn(),onResume:vi.fn(),onDelete:vi.fn(),busy:false}
it('shows an automatic partial preview with the existing recovery actions and no score',()=>{
  render(<Queue {...props} items={[{id:'partial',title:'https://example.test/a',status:'awaiting_manual_content',failure_reason:'partial_content',score:null,verdict:null,partial_overview:'The fetched fragment describes an email knowledge library.'}]} />)
  expect(screen.getByText('The fetched fragment describes an email knowledge library.')).toBeInTheDocument()
  expect(screen.getByText(/Partial preview/)).toBeInTheDocument()
  expect(screen.getByText(/incomplete.*not.*assessment/i)).toBeInTheDocument()
  expect(screen.getByRole('button',{name:'Retry'})).toBeInTheDocument()
  expect(screen.getByRole('button',{name:'Paste content'})).toBeInTheDocument()
  expect(screen.queryByRole('button',{name:'Generate preview'})).not.toBeInTheDocument()
  expect(screen.queryByText(/%/)).not.toBeInTheDocument()
})
it('does not show stale previews on completed items',()=>{
  render(<Queue {...props} items={[{id:'ready',title:'Topic',status:'completed',score:80,verdict:'valuable',partial_overview:'Old partial preview.'}]} />)
  expect(screen.queryByText('Old partial preview.')).not.toBeInTheDocument()
})
it('keeps paste available but suppresses retry while a preview charge is unconfirmed',()=>{
  render(<Queue {...props} items={[{id:'pending',title:'Topic',status:'awaiting_manual_content',score:null,verdict:null,preview_charge_pending:true}]} />)
  expect(screen.queryByRole('button',{name:'Retry'})).not.toBeInTheDocument()
  expect(screen.getByRole('button',{name:'Paste content'})).toBeInTheDocument()
  expect(screen.getByText(/preview charge.*unconfirmed/i)).toBeInTheDocument()
})
