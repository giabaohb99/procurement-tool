import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ReportDailyRowCard } from './report-daily-row-card'

describe('ReportDailyRowCard', () => {
  it('shows the date with the full daily total, then goods and shipping parts', () => {
    render(
      <ReportDailyRowCard
        row={{ date: '2026-08-05', day: '05', goods: 120_000_000, shipping: 3_456_789, amount: 123_456_789 }}
      />,
    )

    expect(screen.getByText('05/08/2026')).toBeInTheDocument()
    //  Không rút gọn: tổng các ngày phải cộng ra đúng tổng ở tiêu đề hộp thoại.
    expect(screen.getByText('123.456.789 đ')).toBeInTheDocument()
    expect(screen.getByText('Hàng hóa 120.000.000 đ')).toBeInTheDocument()
    expect(screen.getByText('Vận chuyển 3.456.789 đ')).toBeInTheDocument()
  })

  it('a day with only shipping still prints "Hàng hóa 0 đ" rather than hiding the part', () => {
    render(
      <ReportDailyRowCard
        row={{ date: '2026-08-06', day: '06', goods: 0, shipping: 500_000, amount: 500_000 }}
      />,
    )

    expect(screen.getByText('Hàng hóa 0 đ')).toBeInTheDocument()
  })

  it('negative amounts (credit notes) keep their minus sign', () => {
    render(
      <ReportDailyRowCard
        row={{ date: '2026-08-07', day: '07', goods: -200_000, shipping: 0, amount: -200_000 }}
      />,
    )

    expect(screen.getByText('-200.000 đ')).toBeInTheDocument()
  })
})
