import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { LeaveBalanceHintBox } from './leave-balance-hint-box'
import type { LeaveBalanceHint } from '../types/leave'

/**
 * Ô «số phép còn lại» — ràng buộc §6.1 của kế hoạch Nghỉ phép (CR-259) và lý do
 * tồn tại của cả đợt. Doc gọi nó là *"chi tiết nhỏ, nhưng nó cắt phần lớn số đơn
 * sai và phần lớn câu hỏi gửi về phòng Nhân sự"*.
 *
 * Bài ở đây chốt bốn nhánh hiển thị. Nới lỏng nhánh nào cũng là trả người dùng
 * về chỗ phải đoán mình còn mấy ngày.
 */

const hookResult = vi.hoisted(() => ({
  current: { data: undefined as LeaveBalanceHint | undefined, isLoading: false },
}))

vi.mock('../hooks/use-leave', () => ({
  useLeaveBalanceHint: () => hookResult.current,
}))

function hint(overrides: Partial<LeaveBalanceHint> = {}): LeaveBalanceHint {
  return {
    employee_id: 1,
    year: 2026,
    leave_type_id: 3,
    counts_balance: true,
    total_days: 12,
    used_days: 2,
    pending_days: 0,
    remaining_days: 10,
    missing_hire_date: false,
    ...overrides,
  }
}

function setHint(data: LeaveBalanceHint | undefined, isLoading = false) {
  hookResult.current = { data, isLoading }
}

/**
 * Cụm ba con số (còn lại · chờ duyệt · trừ đơn này) nay nằm trên MỘT dòng, ghép
 * từ nhiều thẻ `<strong>`/`<span>` để tô đậm được từng số. Khẳng định theo chuỗi
 * đã gộp: hỏi từng thẻ con thì mỗi lần đổi chỗ tô đậm là test đỏ oan, mà cái
 * người dùng đọc vốn là cả câu.
 */
function shownText() {
  return document.body.textContent?.replace(/\s+/g, ' ') ?? ''
}

