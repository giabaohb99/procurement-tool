import { describe, expect, it } from 'vitest'

import type { PackagingLastPricesRow } from '../types/packaging-cost-types'
import type { LastPricesFilters } from '../components/packaging-last-prices-toolbar'
import {
  buildLastPricesParams,
  isRecentMode,
  purchaseAt,
  purchaseGroupLabel,
  purchaseTrendTone,
  sortKeyOutsideN,
} from './packaging-last-prices'

function rowOf(...prices: (number | null)[]): PackagingLastPricesRow {
  return {
    code: 'CPT0105',
    name: 'Chai',
    group: 'Chai',
    unit: 'Cái',
    purchase_count: prices.length,
    purchases: prices.map((price, i) => ({
      date: `2026-0${6 - i}-01`,
      supplier_code: 'NCC01',
      supplier: 'Nhựa Á Châu',
      qty: 100,
      price,
    })),
    last_price: prices[0] ?? null,
    last_date: '2026-06-01',
    v12: null,
    v1n: null,
    avg: null,
  }
}

describe('purchaseTrendTone', () => {
  it('paints a purchase red when it is dearer than the next-older one, green when cheaper', () => {
    const row = rowOf(150, 130, 130, 140)
    expect(purchaseTrendTone(row, 0)).toContain('destructive') // 150 > 130: tăng = đỏ (người chủ chốt 27/11)
    expect(purchaseTrendTone(row, 2)).toContain('emerald') // 130 < 140: giảm = xanh
  })

  it('leaves equal prices, the oldest shown purchase and missing slots unpainted', () => {
    const row = rowOf(150, 130, 130)
    expect(purchaseTrendTone(row, 1)).toBeUndefined() // 130 = 130
    expect(purchaseTrendTone(row, 2)).toBeUndefined() // no older purchase to compare with
    expect(purchaseTrendTone(row, 4)).toBeUndefined() // slot is empty
    expect(purchaseTrendTone(rowOf(150, null), 0)).toBeUndefined() // missing price on one side
  })
})

describe('purchaseAt', () => {
  it('returns null for slots beyond the purchases we have', () => {
    const row = rowOf(150, 130)
    expect(purchaseAt(row, 1)?.price).toBe(130)
    expect(purchaseAt(row, 2)).toBeNull()
  })
})

describe('purchaseGroupLabel', () => {
  it('marks only the first purchase as the most recent', () => {
    expect(purchaseGroupLabel(0)).toBe('Lần 1 (gần nhất)')
    expect(purchaseGroupLabel(4)).toBe('Lần 5')
  })
})

const FILTERS: LastPricesFilters = {
  codes: [],
  groups: [],
  n: 5,
  scope: 'bom',
  suppliers: [],
  from: '',
  to: '',
  trend: 'all',
  minPct: 0,
  onlyPriced: true,
  bomOnly: false,
  showQty: false,
  all: false,
  trendAllLit: false,
}

describe('buildLastPricesParams', () => {
  it('sends only n, scope and only_priced when everything else is at its default', () => {
    expect(buildLastPricesParams(FILTERS, { by: '', dir: 'asc' })).toEqual({
      n: 5,
      only_priced: true,
      scope: 'bom',
    })
  })

  it('maps every option, chosen codes included', () => {
    const params = buildLastPricesParams(
      {
        ...FILTERS,
        n: 10,
        codes: ['NAP0085', 'CPT0105'],
        groups: ['Chai', 'Nắp'],
        suppliers: ['PHL', 'NCC02'],
        from: '2026-01-01',
        to: '2026-06-30',
        trend: 'up',
        minPct: 7.5,
        onlyPriced: false,
        bomOnly: true,
        scope: 'all',
      },
      { by: 'p2_price', dir: 'desc' },
    )
    expect(params).toEqual({
      n: 10,
      code: ['NAP0085', 'CPT0105'],
      group: ['Chai', 'Nắp'],
      supplier: ['PHL', 'NCC02'],
      date_from: '2026-01-01',
      date_to: '2026-06-30',
      trend: 'up',
      min_pct: 7.5,
      only_priced: false,
      bom_only: true,
      scope: 'all',
      sort_by: 'p2_price',
      sort_dir: 'desc',
    })
  })
})

describe('sortKeyOutsideN', () => {
  it('flags a per-purchase sort key beyond the shown purchases only', () => {
    expect(sortKeyOutsideN('p8_price', 5)).toBe(true)
    expect(sortKeyOutsideN('p5_date', 5)).toBe(false)
    expect(sortKeyOutsideN('v12', 3)).toBe(false)
    expect(sortKeyOutsideN('', 3)).toBe(false)
  })
})

describe('isRecentMode', () => {
  const base: LastPricesFilters = { ...FILTERS, codes: [], scope: 'all', onlyPriced: false }
  it('is on only with nothing chosen (n / showQty do not count)', () => {
    expect(isRecentMode(base)).toBe(true)
    expect(isRecentMode({ ...base, n: 10, showQty: true, trendAllLit: true })).toBe(true)
  })
  it('turns off for "Tất cả", a group chip or any other filter', () => {
    expect(isRecentMode({ ...base, all: true })).toBe(false)
    expect(isRecentMode({ ...base, groups: ['Chai'] })).toBe(false)
    expect(isRecentMode({ ...base, codes: ['NAP0085'] })).toBe(false)
    expect(isRecentMode({ ...base, suppliers: ['A'] })).toBe(false)
    expect(isRecentMode({ ...base, from: '2026-01-01' })).toBe(false)
    expect(isRecentMode({ ...base, trend: 'up' })).toBe(false)
    expect(isRecentMode({ ...base, minPct: 5 })).toBe(false)
    expect(isRecentMode({ ...base, scope: 'bom' })).toBe(false)
    expect(isRecentMode({ ...base, onlyPriced: true })).toBe(false)
    expect(isRecentMode({ ...base, bomOnly: true })).toBe(false)
  })
})
