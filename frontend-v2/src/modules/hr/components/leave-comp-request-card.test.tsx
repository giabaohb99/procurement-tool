import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { LEAVE_COMP_STATUS, type LeaveCompRequest } from '../types/leave-comp'
import { LeaveCompRequestCard } from './leave-comp-request-card'

function request(overrides: Partial<LeaveCompRequest> = {}): LeaveCompRequest {
  return {
    id: 7,
    code: 'NB012',
    company_id: 1,
    department_id: 2,
    department_name: 'Kế toán',
    employee_id: 5,
    employee_name: 'Trần Thị Bình',
    employee_code: 'NSU005',
    work_date: '2026-10-25',
    days: 0.5,
    reason: 'Trực kho ngày Chủ nhật',
    status: LEAVE_COMP_STATUS.PENDING,
    status_label: 'Chờ duyệt',
    approval_instance_id: 3,
    decided_at: null,
    decision_note: '',
    created_by: 1,
    created_at: '2026-10-26T08:00:00',
    updated_at: '2026-10-26T08:00:00',
    ...overrides,
  }
}

describe('LeaveCompRequestCard', () => {
  it('leads with the person, puts the slip code underneath, and shows the status label', () => {
    render(<LeaveCompRequestCard request={request()} />)
    expect(screen.getByText('Trần Thị Bình')).toBeInTheDocument()
    expect(screen.getByText('NB012')).toBeInTheDocument()
    expect(screen.getByText('NSU005')).toBeInTheDocument()
    expect(screen.getByText('Chờ duyệt')).toBeInTheDocument()
  })

  it('shows the work date and half days with a Vietnamese decimal comma like the table', () => {
    render(<LeaveCompRequestCard request={request()} />)
    expect(screen.getByText('Đi làm 25/10/2026')).toBeInTheDocument()
    expect(screen.getByText(/0,5 ngày/)).toBeInTheDocument()
    expect(screen.queryByText(/0\.5/)).not.toBeInTheDocument()
  })

  it('flags slips waiting for the viewer only when told so', () => {
    const { rerender } = render(<LeaveCompRequestCard request={request()} />)
    expect(screen.queryByText('Cần bạn duyệt')).not.toBeInTheDocument()
    rerender(<LeaveCompRequestCard request={request()} waitingForMe />)
    expect(screen.getByText('Cần bạn duyệt')).toBeInTheDocument()
  })

  it('falls back to the employee id when the name is missing, and drops empty optional lines', () => {
    render(<LeaveCompRequestCard request={request({ employee_name: '', employee_code: '', reason: '' })} />)
    expect(screen.getByText('#5')).toBeInTheDocument()
    expect(screen.queryByText('Trực kho ngày Chủ nhật')).not.toBeInTheDocument()
  })

  it('shows the rejection note as plain text, not hidden in a tooltip', () => {
    render(<LeaveCompRequestCard request={request({ decision_note: 'Ngày đó không có lịch trực' })} />)
    expect(screen.getByText('Ngày đó không có lịch trực')).toBeInTheDocument()
  })

  it('contains no button of its own, since the whole card is the tap target', () => {
    render(<LeaveCompRequestCard request={request()} />)
    expect(screen.queryByRole('button')).not.toBeInTheDocument()
  })
})
