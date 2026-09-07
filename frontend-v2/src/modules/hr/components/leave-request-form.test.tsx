import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { LeaveRequestForm } from './leave-request-form'
import { emptyLeaveForm, type LeaveFormValues } from '../utils/leave-form-values'
import { LEAVE_SESSION } from '../types/leave'

/**
 * Ô «Tổng số ngày» — con số tự tính KHÔNG được đè lên con số người dùng đã gõ.
 *
 * Lỗi báo 05/09/2026 (đơn NP025): người dùng gõ 4, mở lại tờ đơn thì ô hiện 3
 * (20/09 rơi vào Chủ nhật nên máy tính ra 3 ngày công), lưu xong lại nhảy về 4.
 * Nguyên do: cờ "đã gõ tay" là `useState` trong chính component, nên nó chết
 * theo lần mở màn — mở lại là cờ về `false` và con số gợi ý đè mất số đã lưu.
 */

const { useEstimateLeaveDays } = vi.hoisted(() => ({
  useEstimateLeaveDays: vi.fn(),
}))

vi.mock('../hooks/use-leave', () => ({
  useLeaveTypes: () => ({ data: { items: [{ id: 1, name: 'Phép năm' }] } }),
  useEstimateLeaveDays,
  useLeaveBalanceHint: () => ({ data: undefined, isLoading: true }),
}))

vi.mock('../hooks/use-employees', () => ({
  useEmployees: () => ({
    data: { items: [{ id: 7, code: 'NV007', full_name: 'Lê Thị B' }] },
  }),
}))

const { can } = vi.hoisted(() => ({ can: vi.fn(() => true) }))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can }),
}))

vi.mock('@/core/auth/use-auth', () => ({
  useAuth: () => ({ user: { id: 1, employee_id: 7, full_name: 'Lê Thị B' } }),
}))

/** Bọc form trong state thật — form là component có kiểm soát, cha giữ giá trị. */
function Harness({ initial }: { initial: LeaveFormValues }) {
  const [value, setValue] = useState(initial)
  return <LeaveRequestForm value={value} onChange={setValue} />
}

function daysInput() {
  return screen.getByLabelText(/Tổng số ngày/)
}

function formWith(overrides: Partial<LeaveFormValues>): LeaveFormValues {
  return { ...emptyLeaveForm(), leave_type_id: 1, ...overrides }
}

beforeEach(() => {
  useEstimateLeaveDays.mockReset()
  useEstimateLeaveDays.mockReturnValue({ data: { total_days: 3 } })
  can.mockReset()
  can.mockReturnValue(true)
})

describe('LeaveRequestForm — ô Tổng số ngày', () => {
  it('giữ nguyên số ngày đã lưu của đơn cũ, không để con số tự tính đè lên', () => {
    render(<Harness initial={formWith({ total_days: 4 })} />)
    expect(daysInput()).toHaveValue('4')
  })

  it('nói rõ đang nhập tay khi số của đơn khác số máy tính ra', () => {
    render(<Harness initial={formWith({ total_days: 4 })} />)
    expect(screen.getByText(/Hệ thống gợi ý 3 ngày/)).toBeInTheDocument()
  })

  it('tự điền khi ô còn trống — đó là lý do tồn tại của con số gợi ý', () => {
    render(<Harness initial={formWith({ total_days: 0 })} />)
    expect(daysInput()).toHaveValue('3')
    expect(screen.getByText(/Tự tính, đã trừ thứ Bảy/)).toBeInTheDocument()
  })

  it('người dùng gõ đè xong thì con số gợi ý mới KHÔNG được đè lại', async () => {
    const user = userEvent.setup()
    const { rerender } = render(<Harness initial={formWith({ total_days: 0 })} />)
    expect(daysInput()).toHaveValue('3')

    await user.clear(daysInput())
    await user.type(daysInput(), '4')
    await user.tab()
    expect(daysInput()).toHaveValue('4')

    //  Đổi ngày → backend trả con số gợi ý khác. Số người dùng gõ phải còn.
    useEstimateLeaveDays.mockReturnValue({ data: { total_days: 5 } })
    rerender(<Harness initial={formWith({ total_days: 0 })} />)
    expect(daysInput()).toHaveValue('4')
  })
})

