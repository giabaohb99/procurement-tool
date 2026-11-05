import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { CustomsSeriesPoint } from '../../types/customs'
import { CustomsPricePeriodCard } from './customs-price-period-card'

function point(overrides: Partial<CustomsSeriesPoint & { isBest: boolean }> = {}) {
  return {
    period: '2026-03',
    label: 'T3/2026',
    count: 18,
    qty: 52_000.25,
    min: 2.1,
    max: 4.25,
    p25: 2.5,
    p75: 3.2,
    wavg: 2.8175,
    low_data: false,
    isBest: false,
    ...overrides,
  }
}

function statValue(label: string): string {
  const term = screen.getByText(label, { selector: 'dt' })
  return term.parentElement ? (within(term.parentElement).getByRole('definition').textContent ?? '') : ''
}

describe('CustomsPricePeriodCard', () => {
  it('puts the weighted average next to the period and lists min / common range / max unrounded', () => {
    render(
      <CustomsPricePeriodCard point={point()} unit="kg" commonRange="2,5 – 3,2" note="" />,
    )

    expect(screen.getByText('T3/2026')).toBeInTheDocument()
    expect(screen.getByText('2,8175')).toBeInTheDocument()
    expect(screen.getByText('USD/kg BQ')).toBeInTheDocument()
    expect(statValue('Thấp nhất')).toBe('2,1')
    expect(statValue('Phổ biến (25–75%)')).toBe('2,5 – 3,2')
    expect(statValue('Cao nhất')).toBe('4,25')
    expect(statValue('Số dòng')).toBe('18')
    expect(statValue('Tổng lượng (kg)')).toBe('52.000,25')
  })

  it('an empty period shows dashes and its note, never 0 USD', () => {
    render(
      <CustomsPricePeriodCard
        point={point({ count: 0, qty: 0, min: null, max: null, wavg: null })}
        unit=""
        commonRange="—"
        note="Không có dữ liệu"
      />,
    )

    expect(screen.getByText('USD BQ')).toBeInTheDocument()
    expect(statValue('Thấp nhất')).toBe('—')
    expect(statValue('Tổng lượng')).toBe('—')
    expect(screen.getByText('Không có dữ liệu')).toBeInTheDocument()
  })

  it('shows the best-price note for the best period', () => {
    render(
      <CustomsPricePeriodCard
        point={point({ isBest: true })}
        unit="kg"
        commonRange="2,5 – 3,2"
        note="Giá tốt nhất (đủ dữ liệu)"
      />,
    )

    expect(screen.getByText('Giá tốt nhất (đủ dữ liệu)')).toBeInTheDocument()
  })
})
