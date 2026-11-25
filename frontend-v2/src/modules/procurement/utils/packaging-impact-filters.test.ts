import { describe, expect, it } from 'vitest'

import type { PackagingImpactRequest } from '../types/packaging-cost-types'
import {
  EMPTY_IMPACT_FILTERS,
  appendImpactFilterSearch,
  countAdvancedFilters,
  countImpactFilters,
  describeImpactAdvancedFilters,
  impactFiltersToRequest,
  invalidImpactRanges,
  OVERVIEW_RANGE_FIELDS,
  overviewFiltersToParams,
  parseImpactFilterSearch,
  parseRangeText,
  type ImpactAdvancedFilters,
} from './packaging-impact-filters'
import { buildImpactPrintSearch, parseImpactPrintSearch } from './packaging-impact-print'

const filters = (over: Partial<ImpactAdvancedFilters> = {}): ImpactAdvancedFilters => ({
  ...EMPTY_IMPACT_FILTERS,
  ...over,
})

describe('parseRangeText', () => {
  it('reads Vietnamese numbers (dot = thousands, comma = decimal) and negatives', () => {
    expect(parseRangeText('1.234,5')).toBe(1234.5)
    expect(parseRangeText(' -50 ')).toBe(-50)
    expect(parseRangeText('0')).toBe(0)
  })

  it('treats blank, junk, partial typing, exponent, infinity and out-of-range as "not entered"', () => {
    for (const text of ['', '   ', '-', ',', 'abc', '1e5', 'Infinity', 'NaN', '1,2,3', '--1', '9999999999999', '1 2x']) {
      expect(parseRangeText(text), text).toBeNull()
    }
  })
})

describe('impactFiltersToRequest', () => {
  it('sends nothing for the empty filter set', () => {
    expect(impactFiltersToRequest(EMPTY_IMPACT_FILTERS)).toEqual({})
    expect(countImpactFilters(EMPTY_IMPACT_FILTERS)).toBe(0)
  })

  it('maps every group to its request fields and counts one condition per group', () => {
    const f = filters({
      trend: 'up',
      roles: [5, 1],
      cartonQty: { min: '12', max: '12' },
      diffBottle: { min: '-1.000', max: '' },
      diffCarton: { min: '', max: '5.000' },
      costNewBottle: { min: '100,5', max: '200' },
      warningsOnly: true,
    })
    expect(impactFiltersToRequest(f)).toEqual({
      trend: 'up',
      part_roles: [1, 5],
      warnings_only: true,
      carton_qty_min: 12,
      carton_qty_max: 12,
      diff_bottle_min: -1000,
      diff_carton_max: 5000,
      cost_new_bottle_min: 100.5,
      cost_new_bottle_max: 200,
    })
    expect(countImpactFilters(f)).toBe(7)
  })

  it('never sends a range whose "from" is greater than "to" (the server would answer 422) and flags it', () => {
    const f = filters({ diffBottle: { min: '10', max: '5' }, diffCarton: { min: '1', max: '2' } })
    expect(invalidImpactRanges(f)).toEqual(['diffBottle'])
    expect(impactFiltersToRequest(f)).toEqual({ diff_carton_min: 1, diff_carton_max: 2 })
    expect(countImpactFilters(f)).toBe(1)
  })

  it('drops fractional / negative / oversized carton quantities instead of sending a value the server rejects', () => {
    for (const text of ['1,5', '-1', '1000001']) {
      expect(impactFiltersToRequest(filters({ cartonQty: { min: text, max: '' } })), text).toEqual({})
    }
    expect(impactFiltersToRequest(filters({ cartonQty: { min: '0', max: '' } }))).toEqual({ carton_qty_min: 0 })
  })

  it('treats equal bounds as valid (an exact value)', () => {
    expect(invalidImpactRanges(filters({ cartonQty: { min: '24', max: '24' } }))).toEqual([])
  })
})

