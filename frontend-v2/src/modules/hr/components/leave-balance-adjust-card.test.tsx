import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { LeaveBalanceAdjustCard } from './leave-balance-adjust-card'
import { balanceFixture } from './leave-balance-fixture'

const mutate = vi.fn()
vi.mock('../hooks/use-leave', () => ({
  useAdjustLeaveBalance: () => ({ mutate, isPending: false }),
}))

/**
 * Thẻ ĐIỀU CHỈNH TAY quỹ phép — thao tác nhạy cảm nhất của cả phân hệ: nó là
 * tặng ngày phép cho người khác.
 */
describe('LeaveBalanceAdjustCard', () => {
  it('KHÔNG lưu được khi chưa ghi lý do', () => {
    //  Phải truy được ai làm và vì sao. Backend chặn lớp thứ hai, nhưng chặn ở
    //  đây mới đúng chỗ — để backend chặn thì người dùng gõ xong mới ăn lỗi.
    render(<LeaveBalanceAdjustCard balance={balanceFixture()} />)
    expect(screen.getByRole('button', { name: 'Lưu điều chỉnh' })).toBeDisabled()
  })

  it('khoảng trắng KHÔNG tính là lý do', () => {
    render(<LeaveBalanceAdjustCard balance={balanceFixture({ note: '   ' })} />)
    expect(screen.getByRole('button', { name: 'Lưu điều chỉnh' })).toBeDisabled()
  })

  it('nói rõ đang GHI ĐÈ lần trước, và «còn lại» sẽ thành bao nhiêu', () => {
    //  Cộng dồn thì bấm Lưu hai lần là gấp đôi, mà không ai đoán được điều đó
    //  từ giao diện — nên phải viết ra thành chữ.
    render(
      <LeaveBalanceAdjustCard
        balance={balanceFixture({ adjusted_days: 3, remaining_days: 10, note: 'Bù phép' })}
      />,
    )

    expect(screen.getByText(/ghi đè/)).toBeInTheDocument()
    //  Số điều chỉnh nạp sẵn 3, còn lại 10 → gỡ 3 cũ rồi cộng 3 mới = vẫn 10.
    expect(screen.getByText('10')).toBeInTheDocument()
  })

  it('nạp sẵn số và lý do của lần chỉnh trước, không để ô trống', () => {
    //  Ô trống đọc ra là "chưa từng chỉnh", trong khi thực tế đang có 3 ngày —
    //  và vì ô này GHI ĐÈ, lưu với ô trống là xóa mất lần chỉnh cũ.
    render(
      <LeaveBalanceAdjustCard
        balance={balanceFixture({ adjusted_days: -2, note: 'Cấp nhầm, trừ lại' })}
      />,
    )

    expect(screen.getByLabelText(/Số ngày điều chỉnh/)).toHaveValue(-2)
    expect(screen.getByLabelText(/Lý do điều chỉnh/)).toHaveValue('Cấp nhầm, trừ lại')
  })
})
