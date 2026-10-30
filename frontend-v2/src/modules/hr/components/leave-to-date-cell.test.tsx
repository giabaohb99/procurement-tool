import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { LeaveToDateCell } from './leave-to-date-cell'
import { LEAVE_SESSION, LEAVE_STATUS, LEAVE_UNIT, type LeaveRequest } from '../types/leave'

/**
 * Ô "Đến ngày" của bảng đơn nghỉ. Danh sách khoảng từng chỉ nằm ở `title` — trình đọc màn hình
 * và màn cảm ứng không nhận được (L9 của bản rà duoc-CR-683).
 */

function request(overrides: Partial<LeaveRequest> = {}): LeaveRequest {
  return {
    id: 1,
    code: 'NP001',
    company_id: 1,
    department_id: 1,
    employee_id: 1,
    leave_type_id: 1,
    from_date: '2026-10-27',
    to_date: '2026-11-07',
    from_session: LEAVE_SESSION.FULL,
    to_session: LEAVE_SESSION.FULL,
    unit: LEAVE_UNIT.DAY,
    total_days: 5.5,
    reason: '',
    contact_phone: '',
    contact_address: '',
    status: LEAVE_STATUS.DRAFT,
    approval_instance_id: 0,
    document_id: 0,
    decision_note: '',
    ...overrides,
  }
}

const twoPeriods = [
  { id: 1, from_date: '2026-10-27', from_session: LEAVE_SESSION.FULL, to_date: '2026-10-27', to_session: LEAVE_SESSION.FULL, days: 1, sort_order: 0 },
  { id: 2, from_date: '2026-11-03', from_session: LEAVE_SESSION.AFTERNOON, to_date: '2026-11-07', to_session: LEAVE_SESSION.FULL, days: 4.5, sort_order: 1 },
]

describe('LeaveToDateCell', () => {
  it('reads the full period list as text, not only as a hover title', () => {
    render(<LeaveToDateCell request={request({ periods: twoPeriods })} />)
    expect(
      screen.getByText(', gồm 2 khoảng: 27/10/2026 · 03/11 (chiều) → 07/11/2026'),
    ).toBeInTheDocument()
    //  Chữ mờ "· 2 khoảng" vẫn hiện bằng mắt, nhưng ẩn khỏi trình đọc màn hình cho khỏi đọc hai lần.
    expect(screen.getByText('· 2 khoảng')).toHaveAttribute('aria-hidden', 'true')
  })

  it('a single-period request shows only the date, with no period text', () => {
    render(<LeaveToDateCell request={request({ to_date: '2026-10-29' })} />)
    expect(screen.getByText('29/10/2026')).toBeInTheDocument()
    expect(screen.queryByText(/khoảng/)).not.toBeInTheDocument()
  })
})