describe('LeaveRequestForm — nghỉ theo GIỜ', () => {
  it('chọn «Theo giờ» thì mọc thêm ô giờ ở CẢ HAI đầu, hai ô ngày còn nguyên', async () => {
    //  Khách bác bản gộp hai ô ngày làm một (07/09/2026): nghỉ từ 14:00 ngày A
    //  đến 10:00 ngày B là tờ đơn có thật.
    const user = userEvent.setup()
    render(<Harness initial={formWith({})} />)

    await user.click(screen.getByRole('combobox', { name: 'Buổi bắt đầu' }))
    await user.click(screen.getByRole('option', { name: 'Theo giờ' }))

    expect(screen.getByLabelText('Từ giờ')).toBeInTheDocument()
    expect(screen.getByLabelText('Đến giờ')).toBeInTheDocument()
    expect(screen.getByText('Từ ngày')).toBeInTheDocument()
    expect(screen.getByText('Đến ngày')).toBeInTheDocument()
    //  Chọn một đầu là đầu kia theo luôn — backend đòi hai ô buổi giống nhau.
    expect(screen.getByRole('combobox', { name: 'Buổi kết thúc' })).toHaveTextContent(
      'Theo giờ',
    )
  })

  it('số ngày của đơn theo giờ là ô CHỈ XEM — không cho gõ đè', () => {
    useEstimateLeaveDays.mockReturnValue({ data: { total_days: 0.25 } })
    render(
      <Harness
        initial={formWith({
          from_session: LEAVE_SESSION.HOURLY,
          to_session: LEAVE_SESSION.HOURLY,
          from_time: '09:00',
          to_time: '11:00',
          total_days: 0.25,
        })}
      />,
    )
    expect(screen.queryByLabelText(/Tổng số ngày/)).not.toBeInTheDocument()
    expect(screen.getByText('0.25 ngày')).toBeInTheDocument()
  })

  it('đơn theo giờ LUÔN bám con số máy tính, kể cả khi mở lại đơn đã lưu', () => {
    //  Bắt được lúc test tay 07/09/2026: mở đơn theo giờ đã lưu 0.38 rồi đổi
    //  «Đến ngày», ô số ngày đứng im — vì con số đã lưu bị coi là "người dùng gõ
    //  tay", mà đơn theo giờ thì không có đường gõ tay nào cả.
    useEstimateLeaveDays.mockReturnValue({ data: { total_days: 2.31 } })
    render(
      <Harness
        initial={formWith({
          from_session: LEAVE_SESSION.HOURLY,
          to_session: LEAVE_SESSION.HOURLY,
          from_time: '09:30',
          to_time: '12:30',
          total_days: 0.38,
        })}
      />,
    )
    expect(screen.getByText('2.31 ngày')).toBeInTheDocument()
  })

  it('bỏ «Theo giờ» thì XÓA khoảng giờ đã nhập', async () => {
    const user = userEvent.setup()
    render(
      <Harness
        initial={formWith({
          from_session: LEAVE_SESSION.HOURLY,
          to_session: LEAVE_SESSION.HOURLY,
          from_time: '09:00',
          to_time: '11:00',
        })}
      />,
    )
    await user.click(screen.getByRole('combobox', { name: 'Buổi bắt đầu' }))
    await user.click(screen.getByRole('option', { name: 'Cả ngày' }))

    expect(screen.queryByLabelText('Đến giờ')).not.toBeInTheDocument()
  })
})

describe('LeaveRequestForm — lập hộ người khác', () => {
  it('có quyền đọc danh bạ thì hiện ô «Người nghỉ»', () => {
    render(<Harness initial={formWith({})} />)
    expect(screen.getByText('Người nghỉ')).toBeInTheDocument()
  })

  it('đơn MỚI thì ô «Người nghỉ» điền sẵn CHÍNH MÌNH', () => {
    //  Để trống kèm câu "mặc định là bạn" thì người dùng vẫn phải đoán đơn đứng
    //  tên ai — mà chỗ đó đáng ra là câu trả lời.
    render(<Harness initial={formWith({})} />)
    expect(screen.getByText('Lê Thị B (NV007)')).toBeInTheDocument()
  })

  it('KHÔNG có quyền thì giấu hẳn ô đó — đơn luôn đứng tên chính mình', () => {
    can.mockReturnValue(false)
    render(<Harness initial={formWith({})} />)
    expect(screen.queryByText('Người nghỉ')).not.toBeInTheDocument()
  })
})
