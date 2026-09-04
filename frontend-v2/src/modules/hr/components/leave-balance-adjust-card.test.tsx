import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { LeaveBalanceAdjustCard } from './leave-balance-adjust-card'
import { balanceFixture } from './leave-balance-fixture'
import { useLeaveBalanceAdjustForm } from '../hooks/use-leave-balance-adjust-form'
import type { LeaveBalance } from '../types/leave'

//  `mutate` phải gọi `onSettled` như TanStack thật, không thì khóa chống bấm
//  trùng (`useSingleFlight`) không nhả và bài sau xanh nhầm.
const mutate = vi.fn((_vars, options?: { onSettled?: () => void }) => options?.onSettled?.())
vi.mock('../hooks/use-leave', () => ({
  useAdjustLeaveBalance: () => ({ mutate, isPending: false }),
}))

/**
 * Dựng ĐÚNG cách trang thật ghép: nút Lưu ở trên (đầu trang), ô nhập ở dưới
 * (trong thẻ), hai chỗ chung một trạng thái. Kiểm riêng cái thẻ thì mất luôn
 * phần quan trọng nhất — cái nút.
 */
function Harness({ balance }: { balance: LeaveBalance }) {
  const form = useLeaveBalanceAdjustForm(balance)
  return (
    <>
      <button type="button" onClick={form.submit} disabled={!form.canSave}>
        Lưu điều chỉnh
      </button>
      <LeaveBalanceAdjustCard balance={balance} form={form} />
    </>
  )
}

function build(balance: LeaveBalance = balanceFixture()) {
  render(<Harness balance={balance} />)
  return screen.getByRole('button', { name: 'Lưu điều chỉnh' })
}

/**
 * Thẻ ĐIỀU CHỈNH TAY quỹ phép — thao tác nhạy cảm nhất của cả phân hệ: nó là
 * tặng ngày phép cho người khác.
 */
describe('LeaveBalanceAdjustCard', () => {
  it('KHÔNG lưu được khi chưa ghi lý do', () => {
    //  Phải truy được ai làm và vì sao. Backend chặn lớp thứ hai, nhưng chặn ở
    //  đây mới đúng chỗ — để backend chặn thì người dùng gõ xong mới ăn lỗi.
    expect(build()).toBeDisabled()
  })

  it('khoảng trắng KHÔNG tính là lý do', () => {
    expect(build(balanceFixture({ note: '   ' }))).toBeDisabled()
  })

  it('gõ lý do vào thì nút trên đầu trang MỞ ra theo', async () => {
    //  Nút và ô nhập nay ở hai component khác nhau; đứt trạng thái giữa chúng
    //  thì gõ đủ lý do mà nút vẫn khóa, không cách nào lưu được.
    const button = build()
    await userEvent.type(screen.getByLabelText(/Lý do điều chỉnh/), 'Bù phép tồn')
    expect(button).toBeEnabled()
  })

  it('bấm Lưu gửi đúng số và lý do đã CẮT khoảng trắng', async () => {
    const button = build(balanceFixture({ id: 12, adjusted_days: 2, note: '' }))
    await userEvent.type(screen.getByLabelText(/Lý do điều chỉnh/), '  Bù phép tồn  ')
    await userEvent.click(button)

    expect(mutate).toHaveBeenCalledWith(
      { id: 12, values: { adjusted_days: 2, note: 'Bù phép tồn' } },
      expect.anything(),
    )
  })

  it('nói rõ đang GHI ĐÈ lần trước, và «còn lại» sẽ thành bao nhiêu', () => {
    //  Cộng dồn thì bấm Lưu hai lần là gấp đôi, mà không ai đoán được điều đó
    //  từ giao diện — nên phải viết ra thành chữ.
    build(balanceFixture({ adjusted_days: 3, remaining_days: 10, note: 'Bù phép' }))

    expect(screen.getByText(/ghi đè/)).toBeInTheDocument()
    //  Số điều chỉnh nạp sẵn 3, còn lại 10 → gỡ 3 cũ rồi cộng 3 mới = vẫn 10.
    expect(screen.getByText('10')).toBeInTheDocument()
  })

  it('nạp sẵn số và lý do của lần chỉnh trước, không để ô trống', () => {
    //  Ô trống đọc ra là "chưa từng chỉnh", trong khi thực tế đang có 3 ngày —
    //  và vì ô này GHI ĐÈ, lưu với ô trống là xóa mất lần chỉnh cũ.
    build(balanceFixture({ adjusted_days: -2, note: 'Cấp nhầm, trừ lại' }))

    expect(screen.getByLabelText(/Số ngày điều chỉnh/)).toHaveValue(-2)
    expect(screen.getByLabelText(/Lý do điều chỉnh/)).toHaveValue('Cấp nhầm, trừ lại')
  })
})
