import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { PESTICIDE_STATUS, type CustomsPesticide } from '../../types/customs-pesticide'
import { CustomsPesticideCard } from './customs-pesticide-card'

function pesticide(overrides: Partial<CustomsPesticide> = {}): CustomsPesticide {
  return {
    id: 7,
    source_id: 70,
    trade_name: 'Atranex 80WP',
    active_ingredient: 'Atrazine',
    concentration: '800g/kg',
    pest_group: 'Thuốc trừ cỏ',
    sector: 'Nông nghiệp',
    registrant: 'Công ty TNHH ADC',
    registration_no: 'BVTV-123/24',
    registered_on: '2024-01-01',
    expires_on: '2029-01-01',
    status: PESTICIDE_STATUS.active,
    status_label: 'Còn hiệu lực',
    toxicity: '',
    resistance: '',
    source_url: '',
    summary: '',
    use_count: 3,
    is_manual: false,
    banned: [],
    ...overrides,
  }
}

describe('CustomsPesticideCard', () => {
  it('leads with the trade name, then ingredient, then registrant and registration number', () => {
    render(<CustomsPesticideCard row={pesticide()} />)

    expect(screen.getByText('Atranex 80WP')).toBeInTheDocument()
    expect(screen.getByText('Atrazine · 800g/kg')).toBeInTheDocument()
    expect(screen.getByText('Công ty TNHH ADC · Số ĐK BVTV-123/24')).toBeInTheDocument()
    expect(screen.getByText('Còn hiệu lực')).toBeInTheDocument()
    expect(screen.getByText('Hết hạn 01/01/2029')).toBeInTheDocument()
    expect(screen.getByText('3 phạm vi sử dụng')).toBeInTheDocument()
  })

  it('shows every banned ingredient as its own badge — a hit here means the catalog let one slip', () => {
    render(
      <CustomsPesticideCard
        row={pesticide({
          banned: [
            { id: 1, name: 'Paraquat', cas_no: '', banned_year: 2026, legal_basis: '' },
            { id: 2, name: 'Carbofuran', cas_no: '', banned_year: null, legal_basis: '' },
          ],
        })}
      />,
    )

    expect(screen.getByText('Cấm: Paraquat')).toBeInTheDocument()
    expect(screen.getByText('Cấm: Carbofuran')).toBeInTheDocument()
  })

  it('marks manually added drugs, like the table does', () => {
    render(<CustomsPesticideCard row={pesticide({ is_manual: true })} />)

    expect(screen.getByText('Tự thêm')).toBeInTheDocument()
  })

  it('works with the brief shape of the related block (no registration fields) without printing "undefined"', () => {
    const { container } = render(
      <CustomsPesticideCard
        row={{
          id: 8,
          trade_name: 'Cỏ Cháy 20SL',
          pest_group: 'Thuốc trừ cỏ',
          active_ingredient: 'Glufosinate',
          registrant: 'Công ty B',
          status: PESTICIDE_STATUS.expired,
          status_label: 'Hết hiệu lực',
        }}
      />,
    )

    expect(container.textContent).not.toMatch(/undefined|null|NaN/)
    expect(screen.queryByText(/Số ĐK/)).toBeNull()
    expect(screen.queryByText(/phạm vi sử dụng/)).toBeNull()
    expect(screen.getByText('Hết hiệu lực')).toBeInTheDocument()
  })

  it('hides the "still valid" badge only when asked, never an "expired" one', () => {
    const { rerender } = render(<CustomsPesticideCard row={pesticide()} hideActiveStatus />)
    expect(screen.queryByText('Còn hiệu lực')).toBeNull()

    rerender(
      <CustomsPesticideCard
        row={pesticide({ status: PESTICIDE_STATUS.expired, status_label: 'Hết hiệu lực' })}
        hideActiveStatus
      />,
    )
    expect(screen.getByText('Hết hiệu lực')).toBeInTheDocument()
  })

  it('drops the registrant on the "same company" tab but keeps the registration number', () => {
    render(<CustomsPesticideCard row={pesticide()} hideRegistrant />)

    expect(screen.queryByText(/Công ty TNHH ADC/)).toBeNull()
    expect(screen.getByText('Số ĐK BVTV-123/24')).toBeInTheDocument()
  })

  it('zero uses means no usage line, not "0 phạm vi sử dụng"', () => {
    render(<CustomsPesticideCard row={pesticide({ use_count: 0, expires_on: null })} />)

    expect(screen.queryByText(/phạm vi sử dụng/)).toBeNull()
    expect(screen.queryByText(/Hết hạn/)).toBeNull()
  })
})
