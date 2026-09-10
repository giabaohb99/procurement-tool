import { describe, expect, it } from 'vitest'

import {
  buildLandedCostParams,
  LANDED_COST_VIEWS,
  landedCostViewLabel,
} from './import-landed-cost'

const EMPTY = { codes: '', date_from: '', date_to: '' }

describe('buildLandedCostParams', () => {
  it('drops the date range entirely when order codes are given', () => {
    //  Gửi kèm khoảng ngày thì lô đặt ngoài khoảng biến mất, dù người dùng gõ
    //  đúng mã của nó — đúng thứ khiến người ta tưởng đơn bị xóa.
    expect(
      buildLandedCostParams({ codes: 'PO-001', date_from: '2026-01-01', date_to: '2026-12-31' }),
    ).toEqual({ codes: 'PO-001' })
  })

  it('trims each code and drops empty segments', () => {
    expect(buildLandedCostParams({ ...EMPTY, codes: ' PO-1 , , PO-2 ,' })).toEqual({
      codes: 'PO-1,PO-2',
    })
  })

  it('falls back to the date range when the codes box holds only separators', () => {
    //  " , , " không phải là một mã đơn nào cả; coi nó là "có lọc mã" thì backend
    //  nhận chuỗi rỗng và trả về không có gì, không ai hiểu vì sao.
    expect(
      buildLandedCostParams({ codes: ' , , ', date_from: '2026-03-01', date_to: '2026-03-31' }),
    ).toEqual({ date_from: '2026-03-01', date_to: '2026-03-31' })
  })

  it('sends only the half of the range that was filled in', () => {
    expect(buildLandedCostParams({ ...EMPTY, date_from: '2026-05-01' })).toEqual({
      date_from: '2026-05-01',
    })
    expect(buildLandedCostParams({ ...EMPTY, date_to: '2026-05-31' })).toEqual({
      date_to: '2026-05-31',
    })
  })

  it('returns an empty object when nothing is filled in', () => {
    expect(buildLandedCostParams(EMPTY)).toEqual({})
  })

  it('omits company_id when it is empty or missing', () => {
    expect(buildLandedCostParams(EMPTY, '')).toEqual({})
    expect(buildLandedCostParams(EMPTY, undefined)).toEqual({})
    expect(buildLandedCostParams(EMPTY, '3')).toEqual({ company_id: '3' })
  })

  it('keeps company_id alongside either filter shape', () => {
    expect(buildLandedCostParams({ ...EMPTY, codes: 'PO-9' }, '2')).toEqual({
      codes: 'PO-9',
      company_id: '2',
    })
    expect(buildLandedCostParams({ ...EMPTY, date_from: '2026-01-01' }, '2')).toEqual({
      date_from: '2026-01-01',
      company_id: '2',
    })
  })
})

describe('landedCostViewLabel', () => {
  it('names every view declared in LANDED_COST_VIEWS', () => {
    for (const view of LANDED_COST_VIEWS) {
      expect(landedCostViewLabel(view.value)).toBe(view.label)
    }
  })
})
