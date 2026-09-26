// bao-CR-499 — ô «Trưởng phòng phê duyệt» chọn được trước khi duyệt, khóa sau khi duyệt.
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import type { Employee } from '@/modules/hr/types/employee'

import { ApproverSelect } from './approver-select'

const EMPLOYEES = [
  { id: 5, code: 'NS005', full_name: 'Đoàn Minh Khôi' },
  { id: 9, code: 'NS009', full_name: 'Trần Thị Mi' },
] as Employee[]

describe('ApproverSelect', () => {
  it('lets the user pick an employee and reports id + name', async () => {
    const onChange = vi.fn()
    render(<ApproverSelect id="x" value={0} name="" employees={EMPLOYEES} editable onChange={onChange} />)
    await userEvent.click(screen.getByRole('combobox'))
    await userEvent.click(await screen.findByText('NS009 - Trần Thị Mi'))
    expect(onChange).toHaveBeenCalledWith({ approver_employee_id: 9, approver_employee_name: 'Trần Thị Mi' })
  })

  it('is read-only once the document is approved and shows who approved', () => {
    render(<ApproverSelect id="x" value={5} name="Đoàn Minh Khôi" employees={EMPLOYEES} editable={false} onChange={vi.fn()} />)
    expect(screen.queryByRole('combobox')).toBeNull()
    expect(screen.getByText('Đoàn Minh Khôi')).toBeInTheDocument()
  })

  it('shows «Chưa chọn» when nothing is stored', () => {
    render(<ApproverSelect id="x" value={0} name="" employees={[]} editable={false} onChange={vi.fn()} />)
    expect(screen.getByText('Chưa chọn')).toBeInTheDocument()
  })
})
