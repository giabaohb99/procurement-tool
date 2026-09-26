// bao-CR-499 — ô «Trưởng phòng phê duyệt» chọn được trước khi duyệt, khóa sau khi duyệt.
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { DeptHeadCandidate } from '../types/purchase-request-detail'

import { ApproverSelect } from './approver-select'

const CANDIDATES: DeptHeadCandidate[] = [
  { employee_id: 5, code: 'NS005', name: 'Đoàn Minh Khôi', position: 'Trưởng phòng' },
  { employee_id: 9, code: 'NS009', name: 'Trần Thị Mi', position: '' },
]

describe('ApproverSelect', () => {
  it('lets the user pick an employee and reports id + name', async () => {
    const onChange = vi.fn()
    render(<ApproverSelect id="x" value={0} name="" candidates={CANDIDATES} editable onChange={onChange} />)
    await userEvent.click(screen.getByRole('combobox'))
    await userEvent.click(await screen.findByText('NS009 - Trần Thị Mi'))
    expect(onChange).toHaveBeenCalledWith({ approver_employee_id: 9, approver_employee_name: 'Trần Thị Mi' })
  })

  it('is read-only once the document is approved and shows who approved', () => {
    render(<ApproverSelect id="x" value={5} name="Đoàn Minh Khôi" candidates={CANDIDATES} editable={false} onChange={vi.fn()} />)
    expect(screen.queryByRole('combobox')).toBeNull()
    expect(screen.getByText('Đoàn Minh Khôi')).toBeInTheDocument()
  })

  it('shows «Chưa chọn» when nothing is stored', () => {
    render(<ApproverSelect id="x" value={0} name="" candidates={[]} editable={false} onChange={vi.fn()} />)
    expect(screen.getByText('Chưa chọn')).toBeInTheDocument()
  })

  it('says why the box is empty when nobody can approve the ticket', () => {
    render(<ApproverSelect id="x" value={0} name="" candidates={[]} editable onChange={vi.fn()} />)
    expect(screen.getByText(/chưa có ai duyệt được phiếu này/i)).toBeInTheDocument()
  })

  it('shows the position next to the name when there is one', async () => {
    render(<ApproverSelect id="x" value={0} name="" candidates={CANDIDATES} editable onChange={vi.fn()} />)
    await userEvent.click(screen.getByRole('combobox'))
    expect(await screen.findByText('NS005 - Đoàn Minh Khôi - Trưởng phòng')).toBeInTheDocument()
  })
})
