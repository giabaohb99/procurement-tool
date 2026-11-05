import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import type { CustomsLine } from '../../types/customs'
import { CustomsLineCard } from './customs-line-card'

function line(overrides: Partial<CustomsLine> = {}): CustomsLine {
  return {
    id: 1201,
    batch_id: 3,
    source_row: 12,
    date_fixed: false,
    importer_id: 9,
    partner_id: 4,
    active_ingredient: 'ATRAZINE',
    formulation: '97% TC',
    product_kind: 2,
    product_kind_label: 'Nguyên liệu',
    reg_date: '2026-03-14',
    office_code: 'CHQ HP',
    line_no: 1,
    import_country: 'VN',
    importer_name: 'CÔNG TY CỔ PHẦN THUỐC BẢO VỆ THỰC VẬT SÀI GÒN',
    importer_tax_code: '0301234567',
    partner_name: 'SHANDONG BINNONG',
    origin_country: 'CN',
    product_name: 'Nguyên liệu thuốc trừ cỏ ATRAZINE 97% TECH',
    hs_code: '38089319',
    quantity: 20000,
    unit_code: 'KGM',
    price_usd: 2.8175,
    adj_price_usd: 2.9,
    effective_price_usd: 2.9,
    price_vnd_flat: 79_840_000,
    price_vnd_line_tax: null,
    price_nt: 2.8175,
    adj_price_nt: null,
    currency: 'USD',
    fx_rate: 1,
    usd_rate: 25_730,
    contract_no: 'HD-01',
    contract_date: '2026-02-01',
    incoterm: 'CIF',
    transport_mode: 2,
    transport_label: 'Đường biển',
    rate_import: 0,
    rate_excise: null,
    rate_vat: 5,
    rate_safeguard: null,
    tax_import: 0,
    tax_excise: null,
    tax_vat: 1000,
    tax_environment: null,
    tax_safeguard: null,
    ...overrides,
  }
}

describe('CustomsLineCard', () => {
  it('leads with the product name, keeps HS code and ID on the secondary line', () => {
    render(<CustomsLineCard row={line()} />)

    expect(screen.getByText('Nguyên liệu thuốc trừ cỏ ATRAZINE 97% TECH')).toBeInTheDocument()
    expect(screen.getByText(/HS 38089319/)).toBeInTheDocument()
    expect(screen.getByText(/ID 1201/)).toBeInTheDocument()
    expect(screen.getByText('14/03/2026')).toBeInTheDocument()
    expect(screen.getByText('CÔNG TY CỔ PHẦN THUỐC BẢO VỆ THỰC VẬT SÀI GÒN')).toBeInTheDocument()
  })

  it('keeps all four decimals of the USD price and the unit — rounding 2,8175 to 3 ruins a price lookup', () => {
    render(<CustomsLineCard row={line()} />)

    expect(screen.getByText('2,8175 USD/KGM')).toBeInTheDocument()
    expect(screen.getByText('2,9 USD/KGM')).toBeInTheDocument()
    expect(screen.getByText(/Lượng 20\.000 KGM/)).toBeInTheDocument()
  })

  it('omits the adjusted price when customs did not adjust it, instead of printing a dash price', () => {
    render(<CustomsLineCard row={line({ adj_price_usd: null })} />)

    expect(screen.queryByText(/Điều chỉnh/)).toBeNull()
  })

  it('shows a dash rather than "0" or blank when the declared price is missing', () => {
    render(<CustomsLineCard row={line({ price_usd: null, unit_code: '' })} />)

    expect(screen.getByText('— USD')).toBeInTheDocument()
  })

  it('flags a swapped day/month date the same way the table does', () => {
    render(<CustomsLineCard row={line({ date_fixed: true })} />)

    expect(screen.getByLabelText(/đảo ngày\/tháng/)).toBeInTheDocument()
  })

  it('falls back to the tax code when the importer name is empty, never starts with a blank line', () => {
    render(<CustomsLineCard row={line({ importer_name: '' })} />)

    expect(screen.getByText('0301234567')).toBeInTheDocument()
  })

  it('renders a placeholder for a line with no name at all', () => {
    render(<CustomsLineCard row={line({ product_name: '', reg_date: null })} />)

    expect(screen.getAllByText('—').length).toBeGreaterThan(0)
  })

  it('keeps the VND price unrounded with its label, and drops it when backend has none', () => {
    const { rerender } = render(<CustomsLineCard row={line()} />)
    expect(screen.getByText('79.840.000')).toBeInTheDocument()

    rerender(<CustomsLineCard row={line({ price_vnd_flat: null })} />)
    expect(screen.queryByText(/Giá VND/)).toBeNull()
  })
})
