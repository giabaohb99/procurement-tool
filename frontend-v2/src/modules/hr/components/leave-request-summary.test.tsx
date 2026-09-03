import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { LeaveRequestSummary } from './leave-request-summary'
import { LEAVE_SESSION, LEAVE_STATUS, LEAVE_UNIT, type LeaveRequest } from '../types/leave'

function request(overrides: Partial<LeaveRequest> = {}): LeaveRequest {
  return {
    id: 1,
    code: 'NP001',
    company_id: 1,
    department_id: 2,
    employee_id: 3,
    employee_name: 'Hồ Quyền Trưởng Phòng',
    leave_type_id: 4,
    leave_type_name: 'Phép năm',
    from_date: '2026-12-14',
    to_date: '2026-12-15',
    from_session: LEAVE_SESSION.FULL,
    to_session: LEAVE_SESSION.FULL,
    unit: LEAVE_UNIT.DAY,
    total_days: 2,
    reason: 'Về quê',
    contact_phone: '',
    contact_address: '',
    status: LEAVE_STATUS.PENDING,
    approval_instance_id: 0,
    document_id: 0,
    submitted_at: null,
    decided_at: null,
    decision_note: '',
    ...overrides,
  }
}

describe('LeaveRequestSummary', () => {
  it('LUÔN dựng mục Bàn giao, kể cả khi chưa khai ai', () => {
    //  Trước 03/09/2026 mục này ẩn hẳn khi rỗng, và người duyệt mở tờ đơn ra
    //  không phân biệt được "người nộp chưa khai ai" với "màn hình thiếu mục
    //  đó" — họ phải đi hỏi. Mà *thiếu người bàn giao* là lý do trả đơn phổ
    //  biến nhất, nên nó phải nói ra thành lời.
    render(<LeaveRequestSummary request={request({ handovers: [] })} />)

    expect(screen.getByText('Bàn giao công việc')).toBeInTheDocument()
    expect(
      screen.getByText('Người nộp chưa khai ai nhận bàn giao trong thời gian nghỉ.'),
    ).toBeInTheDocument()
  })

  it('`handovers` KHÔNG có trong dữ liệu cũng phải hiện mục đó', () => {
    //  Đường danh sách không trả `handovers` (chỉ đường lấy MỘT đơn mới trả).
    //  Đọc `undefined` mà lăn ra ẩn thì lại đúng lỗi vừa vá.
    render(<LeaveRequestSummary request={request()} />)
    expect(screen.getByText('Bàn giao công việc')).toBeInTheDocument()
  })

  it('có bàn giao thì hiện tên và nội dung từng người', () => {
    render(
      <LeaveRequestSummary
        request={request({
          handovers: [
            { id: 1, employee_id: 9, employee_name: 'Lê Thị C', content: 'Trực tổng đài', sort_order: 0 },
            { id: 2, employee_id: 10, employee_name: '', content: 'Chốt công nợ', sort_order: 0 },
          ],
        })}
      />,
    )

    expect(screen.getByText('Lê Thị C')).toBeInTheDocument()
    expect(screen.getByText('Trực tổng đài')).toBeInTheDocument()
    //  Thiếu tên thì rơi về mã nhân sự, không được để dòng trống trơn.
    expect(screen.getByText('#10')).toBeInTheDocument()
  })

  it('nội dung bàn giao dài không dấu cách phải BẺ ĐƯỢC', () => {
    const dai = 'Bangiaocongviec'.repeat(40)
    render(
      <LeaveRequestSummary
        request={request({
          handovers: [{ id: 1, employee_id: 9, employee_name: 'Lê Thị C', content: dai, sort_order: 0 }],
        })}
      />,
    )
    expect(screen.getByText(dai)).toHaveClass('break-words')
  })

  it('buổi nghỉ chỉ nhắc khi KHÁC cả ngày', () => {
    //  Thêm "(Cả ngày)" vào mọi tờ đơn là bốn chữ thừa trên mọi dòng.
    const { rerender } = render(<LeaveRequestSummary request={request()} />)
    expect(screen.getByText('14/12/2026')).toBeInTheDocument()

    rerender(
      <LeaveRequestSummary
        request={request({ from_session: LEAVE_SESSION.AFTERNOON })}
      />,
    )
    expect(screen.getByText('14/12/2026 (Buổi chiều)')).toBeInTheDocument()
  })
})
