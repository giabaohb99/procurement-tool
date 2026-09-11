import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ProfileLeaveCard } from './profile-leave-card'

//  Khóa quyền đổi theo từng bài — biến này là chỗ bài kiểm bẻ lái.
let hasBalanceKey = true
vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({
    can: (entity: string) => (entity === 'leave_balance' ? hasBalanceKey : true),
    canAny: () => true,
  }),
}))

//  Theo dõi hook đọc quỹ: điều quan trọng nhất của bài này không phải «vẽ ra gì»
//  mà là **có gọi API hay không** khi thiếu khóa.
const useLeaveBalances = vi.fn()
vi.mock('@/modules/hr/hooks/use-leave', () => ({
  useLeaveBalances: (...args: unknown[]) => useLeaveBalances(...args),
}))

function renderCard(props: { employeeId?: number; hasHireDate?: boolean } = {}) {
  return render(
    <MemoryRouter>
      <ProfileLeaveCard employeeId={props.employeeId ?? 7} hasHireDate={props.hasHireDate ?? true} />
    </MemoryRouter>,
  )
}

beforeEach(() => {
  hasBalanceKey = true
  useLeaveBalances.mockReset()
  useLeaveBalances.mockReturnValue({ data: { items: [], total: 0 }, isPending: false })
})

describe('ProfileLeaveCard', () => {
  /**
   * ⚠️ Bài quan trọng nhất của tệp này.
   *
   * Quỹ phép là dữ liệu của PHÂN HỆ KHÁC. Cứ mount là gọi thì người không được
   * cấp `leave_balance.read` ăn một toast 403 ngay lúc mở Trang cá nhân — chẳng
   * liên quan gì tới việc họ đang làm. Đây đúng là cái bẫy mà `CLAUDE.md` đã ghi
   * ở màn chi tiết Nhà cung cấp (`usePayables` không có nhánh tắt).
   */
  it('không gọi API quỹ phép khi thiếu khóa leave_balance.read', () => {
    hasBalanceKey = false

    renderCard()

    expect(useLeaveBalances).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ enabled: false }),
    )
  })

  it('ẩn hẳn thẻ khi thiếu khóa, không bày một thẻ rỗng kèm câu từ chối', () => {
    hasBalanceKey = false

    renderCard()

    expect(screen.queryByText(/Quỹ phép/)).not.toBeInTheDocument()
  })

  it('không gọi API khi tài khoản chưa gắn hồ sơ nhân sự', () => {
    renderCard({ employeeId: 0 })

    expect(useLeaveBalances).toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ enabled: false }),
    )
  })

  it('hiện SỐ CÒN LẠI kèm tổng được cấp', () => {
    useLeaveBalances.mockReturnValue({
      isPending: false,
      data: {
        total: 1,
        items: [
          { id: 1, leave_type_name: 'Phép năm', remaining_days: 3, total_days: 12, pending_days: 0 },
        ],
      },
    })

    renderCard()

    expect(screen.getByText('Phép năm')).toBeInTheDocument()
    expect(screen.getByText('3')).toBeInTheDocument()
    expect(screen.getByText(/\/ 12 ngày/)).toBeInTheDocument()
  })

  /** Quỹ phép đếm theo NỬA ngày — `2.5` không được làm tròn thành `3`. */
  it('giữ nửa ngày, và bỏ đuôi .0 của số nguyên', () => {
    useLeaveBalances.mockReturnValue({
      isPending: false,
      data: {
        total: 1,
        items: [
          { id: 1, leave_type_name: 'Phép năm', remaining_days: 2.5, total_days: 12, pending_days: 0 },
        ],
      },
    })

    renderCard()

    expect(screen.getByText('2.5')).toBeInTheDocument()
    expect(screen.getByText(/\/ 12 ngày/)).toBeInTheDocument()
  })

  /**
   * `pending_days` bị trừ khỏi `remaining_days` ngay lúc GỬI DUYỆT (chốt của
   * phân hệ Nghỉ phép). Người vừa nộp đơn thấy số tụt xuống mà chưa ai duyệt —
   * không nói ra thì họ tưởng hệ thống trừ nhầm.
   */
  it('nói rõ phần đang giữ chỗ khi có đơn chờ duyệt', () => {
    useLeaveBalances.mockReturnValue({
      isPending: false,
      data: {
        total: 1,
        items: [
          { id: 1, leave_type_name: 'Phép năm', remaining_days: 3, total_days: 12, pending_days: 2 },
        ],
      },
    })

    renderCard()

    expect(screen.getByText(/đang giữ chỗ/)).toBeInTheDocument()
  })

  it('không nhắc giữ chỗ khi không có đơn nào chờ duyệt', () => {
    renderCard()

    expect(screen.queryByText(/đang giữ chỗ/)).not.toBeInTheDocument()
  })

  /**
   * Thiếu NGÀY VÀO LÀM thì thâm niên tính bằng 0 năm và người này mất phần ngày
   * phép cộng thêm — không màn nào khác báo, mà chính chủ là người có động cơ đi
   * đòi sửa nhất.
   */
  it('cảnh báo khi hồ sơ chưa có ngày vào làm', () => {
    renderCard({ hasHireDate: false })

    expect(screen.getByText(/chưa có Ngày vào làm/)).toBeInTheDocument()
  })

  it('không cảnh báo khi hồ sơ đã có ngày vào làm', () => {
    renderCard({ hasHireDate: true })

    expect(screen.queryByText(/chưa có Ngày vào làm/)).not.toBeInTheDocument()
  })
})
