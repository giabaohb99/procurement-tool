import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { useState } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { LeaveRequestForm } from './leave-request-form'
import { emptyLeaveForm, type LeaveFormValues } from '../utils/leave-form-values'

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
  useEmployees: () => ({ data: { items: [] } }),
}))

vi.mock('@/core/authorization/use-permission', () => ({
  usePermission: () => ({ can: () => true }),
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
