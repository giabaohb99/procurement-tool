import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { LeaveApprovalTimeline } from './leave-approval-timeline'
import { LEAVE_STATUS, LEAVE_SESSION, LEAVE_UNIT, type LeaveRequest } from '../types/leave'

/**
 * Dòng thời gian duyệt của tờ đơn.
 *
 * Bài ở đây chốt đúng một luật, và nó là luật hay bị làm hỏng nhất: **lý do
 * không-duyệt phải nằm TRONG dòng thời gian**, ở cả hai đường (có luồng nhiều
 * bước và duyệt thẳng). Bộ máy duyệt không biết gì về `decision_note` của đơn,
 * nên nếu quên chuyền nó vào thì màn hình vẫn dựng ra một dấu vết đầy đủ, trông
 * rất bình thường, mà tuyệt nhiên không có chữ người dùng vừa gõ.
 */

//  Giả lập thẻ dấu vết: in ra CHÍNH những mốc mà Nghỉ phép chuyền vào, để bài
//  test nhìn được thứ đi qua ranh giới hai phân hệ.
vi.mock('@/modules/approval/components/approval-trail-card', () => ({
  ApprovalTrailCard: ({
    extraEvents = [],
  }: {
    extraEvents?: { title: string; detail?: string }[]
  }) => (
    <div data-testid="approval-trail">
      {extraEvents.map((event) => (
        <div key={event.title}>
          <span>{event.title}</span>
          {event.detail && <span>{event.detail}</span>}
        </div>
      ))}
    </div>
  ),
}))

function request(overrides: Partial<LeaveRequest> = {}): LeaveRequest {
  return {
    id: 1,
    code: 'NP001',
    company_id: 1,
    department_id: 2,
    employee_id: 3,
    leave_type_id: 4,
    from_date: '2026-10-05',
    to_date: '2026-10-07',
    from_session: LEAVE_SESSION.FULL,
    to_session: LEAVE_SESSION.FULL,
    unit: LEAVE_UNIT.DAY,
    total_days: 3,
    reason: 'Về quê',
    contact_phone: '',
    contact_address: '',
    status: LEAVE_STATUS.DRAFT,
    approval_instance_id: 0,
    document_id: 0,
    submitted_at: null,
    decided_at: null,
    decision_note: '',
    ...overrides,
  }
}

