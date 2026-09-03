import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { LeaveDecisionDialog } from './leave-decision-dialog'
import { LEAVE_SESSION, LEAVE_STATUS, LEAVE_UNIT, type LeaveInboxRow } from '../types/leave'

/**
 * Hộp xác nhận duyệt (CR-260).
 *
 * Luật chính: **từ chối và trả về BẮT BUỘC lý do, duyệt thì không.** Backend
 * cũng chặn, nhưng chặn ở đây mới đúng chỗ — để backend chặn thì người dùng gõ
 * xong, bấm, rồi mới ăn một câu lỗi đỏ.
 */
function row(overrides: Partial<LeaveInboxRow> = {}): LeaveInboxRow {
  return {
    id: 7,
    code: 'NP007',
    company_id: 1,
    department_id: 2,
    employee_id: 3,
    employee_name: 'Hồ Quyền Trưởng Phòng',
    leave_type_id: 4,
    leave_type_name: 'Phép năm',
    from_date: '2026-10-05',
    to_date: '2026-10-07',
    from_session: LEAVE_SESSION.FULL,
    to_session: LEAVE_SESSION.FULL,
    unit: LEAVE_UNIT.DAY,
    total_days: 3,
    reason: 'Về quê',
    contact_phone: '',
    contact_address: '',
    status: LEAVE_STATUS.PENDING,
    approval_instance_id: 77,
    document_id: 0,
    submitted_at: null,
    decided_at: null,
    decision_note: '',
    task: { id: 1, instance_id: 77, node_seq: 1, node_name: 'Trưởng bộ phận duyệt' },
    ...overrides,
  }
}

describe('LeaveDecisionDialog', () => {
  it('DUYỆT không bắt lý do — bấm được ngay', async () => {
    //  Bắt lý do khi duyệt thì người ta gõ "ok" hai mươi lần một buổi sáng, và
    //  ô ý kiến mất sạch giá trị cho những lần thật sự có gì để nói.
    const onConfirm = vi.fn()
    render(
      <LeaveDecisionDialog
        row={row()}
        decision="approve"
        isPending={false}
        onClose={vi.fn()}
        onConfirm={onConfirm}
      />,
    )

    await userEvent.click(screen.getByRole('button', { name: 'Duyệt' }))
    expect(onConfirm).toHaveBeenCalledWith('')
  })

  it.each([
    ['reject', 'Từ chối'],
    ['return', 'Trả về'],
  ] as const)('%s KHÔNG bấm được khi chưa ghi lý do', async (decision, label) => {
    const onConfirm = vi.fn()
    render(
      <LeaveDecisionDialog
        row={row()}
        decision={decision}
        isPending={false}
        onClose={vi.fn()}
        onConfirm={onConfirm}
      />,
    )

    const confirm = screen.getByRole('button', { name: label })
    expect(confirm).toBeDisabled()

    //  Khoảng trắng KHÔNG tính là lý do: người nộp mở ra đọc được một ô trống
    //  thì vẫn không biết phải sửa gì.
    await userEvent.type(screen.getByLabelText(/Lý do từ chối|Cần sửa gì/), '   ')
    expect(confirm).toBeDisabled()

    await userEvent.type(screen.getByLabelText(/Lý do từ chối|Cần sửa gì/), 'trùng lịch nghỉ')
    expect(confirm).toBeEnabled()
    await userEvent.click(confirm)
    expect(onConfirm).toHaveBeenCalledWith('trùng lịch nghỉ')
  })

  it('tóm tắt đủ bốn thông tin để quyết mà không phải mở tờ đơn', () => {
    //  Duyệt ngay trên dòng nhanh thật, nhưng ký nhầm ngày nghỉ của người khác
    //  thì hỏng hơn là chậm.
    render(
      <LeaveDecisionDialog
        row={row()}
        decision="approve"
        isPending={false}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
      />,
    )

    expect(screen.getByText('NP007')).toBeInTheDocument()
    expect(screen.getByText('Hồ Quyền Trưởng Phòng')).toBeInTheDocument()
    expect(screen.getByText('Phép năm')).toBeInTheDocument()
    expect(screen.getByText('3 ngày')).toBeInTheDocument()
    expect(screen.getByText('05/10/2026 → 07/10/2026')).toBeInTheDocument()
  })

  it('nói rõ TỪ CHỐI đóng hẳn đơn, còn TRẢ VỀ thì không', () => {
    //  Hai nút nằm cạnh nhau và hậu quả khác hẳn nhau — người bấm phải đọc được
    //  điều đó TRƯỚC khi bấm.
    const { rerender } = render(
      <LeaveDecisionDialog
        row={row()}
        decision="reject"
        isPending={false}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
      />,
    )
    expect(screen.getByText(/Đơn đóng hẳn/)).toBeInTheDocument()

    rerender(
      <LeaveDecisionDialog
        row={row()}
        decision="return"
        isPending={false}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
      />,
    )
    expect(screen.getByText(/Đơn KHÔNG bị đóng/)).toBeInTheDocument()
  })

  it('KHÔNG có người bàn giao thì nói thẳng ra, không để trống', () => {
    //  Giấu mục này khi rỗng thì người duyệt không phân biệt được "chưa khai ai"
    //  với "hộp thoại thiếu mục đó" — mà *thiếu người bàn giao* chính là lý do
    //  trả đơn phổ biến nhất, tức là thứ quyết định họ bấm Duyệt hay Trả về.
    render(
      <LeaveDecisionDialog
        row={row({ handovers: [] })}
        decision="approve"
        isPending={false}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
      />,
    )

    expect(screen.getByText('Bàn giao công việc')).toBeInTheDocument()
    expect(screen.getByText('Chưa khai người nhận bàn giao')).toBeInTheDocument()
  })

  it('có người bàn giao thì hiện đủ tên và việc', () => {
    render(
      <LeaveDecisionDialog
        row={row({
          handovers: [
            { id: 1, employee_id: 9, employee_name: 'Lê Thị C', content: 'Trực tổng đài', sort_order: 0 },
            { id: 2, employee_id: 10, employee_name: 'Trần Văn D', content: '', sort_order: 0 },
          ],
        })}
        decision="approve"
        isPending={false}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
      />,
    )

    //  Người không kèm việc vẫn phải hiện TÊN — bàn giao cho ai là thông tin,
    //  bàn giao việc gì là chi tiết.
    expect(screen.getByText('Lê Thị C: Trực tổng đài · Trần Văn D')).toBeInTheDocument()
  })

  it('không có đơn thì không dựng hộp', () => {
    render(
      <LeaveDecisionDialog
        row={null}
        decision="approve"
        isPending={false}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
      />,
    )
    expect(screen.queryByRole('dialog')).not.toBeInTheDocument()
  })

  it('lý do dài không dấu cách phải BẺ ĐƯỢC, không nong hộp ra khỏi màn hình', () => {
    const dai = 'Lydonghirat'.repeat(45)
    render(
      <LeaveDecisionDialog
        row={row({ reason: dai })}
        decision="approve"
        isPending={false}
        onClose={vi.fn()}
        onConfirm={vi.fn()}
      />,
    )
    expect(screen.getByText(dai)).toHaveClass('break-words')
  })
})
