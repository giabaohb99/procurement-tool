import { describe, expect, it } from 'vitest'

import type { CustomsPesticideDetail } from '../types/customs-pesticide'
import {
  buildPesticidePayload,
  emptyPesticideInput,
  emptyPesticideUse,
  MAX_PESTICIDE_USES,
  toPesticideInput,
  validatePesticideInput,
} from './customs-pesticide-form'

const valid = () => ({ ...emptyPesticideInput(), trade_name: 'Mới 10EC', active_ingredient: 'Abamectin' })

describe('buildPesticidePayload', () => {
  it('trims text and turns empty dates into null (FastAPI rejects "" for a date)', () => {
    const body = buildPesticidePayload({ ...valid(), trade_name: '  A  ', registered_on: ' ', expires_on: '' })
    expect(body.trade_name).toBe('A')
    expect(body.registered_on).toBeNull()
    expect(body.expires_on).toBeNull()
  })

  it('drops usage rows that are blank after trimming, keeps a row with any one cell', () => {
    const blank = { ...emptyPesticideUse(), crop: '   ', usage: '\n' }
    const half = { ...emptyPesticideUse(), usage: 'Phun' }
    expect(buildPesticidePayload({ ...valid(), uses: [blank, half, emptyPesticideUse()] }).uses).toEqual([
      { crop: '', pest: '', dosage: '', pre_harvest_interval: '', usage: 'Phun' },
    ])
  })
})

describe('validatePesticideInput', () => {
  it.each([
    [{ trade_name: '   ' }, 'Nhập tên thuốc.'],
    [{ active_ingredient: '' }, 'Nhập hoạt chất.'],
    [{ source_url: 'javascript:alert(1)' }, /http:\/\//],
    [{ source_url: 'ftp://x' }, /http:\/\//],
    [{ registered_on: '2025-05-01', expires_on: '2024-05-01' }, /sau ngày cấp/],
  ])('blocks %j', (over, message) => {
    expect(validatePesticideInput({ ...valid(), ...over })).toMatch(message)
  })

  it('accepts a minimal drug, an http(s) link and a same-day expiry', () => {
    expect(validatePesticideInput(valid())).toBeNull()
    expect(validatePesticideInput({ ...valid(), source_url: 'HTTPS://x.vn' })).toBeNull()
    expect(validatePesticideInput({ ...valid(), registered_on: '2025-01-01', expires_on: '2025-01-01' })).toBeNull()
  })

  it('caps usage rows at the backend limit, not counting blank ones', () => {
    const row = { ...emptyPesticideUse(), crop: 'lúa' }
    expect(validatePesticideInput({ ...valid(), uses: Array(MAX_PESTICIDE_USES).fill(row) })).toBeNull()
    expect(validatePesticideInput({ ...valid(), uses: Array(MAX_PESTICIDE_USES + 1).fill(row) })).toMatch(/Tối đa/)
    const blanks = Array(MAX_PESTICIDE_USES + 5).fill(emptyPesticideUse())
    expect(validatePesticideInput({ ...valid(), uses: blanks })).toBeNull()
  })
})

describe('toPesticideInput', () => {
  it('turns null text columns from the backend into empty strings and drops use ids', () => {
    const detail = {
      id: 3, source_id: 1, trade_name: 'A', active_ingredient: 'B', concentration: '', pest_group: '',
      sector: '', registrant: '', registration_no: '', registered_on: null, expires_on: '2028-01-01',
      status: 2, status_label: 'Hết hiệu lực', toxicity: '', resistance: null, source_url: '', summary: null,
      use_count: 1, is_manual: false, banned: [],
      uses: [{ id: 9, crop: 'lúa', pest: null, dosage: '', pre_harvest_interval: '', usage: null }],
    } as unknown as CustomsPesticideDetail
    const input = toPesticideInput(detail)
    expect(input.resistance).toBe('')
    expect(input.summary).toBe('')
    expect(input.expires_on).toBe('2028-01-01')
    expect(input.uses).toEqual([{ crop: 'lúa', pest: '', dosage: '', pre_harvest_interval: '', usage: '' }])
    expect(input).not.toHaveProperty('id')
  })
})