describe('LeaveApprovalTimeline — đường DUYỆT THẲNG (chưa khai luồng)', () => {
  it('đưa TÊN người chốt lên tiêu đề mốc, cùng khuôn với các mốc khác', () => {
    //  Tiêu đề vô chủ ("Đơn đã hủy") xen giữa những dòng có chủ ngữ thì mốc quan
    //  trọng nhất lại là mốc duy nhất không nói ai chịu trách nhiệm.
    render(
      <LeaveApprovalTimeline
        request={request({
          status: LEAVE_STATUS.CANCELLED,
          decision_note: 'đổi ý',
          decided_by_name: 'Dego Admin',
          decided_at: '2026-09-03T12:03:00',
        })}
      />,
    )

    expect(screen.getByText('Dego Admin đã hủy yêu cầu')).toBeInTheDocument()
    expect(screen.getByText('Lý do: đổi ý')).toBeInTheDocument()
  })

  it('ba kết cục xấu giữ NGUYÊN nghĩa riêng, không gộp thành một câu', () => {
    //  Tự rút đơn ≠ bị sếp bác ≠ bị trả về sửa. Gộp câu chữ là người xem mất khả
    //  năng phân biệt, mà ba chuyện đó dẫn tới ba hành động khác nhau.
    const cases: [number, string][] = [
      [LEAVE_STATUS.REJECTED, 'An đã từ chối yêu cầu'],
      [LEAVE_STATUS.RETURNED, 'An đã trả yêu cầu về'],
      [LEAVE_STATUS.CANCELLED, 'An đã hủy yêu cầu'],
    ]
    for (const [status, title] of cases) {
      const { unmount } = render(
        <LeaveApprovalTimeline request={request({ status, decided_by_name: 'An' })} />,
      )
      expect(screen.getByText(title)).toBeInTheDocument()
      unmount()
    }
  })

  it('không biết ai chốt thì rơi về câu vô chủ, không in câu cụt kiểu " đã hủy yêu cầu"', () => {
    //  `decided_by_name` chỉ có ở đường lấy MỘT đơn; nối chuỗi mà không hỏi thì
    //  ra " đã hủy yêu cầu" — đọc như dữ liệu hỏng.
    render(
      <LeaveApprovalTimeline
        request={request({ status: LEAVE_STATUS.CANCELLED, decision_note: 'đổi ý' })}
      />,
    )
    expect(screen.getByText('Yêu cầu đã bị hủy')).toBeInTheDocument()
    expect(screen.getByText('Lý do: đổi ý')).toBeInTheDocument()
  })

  it('bị từ chối mà KHÔNG ai ghi lý do thì nói thẳng ra, không để trống', () => {
    //  Để trống thì người nộp tưởng màn hình lỗi và đi hỏi Nhân sự — đúng cuộc
    //  gọi mà cả tính năng này sinh ra để chặn.
    render(<LeaveApprovalTimeline request={request({ status: LEAVE_STATUS.REJECTED })} />)
    expect(screen.getByText('Không ai ghi lý do.')).toBeInTheDocument()
  })

  it('đơn ĐÃ DUYỆT không dựng dòng «Lý do:» nào', () => {
    render(
      <LeaveApprovalTimeline
        request={request({ status: LEAVE_STATUS.APPROVED, decision_note: 'nhớ bàn giao' })}
      />,
    )
    expect(screen.getByText('Yêu cầu đã được duyệt')).toBeInTheDocument()
    expect(screen.queryByText(/^Lý do:/)).not.toBeInTheDocument()
  })

  it('đơn nháp chưa gửi thì mốc gửi duyệt còn bỏ ngỏ', () => {
    render(<LeaveApprovalTimeline request={request()} />)
    expect(screen.getByText('Chưa gửi duyệt')).toBeInTheDocument()
    expect(screen.getByText('Chờ kết quả duyệt')).toBeInTheDocument()
  })

  it('lý do dài 500 ký tự KHÔNG bị cắt mất chữ — thu gọn là việc của CSS', () => {
    const long = 'a'.repeat(500)
    render(
      <LeaveApprovalTimeline
        request={request({ status: LEAVE_STATUS.CANCELLED, decision_note: long })}
      />,
    )
    expect(screen.getByText(`Lý do: ${long}`)).toBeInTheDocument()
  })

  it('lý do có xuống dòng được gộp lại thành một dòng, không vỡ mốc', () => {
    render(
      <LeaveApprovalTimeline
        request={request({
          status: LEAVE_STATUS.RETURNED,
          decision_note: 'thiếu\n\nngười bàn giao',
        })}
      />,
    )
    expect(screen.getByText('Lý do: thiếu người bàn giao')).toBeInTheDocument()
  })
})

describe('LeaveApprovalTimeline — đường CÓ LUỒNG nhiều bước', () => {
  it('chuyền mốc «vì sao đơn hỏng» VÀO thẻ dấu vết, không dựng dải cảnh báo riêng', () => {
    render(
      <LeaveApprovalTimeline
        request={request({
          status: LEAVE_STATUS.CANCELLED,
          approval_instance_id: 77,
          decision_note: 'đổi ý',
        })}
      />,
    )

    const trail = screen.getByTestId('approval-trail')
    expect(trail).toHaveTextContent('Yêu cầu đã bị hủy')
    expect(trail).toHaveTextContent('Lý do: đổi ý')
  })

  it('KHÔNG chèn mốc của đơn khi bộ máy đã tự ghi (từ chối · trả về)', () => {
    //  Bộ máy ghi sẵn mốc "đã từ chối"/"đã trả lại" kèm đủ người, giờ, chặng và
    //  lý do. Chèn thêm mốc của đơn là in cùng một câu hai lần liền nhau — lộ
    //  rõ khi lý do dài, hai khối chữ y hệt chồng lên nhau (dựng lại được trên
    //  giao diện thật 03/09/2026 với lý do 480 ký tự).
    for (const status of [LEAVE_STATUS.REJECTED, LEAVE_STATUS.RETURNED]) {
      const { unmount } = render(
        <LeaveApprovalTimeline
          request={request({
            status,
            approval_instance_id: 77,
            decision_note: 'trùng lịch nghỉ',
            decided_by_name: 'An',
          })}
        />,
      )
      expect(screen.getByTestId('approval-trail')).toBeEmptyDOMElement()
      unmount()
    }
  })

  it('đơn đang chờ duyệt thì không chèn mốc nào của riêng đơn', () => {
    render(
      <LeaveApprovalTimeline
        request={request({ status: LEAVE_STATUS.PENDING, approval_instance_id: 77 })}
      />,
    )
    expect(screen.getByTestId('approval-trail')).toBeEmptyDOMElement()
  })
})
