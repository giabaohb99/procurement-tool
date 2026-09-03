import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { LeaveStatusCell } from './leave-status-cell'
import { LEAVE_STATUS } from '../types/leave'

/**
 * Ô trạng thái của bảng đơn nghỉ phép.
 *
 * Luật ở đây: lý do bị chặn phải HIỆN, phải có NHÃN nói rõ nó là lý do của việc
 * gì, và dài mấy cũng không được nong cột ra làm vỡ bảng.
 */
function cell(status: number, note: string, label = 'Nhãn') {
  return <LeaveStatusCell request={{ status, status_label: label, decision_note: note }} />
}

describe('LeaveStatusCell', () => {
  it('hiện lý do kèm nhãn đúng theo từng kết cục xấu', () => {
    const cases: [number, string][] = [
      [LEAVE_STATUS.REJECTED, 'Lý do từ chối'],
      [LEAVE_STATUS.RETURNED, 'Lý do trả về'],
      [LEAVE_STATUS.CANCELLED, 'Lý do hủy yêu cầu'],
    ]
    for (const [status, label] of cases) {
      const { unmount } = render(cell(status, 'đổi ý'))
      //  Nhãn nằm ở `aria-label` — tooltip chỉ dựng nội dung khi rê chuột, nhưng
      //  người dùng trình đọc màn hình phải nghe được ngay.
      expect(screen.getByLabelText(`${label}: đổi ý`)).toBeInTheDocument()
      unmount()
    }
  })

  it('trạng thái KHÔNG phải kết cục xấu thì không in ghi chú nào', () => {
    //  Đơn đã duyệt cũng có thể có `decision_note` — tô nó lên cột trạng thái là
    //  đọc thành đơn bị chặn.
    render(cell(LEAVE_STATUS.APPROVED, 'nhớ bàn giao', 'Đã duyệt'))
    expect(screen.getByText('Đã duyệt')).toBeInTheDocument()
    expect(screen.queryByText('nhớ bàn giao')).not.toBeInTheDocument()
  })

  it('lý do rỗng / toàn khoảng trắng thì không dựng ô ghi chú trống', () => {
    render(cell(LEAVE_STATUS.CANCELLED, '   \n  '))
    expect(screen.queryByLabelText(/^Lý do/)).not.toBeInTheDocument()
  })

  it('lý do 500 ký tự vẫn giữ đủ chữ và ô vẫn co được (thu gọn là việc của CSS)', () => {
    const long = 'a'.repeat(500)
    render(cell(LEAVE_STATUS.CANCELLED, long))

    const wrapper = screen.getByLabelText(`Lý do hủy yêu cầu: ${long}`)
    expect(wrapper).toHaveClass('min-w-0')
    //  `min-w-0` + `truncate` là cặp bắt buộc: thiếu `min-w-0` thì ô co giãn của
    //  flex không nhỏ hơn nội dung, cột bị nong ra và đẩy vỡ cả bảng.
    expect(wrapper.querySelector('.truncate')).toHaveTextContent(long)
  })

  it('lý do có xuống dòng được gộp thành một dòng, không làm hàng cao lên', () => {
    render(cell(LEAVE_STATUS.RETURNED, 'thiếu\n\nngười bàn giao'))
    expect(screen.getByLabelText('Lý do trả về: thiếu người bàn giao')).toBeInTheDocument()
  })
})