describe('LeaveBalanceHintBox', () => {
  it('nhắc người dùng chọn loại nghỉ khi chưa chọn, thay vì để trống', () => {
    setHint(undefined)
    render(<LeaveBalanceHintBox leaveTypeId={0} year={2026} requestedDays={0} />)
    expect(screen.getByText(/Chọn loại nghỉ/)).toBeInTheDocument()
  })

  it('hiện số ngày còn lại trên tổng quỹ khi đủ phép', () => {
    setHint(hint())
    render(<LeaveBalanceHintBox leaveTypeId={3} year={2026} requestedDays={3} />)

    expect(shownText()).toContain('Phép năm 2026: còn 10/12 ngày')
    //  Đủ phép thì KHÔNG được dọa người dùng.
    expect(screen.queryByText(/vượt quỹ/)).not.toBeInTheDocument()
  })

  it('trừ luôn số ngày đang gõ, để người dùng không phải nhẩm', () => {
    setHint(hint({ remaining_days: 4, pending_days: 0 }))
    render(<LeaveBalanceHintBox leaveTypeId={3} year={2026} requestedDays={3} />)
    expect(shownText()).toContain('còn 4/12 ngày · trừ đơn này 3 còn 1')
  })

  it('trừ nửa ngày không để dấu phẩy động rò ra (4 − 0.1 ≠ 3.9000000000000004)', () => {
    setHint(hint({ remaining_days: 4 }))
    render(<LeaveBalanceHintBox leaveTypeId={3} year={2026} requestedDays={0.1} />)
    expect(shownText()).toContain('trừ đơn này 0.1 còn 3.9')
  })

  it('chưa gõ số ngày thì không hiện mảnh trừ — trừ 0 là câu thừa', () => {
    setHint(hint())
    render(<LeaveBalanceHintBox leaveTypeId={3} year={2026} requestedDays={0} />)
    expect(shownText()).not.toContain('trừ đơn này')
  })

  it('vượt quỹ thì KHÔNG hiện mảnh trừ — số âm ở đó vô nghĩa, đã có câu cảnh báo', () => {
    setHint(hint({ remaining_days: 2 }))
    render(<LeaveBalanceHintBox leaveTypeId={3} year={2026} requestedDays={5} />)
    expect(shownText()).not.toContain('trừ đơn này')
  })

  it('cảnh báo vượt quỹ và chỉ đường sang «Nghỉ không lương» — QĐ-NP2 không cho ứng phép', () => {
    setHint(hint({ remaining_days: 2 }))
    render(<LeaveBalanceHintBox leaveTypeId={3} year={2026} requestedDays={5} />)

    expect(screen.getByText(/vượt quỹ nên sẽ bị chặn lúc gửi duyệt/)).toBeInTheDocument()
    expect(screen.getByText(/Nghỉ không lương/)).toBeInTheDocument()
  })

  it('xin ĐÚNG BẰNG số còn lại thì KHÔNG cảnh báo — backend cũng cho qua', () => {
    //  Ranh giới `>` chứ không `>=`. Lệch một dấu ở đây là mọi người dùng nốt
    //  ngày phép cuối cùng đều thấy cảnh báo đỏ rồi vẫn nộp được — mất tin.
    setHint(hint({ remaining_days: 5 }))
    render(<LeaveBalanceHintBox leaveTypeId={3} year={2026} requestedDays={5} />)
    expect(screen.queryByText(/vượt quỹ/)).not.toBeInTheDocument()
  })

  it('nói rõ phần ĐANG CHỜ DUYỆT đã bị trừ, để người dùng không tưởng hệ thống tính sai', () => {
    setHint(hint({ pending_days: 3, remaining_days: 7 }))
    render(<LeaveBalanceHintBox leaveTypeId={3} year={2026} requestedDays={1} />)
    expect(shownText()).toContain('còn 7/12 ngày · chờ duyệt 3')
  })

  it('không hiện mảnh chờ duyệt khi không có đơn nào treo', () => {
    setHint(hint({ pending_days: 0 }))
    render(<LeaveBalanceHintBox leaveTypeId={3} year={2026} requestedDays={1} />)
    expect(shownText()).not.toContain('chờ duyệt')
  })

  it('loại nghỉ KHÔNG trừ quỹ thì nói thẳng là không giới hạn, không hiện số 0', () => {
    //  Hiện "còn lại 0 / 0 ngày" cho nghỉ không lương là câu SAI — người ta đọc
    //  thành hết phép và không dám nộp.
    setHint(hint({ counts_balance: false, total_days: 0, remaining_days: 0 }))
    render(<LeaveBalanceHintBox leaveTypeId={3} year={2026} requestedDays={90} />)

    expect(screen.getByText(/không giới hạn số ngày/)).toBeInTheDocument()
    expect(screen.queryByText(/vượt quỹ/)).not.toBeInTheDocument()
  })

  it('cảnh báo hồ sơ thiếu ngày vào làm — Q4: quỹ có thể THIẾU ngày thâm niên', () => {
    setHint(hint({ missing_hire_date: true }))
    render(<LeaveBalanceHintBox leaveTypeId={3} year={2026} requestedDays={1} />)
    expect(screen.getByText(/chưa có ngày vào làm/)).toBeInTheDocument()
  })

  it('không dựng số nào khi còn đang tra quỹ', () => {
    setHint(undefined, true)
    render(<LeaveBalanceHintBox leaveTypeId={3} year={2026} requestedDays={1} />)
    expect(screen.getByText(/Đang tra quỹ phép/)).toBeInTheDocument()
  })

  it('quỹ về nhưng RỖNG (0 ngày) vẫn hiện, và xin 1 ngày là cảnh báo ngay', () => {
    setHint(hint({ total_days: 0, remaining_days: 0, used_days: 0 }))
    render(<LeaveBalanceHintBox leaveTypeId={3} year={2026} requestedDays={1} />)
    expect(screen.getByText(/vượt quỹ/)).toBeInTheDocument()
  })

  it('nửa ngày phép cũng so đúng — không làm tròn lên rồi báo vượt oan', () => {
    setHint(hint({ remaining_days: 0.5 }))
    render(<LeaveBalanceHintBox leaveTypeId={3} year={2026} requestedDays={0.5} />)
    expect(screen.queryByText(/vượt quỹ/)).not.toBeInTheDocument()
  })
})
