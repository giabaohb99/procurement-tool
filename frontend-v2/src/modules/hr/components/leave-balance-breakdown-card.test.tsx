import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { LeaveBalanceBreakdownCard } from './leave-balance-breakdown-card'
import { balanceFixture } from './leave-balance-fixture'

/**
 * Thẻ PHÂN RÃ quỹ — trả lời câu hỏi *"vì sao còn từng ấy ngày"*.
 *
 * Bảng danh sách chỉ trả lời được nửa: nó cho thấy tám con số nhưng không cho
 * thấy chúng nối với nhau thế nào.
 */
function stat(label: string) {
  const dt = screen.getByText(label)
  return dt.nextElementSibling?.textContent
}

describe('LeaveBalanceBreakdownCard', () => {
  it('hiện ĐỦ các số cấu thành, không bắt người xem đi dò nơi khác', () => {
    render(<LeaveBalanceBreakdownCard balance={balanceFixture()} />)

    expect(stat('Hạn mức')).toBe('12')
    expect(stat('Thâm niên')).toBe('+2')
    expect(stat('Chuyển năm trước')).toBe('+1')
    expect(stat('Điều chỉnh tay')).toBe('0')
    expect(stat('Đã nghỉ')).toBe('3')
    expect(stat('Chờ duyệt (đang giữ chỗ)')).toBe('2')
    expect(stat('Còn lại')).toBe('10')
  })

  it('nói ra TỔNG được nghỉ, không bắt tự cộng bốn số', () => {
    render(<LeaveBalanceBreakdownCard balance={balanceFixture()} />)
    const dong = screen.getByText(/Tổng được nghỉ/)
    expect(within(dong).getByText('15')).toBeInTheDocument()
  })

  it('số 0 hiện thành "0", KHÔNG thành dấu gạch như ngoài bảng', () => {
    //  Ngoài bảng dấu gạch để bảy cột bớt đặc. Ở đây người đọc đang lần theo
    //  một phép tính, và dấu gạch đọc ra là "không biết" chứ không phải "bằng
    //  không".
    render(
      <LeaveBalanceBreakdownCard
        balance={balanceFixture({ seniority_days: 0, carried_days: 0, used_days: 0 })}
      />,
    )

    expect(stat('Thâm niên')).toBe('0')
    expect(stat('Chuyển năm trước')).toBe('0')
    expect(stat('Đã nghỉ')).toBe('0')
  })

  it('điều chỉnh ÂM giữ nguyên dấu trừ, không ghép thành "+-2"', () => {
    render(<LeaveBalanceBreakdownCard balance={balanceFixture({ adjusted_days: -2 })} />)
    expect(stat('Điều chỉnh tay')).toBe('-2')
  })

  it('hết phép thì tô đỏ — đó là thứ Nhân sự cần thấy ngay', () => {
    render(
      <LeaveBalanceBreakdownCard balance={balanceFixture({ remaining_days: 0 })} />,
    )
    expect(screen.getByText('Còn lại').nextElementSibling).toHaveClass('text-destructive')
  })

  it('KHÔNG dùng màu primary cho con số — nó là màu nút, đọc ra như link', () => {
    render(<LeaveBalanceBreakdownCard balance={balanceFixture()} />)
    expect(screen.getByText('Còn lại').nextElementSibling).not.toHaveClass('text-primary')
  })

  it('chưa từng chỉnh tay thì không dựng dòng ghi chú rỗng', () => {
    render(<LeaveBalanceBreakdownCard balance={balanceFixture({ note: '  ' })} />)
    expect(screen.queryByText(/Ghi chú điều chỉnh/)).not.toBeInTheDocument()
  })

  it('ghi chú dài không dấu cách phải BẺ ĐƯỢC', () => {
    const dai = 'Buphepton2025theoquyetdinh'.repeat(20)
    render(<LeaveBalanceBreakdownCard balance={balanceFixture({ note: dai })} />)
    expect(screen.getByText(new RegExp(dai.slice(0, 40)))).toHaveClass('break-words')
  })
})
