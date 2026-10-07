// bao-CR-608 — biểu mẫu sửa một dòng hàng: chỉ gửi ô ĐÃ ĐỔI, ô suy ra để trống = hệ thống tự làm.
//
// Gửi đủ mọi ô là lỗi im lặng: lần lưu nào cũng ghi lại doanh nghiệp / đối tác và biến hoạt chất
// đang suy ra thành «do người nhập» (cờ `_from_file`), «Gắn lại nhãn» hết tác dụng với dòng đó.
import { describe, expect, it } from 'vitest'

import type { CustomsLine } from '../types/customs'
import {
  buildCustomsLinePatch,
  CUSTOMS_LINE_FIELDS,
  derivedPlaceholder,
  parseCustomsNumber,
  toCustomsLineForm,
} from './customs-line-form'

function makeLine(overrides: Partial<CustomsLine> = {}): CustomsLine {
  return {
    id: 7,
    batch_id: 1,
    source_row: 2,
    date_fixed: false,
    importer_id: 3,
    partner_id: 4,
    active_ingredient: 'ATRAZINE',
    formulation: '97%',
    active_ingredient_from_file: false,
    formulation_from_file: true,
    price_vnd_flat_from_file: false,
    price_vnd_line_tax_from_file: true,
    reg_date: '2026-01-13',
    office_code: 'HQHPKV3',
    line_no: 1,
    import_country: 'VN',
    importer_name: 'CÔNG TY A',
    importer_tax_code: '0500590269',
    partner_name: 'NOVADAN APS',
    origin_country: 'DK',
    product_name: 'ATRAZINE 97% TECH',
    hs_code: '38089990',
    quantity: 880,
    unit_code: 'KGM',
    price_usd: 17.3897,
    adj_price_usd: null,
    effective_price_usd: 17.3897,
    price_vnd_flat: 485437,
    price_vnd_line_tax: 480000,
    price_nt: 14.9,
    adj_price_nt: null,
    currency: 'EUR',
    fx_rate: 30448.32,
    usd_rate: 26089,
    contract_no: '770710',
    contract_date: null,
    incoterm: 'CIF',
    transport_mode: 2,
    rate_import: 0,
    rate_excise: null,
    rate_vat: 5,
    rate_safeguard: null,
    tax_import: 0,
    tax_excise: null,
    tax_vat: 19961918.592,
    tax_environment: null,
    tax_safeguard: null,
    ...overrides,
  }
}

describe('toCustomsLineForm', () => {
  it('leaves derived cells blank when the system computes them and keeps user-entered ones', () => {
    const form = toCustomsLineForm(makeLine())
    expect(form.active_ingredient).toBe('')
    expect(form.formulation).toBe('97%')
    expect(form.price_vnd_flat).toBe('')
    expect(form.price_vnd_line_tax).toBe('480000')
  })

  it('keeps zero as "0" and null as blank — 0% tax is not the same as not declared', () => {
    const form = toCustomsLineForm(makeLine())
    expect(form.rate_import).toBe('0')
    expect(form.rate_excise).toBe('')
    expect(form.transport_mode).toBe('2')
  })

  it('shows the derived value as a placeholder only for system-made cells', () => {
    const line = makeLine()
    expect(derivedPlaceholder(line, 'active_ingredient')).toBe('Tự động: ATRAZINE')
    expect(derivedPlaceholder(line, 'formulation')).toBe('')
    expect(derivedPlaceholder(makeLine({ price_vnd_flat: null }), 'price_vnd_flat')).toBe('Tự động')
  })

  it('covers every column the backend schema accepts, each once', () => {
    const keys = CUSTOMS_LINE_FIELDS.map((field) => field.key)
    expect(new Set(keys).size).toBe(keys.length)
    expect(keys).toHaveLength(36)
  })
})

describe('buildCustomsLinePatch', () => {
  it('sends nothing when nothing changed', () => {
    const initial = toCustomsLineForm(makeLine())
    expect(buildCustomsLinePatch(initial, { ...initial })).toEqual({ patch: {}, error: null })
  })

  it('sends only the changed cells, converted to numbers / null', () => {
    const initial = toCustomsLineForm(makeLine())
    const result = buildCustomsLinePatch(initial, {
      ...initial,
      price_usd: '21,5',
      rate_excise: '0',
      tax_vat: '',
      transport_mode: '',
      contract_date: '2025-11-20',
      partner_name: '  Bayer AG ',
    })
    expect(result).toEqual({
      error: null,
      patch: {
        price_usd: 21.5,
        rate_excise: 0,
        tax_vat: null,
        transport_mode: null,
        contract_date: '2025-11-20',
        partner_name: 'Bayer AG',
      },
    })
  })

  it('sends an empty string to hand a derived cell back to the system', () => {
    const initial = toCustomsLineForm(makeLine())
    expect(buildCustomsLinePatch(initial, { ...initial, formulation: '' }).patch).toEqual({ formulation: '' })
    expect(buildCustomsLinePatch(initial, { ...initial, price_vnd_line_tax: '' }).patch).toEqual({
      price_vnd_line_tax: null,
    })
  })

  it('blocks negative numbers, thousand separators, junk and fractional line numbers', () => {
    const initial = toCustomsLineForm(makeLine())
    for (const bad of ['-1', '1.000,5', 'abc', '1e5']) {
      expect(buildCustomsLinePatch(initial, { ...initial, quantity: bad }).error).toContain('Lượng')
    }
    expect(buildCustomsLinePatch(initial, { ...initial, line_no: '2.5' }).error).toContain('số nguyên')
  })

  it('blocks clearing a required cell', () => {
    const initial = toCustomsLineForm(makeLine())
    expect(buildCustomsLinePatch(initial, { ...initial, product_name: '   ' }).error).toContain('Tên hàng')
    expect(buildCustomsLinePatch(initial, { ...initial, reg_date: '' }).error).toContain('Ngày đăng ký')
  })
})

describe('parseCustomsNumber', () => {
  it('reads dot or comma decimals and returns null for blank', () => {
    expect(parseCustomsNumber('')).toBeNull()
    expect(parseCustomsNumber(' 12 ')).toBe(12)
    expect(parseCustomsNumber('0')).toBe(0)
    expect(parseCustomsNumber('3,25')).toBe(3.25)
    expect(parseCustomsNumber('3.25')).toBe(3.25)
    expect(Number.isNaN(parseCustomsNumber('1,000.5'))).toBe(true)
  })
})
