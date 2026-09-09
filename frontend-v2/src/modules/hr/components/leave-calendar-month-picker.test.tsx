import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { LeaveCalendarMonthPicker } from './leave-calendar-month-picker'

/**
 * Bộ chọn tháng/năm của khổ điện thoại — nó thay cho HAI ô `Select` của khổ
 * rộng, nên phải nhảy được tới đúng chỗ hai ô kia nhảy tới.
 */
function renderPicker(anchor: Date, onJump = vi.fn()) {
  render(
    <LeaveCalendarMonthPicker anchor={anchor} label="Tháng 9/2026" onJump={onJump} />,
  )
  return { onJump, user: userEvent.setup() }
}

describe('LeaveCalendarMonthPicker', () => {
  it('chọn một tháng thì nhảy tới NGÀY 1 của tháng đó', async () => {
    //  Giữ nguyên ngày trong tháng sẽ tràn khi tháng đích ngắn hơn — mốc
    //  31/01 nhảy sang tháng 2 mà không nắn thì ra 03/03.
    const { onJump, user } = renderPicker(new Date(2026, 0, 31))

    await user.click(screen.getByRole('button', { name: /Tháng 9\/2026/ }))
    await user.click(screen.getByRole('button', { name: 'Tháng 2' }))

    expect(onJump).toHaveBeenCalledTimes(1)
    const jumped = onJump.mock.calls[0][0] as Date
    expect(jumped.getFullYear()).toBe(2026)
    expect(jumped.getMonth()).toBe(1)
    expect(jumped.getDate()).toBe(1)
  })

  it('đổi năm rồi mới chọn tháng thì nhảy đúng năm vừa đổi', async () => {
    const { onJump, user } = renderPicker(new Date(2026, 8, 9))

    await user.click(screen.getByRole('button', { name: /Tháng 9\/2026/ }))
    await user.click(screen.getByRole('button', { name: 'Năm trước' }))
    await user.click(screen.getByRole('button', { name: 'Tháng 3' }))

    const jumped = onJump.mock.calls[0][0] as Date
    expect(jumped.getFullYear()).toBe(2025)
    expect(jumped.getMonth()).toBe(2)
  })

  it('mở lại thì quay về NĂM ĐANG XEM, không giữ năm bấm dở lần trước', async () => {
    //  Nút ghi "Tháng 9/2026" mà bảng mở ra đứng ở 2024 thì người dùng không
    //  biết mình đang chọn cho năm nào.
    const { user } = renderPicker(new Date(2026, 8, 9))

    await user.click(screen.getByRole('button', { name: /Tháng 9\/2026/ }))
    await user.click(screen.getByRole('button', { name: 'Năm trước' }))
    expect(screen.getByText('2025')).toBeInTheDocument()

    await user.keyboard('{Escape}')
    await user.click(screen.getByRole('button', { name: /Tháng 9\/2026/ }))
    expect(screen.getByText('2026')).toBeInTheDocument()
  })

  it('không đi ra ngoài dải năm mà ô chọn năm khổ rộng đang bày', async () => {
    //  Hai bộ chọn của cùng một màn mà tới được hai khoảng thời gian khác nhau
    //  là thứ không ai báo lỗi nhưng ai gặp cũng thấy sai.
    const now = new Date().getFullYear()
    const { user } = renderPicker(new Date(now + 1, 0, 1))

    await user.click(screen.getByRole('button', { name: /Tháng 9\/2026/ }))
    expect(screen.getByRole('button', { name: 'Năm sau' })).toBeDisabled()
  })
})
