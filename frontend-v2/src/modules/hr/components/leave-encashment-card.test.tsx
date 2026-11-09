import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import {
  LEAVE_ENCASHMENT_REASON,
  LEAVE_ENCASHMENT_STATUS,
  type LeaveEncashment,
} from '../types/leave-encashment'
import { LeaveEncashmentCard } from './leave-encashment-card'

function encashment(overrides: Partial<LeaveEncashment> = {}): LeaveEncashment {
  return {
    id: 9,
    code: 'TTP00009',
    company_id: 1,
    department_id: 1,
    department_name: 'Kho',
    employee_id: 5,
    employee_name: 'Nguyễn Thị An',
    employee_code: 'NSU005',
    leave_type_id: 1,
    leave_type_name: 'Phép năm',
    balance_year: 2026,
    reason_kind: LEAVE_ENCASHMENT_REASON.YEAR_END,
    reason_kind_label: 'Phép dư cuối năm',
    encashment_date: null,
    days: 2.5,
    balance_snapshot: 0,
    encashable_snapshot: 0,
    note: '',
    status: LEAVE_ENCASHMENT_STATUS.APPROVED,
    status_label: 'Đã duyệt',
    approval_instance_id: 0,
    decided_at: null,
    decision_note: '',
    payment_request_id: 31,
    payment_status: 'paid',
    payment_status_label: 'Đã chi',
    created_by: 1,
    created_at: '2026-11-03T00:00:00',
    updated_at: '2026-11-03T00:00:00',
    ...overrides,
  }
}

describe('LeaveEncashmentCard', () => {
  it('leads with the payee and keeps type, year, reason, days and payout status', () => {
    render(<LeaveEncashmentCard encashment={encashment()} />)

    expect(screen.getByText('Nguyễn Thị An')).toBeInTheDocument()
    expect(screen.getByText('TTP00009')).toBeInTheDocument()
    expect(screen.getByText('Phép năm')).toBeInTheDocument()
    expect(screen.getByText(/Năm 2026/)).toBeInTheDocument()
    expect(screen.getByText(/Phép dư cuối năm/)).toBeInTheDocument()
    expect(screen.getByText(/2,5 ngày/)).toBeInTheDocument()
    expect(screen.getByText('Đã duyệt')).toBeInTheDocument()
    expect(screen.getByText('Đã chi')).toBeInTheDocument()
  })

  //  D7a của CR-719: kế toán từ chối chi thì phiếu vẫn Đã duyệt — thẻ phải nói thẳng như cột Trạng thái chi
  //  của bảng, không thì phòng Nhân sự không biết phải hủy phiếu để trả ngày về quỹ.
  it('flags an approved request whose payout was rejected by accounting', () => {
    render(
      <LeaveEncashmentCard
        encashment={encashment({ payment_status: 'cancelled', payment_status_label: 'Đã từ chối' })}
      />,
    )

    expect(screen.getByText('Kế toán từ chối chi')).toBeInTheDocument()
    expect(screen.queryByText('Đã từ chối')).not.toBeInTheDocument()
  })

  it('shows no payout line before approval and marks requests waiting for me', () => {
    render(
      <LeaveEncashmentCard
        encashment={encashment({
          status: LEAVE_ENCASHMENT_STATUS.DRAFT,
          status_label: 'Nháp',
          payment_request_id: 0,
          payment_status: '',
          payment_status_label: '',
        })}
        waitingForMe
      />,
    )

    expect(screen.getByText('Cần bạn duyệt')).toBeInTheDocument()
    expect(screen.queryByText('Kế toán từ chối chi')).not.toBeInTheDocument()
  })

  //  Phiếu chỉ ghi số ngày, tiền do kế toán nhập ở YCTT — thẻ không bao giờ được in chữ "đ".
  it('never shows a money amount', () => {
    const { container } = render(<LeaveEncashmentCard encashment={encashment()} />)

    expect(container.textContent).not.toMatch(/\d\s*đ\b/)
  })
})
