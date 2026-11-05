import { render, screen, within } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { CustomsTariffRow } from '../../types/customs'
import { CustomsTariffCard } from './customs-tariff-card'

function tariff(overrides: Partial<CustomsTariffRow> = {}): CustomsTariffRow {
  return {
    hs_code: '38089319',
    name_vn: 'Thuốc diệt cỏ dạng khác',
    name_en: 'Other herbicides',
    unit: 'kg',
    rate_normal: '5 (a)',
    rate_mfn: 0,
    rate_vat: '*',
    fta: { ACFTA: 0, ATIGA: '', EVFTA: '3' },
    policy: 'Phải đăng ký thuốc BVTV trước khi nhập',
    ...overrides,
  }
}

function rateOf(label: string): string {
  const term = screen.getByText(label, { selector: 'dt' })
  return term.parentElement ? (within(term.parentElement).getByRole('definition').textContent ?? '') : ''
}

describe('CustomsTariffCard', () => {
  it('leads with the description, keeps HS code + unit below and rates as written in the schedule', () => {
    render(<CustomsTariffCard row={tariff()} />)

    expect(screen.getByText('Thuốc diệt cỏ dạng khác')).toBeInTheDocument()
    expect(screen.getByText('HS 38089319')).toBeInTheDocument()
    expect(screen.getByText(/ĐVT kg/)).toBeInTheDocument()
    //  "5 (a)" và "*" là chữ của biểu thuế — đổi sang số là mất ghi chú.
    expect(rateOf('Thông thường')).toBe('5 (a)')
    expect(rateOf('Ưu đãi (MFN)')).toBe('0')
    expect(rateOf('VAT')).toBe('*')
    expect(screen.getByText('Phải đăng ký thuốc BVTV trước khi nhập')).toBeInTheDocument()
  })

  it('a parent heading code with no rates drops the rate grid instead of three dashes', () => {
    render(
      <CustomsTariffCard
        row={tariff({ hs_code: '3808', rate_normal: null, rate_mfn: '', rate_vat: null, policy: '' })}
      />,
    )

    expect(screen.getByText('HS 3808')).toBeInTheDocument()
    expect(screen.queryByText('Thông thường')).toBeNull()
  })

  it('FTA card lists exactly the agreements asked for, dash for an empty cell', () => {
    render(<CustomsTariffCard row={tariff()} ftaKeys={['ACFTA', 'ATIGA', 'EVFTA', 'RCEP']} />)

    expect(rateOf('ACFTA')).toBe('0')
    expect(rateOf('ATIGA')).toBe('—')
    expect(rateOf('EVFTA')).toBe('3')
    expect(rateOf('RCEP')).toBe('—')
    expect(screen.queryByText('Thông thường')).toBeNull()
    expect(screen.queryByText(/Phải đăng ký/)).toBeNull()
  })

  it('FTA card on a row without any fta map does not crash', () => {
    render(
      <CustomsTariffCard
        row={tariff({ fta: undefined as unknown as CustomsTariffRow['fta'] })}
        ftaKeys={['ACFTA']}
      />,
    )

    expect(screen.getByText('HS 38089319')).toBeInTheDocument()
  })
})