describe('overview variant (Tổng hợp theo sản phẩm)', () => {
  it('offers six ranges in column order and sends nothing for the empty set', () => {
    expect(OVERVIEW_RANGE_FIELDS.map((field) => field.key)).toEqual([
      'cartonQty',
      'costOldBottle',
      'costNewBottle',
      'diffBottle',
      'diffCarton',
      'pct',
    ])
    expect(overviewFiltersToParams(EMPTY_IMPACT_FILTERS)).toEqual({})
    expect(countAdvancedFilters(EMPTY_IMPACT_FILTERS, 'overview')).toBe(0)
  })

  it('maps roles to a comma list, ranges to *_min/_max and ignores the trend (it has its own chips)', () => {
    const f = filters({
      trend: 'up',
      roles: [5, 1],
      costOldBottle: { min: '1.000', max: '' },
      pct: { min: '-5,5', max: '10' },
      cartonQty: { min: '12', max: '' },
      warningsOnly: true,
    })
    expect(overviewFiltersToParams(f)).toEqual({
      part_roles: '1,5',
      warnings_only: true,
      carton_qty_min: 12,
      cost_old_bottle_min: 1000,
      pct_min: -5.5,
      pct_max: 10,
    })
    //  roles + warnings + cartonQty + costOldBottle + pct = 5; xu hướng không đếm ở màn này, có đếm ở Tác động giá.
    expect(countAdvancedFilters(f, 'overview')).toBe(5)
    expect(countAdvancedFilters(f, 'impact')).toBe(4)
  })

  it('flags an inverted range of the new fields and does not send it', () => {
    const f = filters({ pct: { min: '9', max: '1' }, costOldBottle: { min: '1', max: '2' } })
    expect(invalidImpactRanges(f, OVERVIEW_RANGE_FIELDS)).toEqual(['pct'])
    expect(overviewFiltersToParams(f)).toEqual({ cost_old_bottle_min: 1, cost_old_bottle_max: 2 })
  })

  it('keeps the two extra fields out of the Tác động giá request', () => {
    const f = filters({ costOldBottle: { min: '1', max: '' }, pct: { min: '2', max: '' } })
    expect(impactFiltersToRequest(f)).toEqual({})
    expect(countImpactFilters(f)).toBe(0)
  })
})

describe('print query string round trip', () => {
  const base: PackagingImpactRequest = {
    codes: ['CPT1'],
    trend: 'down',
    part_roles: [2, 3],
    carton_qty_min: 10,
    diff_bottle_min: -1000.5,
    diff_bottle_max: 0,
    cost_new_bottle_max: 99999,
    warnings_only: true,
    sort_by: 'part_cap',
    sort_dir: 'desc',
  }

  it('carries every advanced filter and the component sort key to the print page and back', () => {
    const parsed = parseImpactPrintSearch(new URLSearchParams(buildImpactPrintSearch(base)))
    expect(parsed).toMatchObject({ ...base, assumed_prices: undefined })
  })

  it('ignores hostile values in the URL', () => {
    const search = new URLSearchParams({
      codes: 'A',
      trend: 'sideways',
      part_roles: '0,9,x,3,3',
      carton_qty_min: '-5',
      diff_bottle_min: 'abc',
      diff_carton_max: '1e30',
      cost_new_bottle_min: '10',
      cost_new_bottle_max: '5',
      warnings_only: 'true',
      sort_by: 'part_hacker',
    })
    expect(parseImpactPrintSearch(search)).toEqual({
      codes: ['A'],
      assumed_prices: undefined,
      date_from: undefined,
      date_to: undefined,
      q: undefined,
      part_roles: [3],
    })
  })

  it('appends nothing and parses nothing for an unfiltered request', () => {
    const search = new URLSearchParams()
    appendImpactFilterSearch(search, { codes: ['A'] })
    expect([...search.keys()]).toEqual([])
    expect(parseImpactFilterSearch(new URLSearchParams())).toEqual({})
  })
})

describe('describeImpactAdvancedFilters', () => {
  it('describes each active condition in Vietnamese and stays empty when nothing is active', () => {
    expect(describeImpactAdvancedFilters({ codes: ['A'] })).toEqual([])
    const text = describeImpactAdvancedFilters({
      codes: ['A'],
      trend: 'up',
      part_roles: [1, 5],
      carton_qty_min: 12,
      carton_qty_max: 12,
      diff_carton_min: 1000,
      warnings_only: true,
    })
    expect(text).toEqual([
      'Xu hướng: Tăng',
      'Mã đã chọn ở vai trò: Chai, Thùng',
      'Quy cách thùng: 12 – 12 chai/thùng',
      'Tăng/giảm /thùng: từ 1.000 đ',
      'Chỉ sản phẩm có cảnh báo',
    ])
  })
})
