import { describe, expect, it } from 'vitest'

import type { PackagingLastPricesRow } from '../types/packaging-cost-types'
import type { LastPricesFilters } from '../components/packaging-last-prices-toolbar'
import {
  buildLastPricesParams,
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
    expect(purchaseTrendTone(row, 0)).toContain('emerald') // 150 > 130: tăng = xanh (người chủ chốt 20/11)
    expect(purchaseTrendTone(row, 2)).toContain('destructive') // 130 < 140: giảm = đỏ
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
  q: 'raw',
  group: '',
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
}

describe('buildLastPricesParams', () => {
  it('sends only n, scope and only_priced when everything else is at its default', () => {
    expect(buildLastPricesParams(FILTERS, '', { by: '', dir: 'asc' })).toEqual({
      n: 5,
      only_priced: true,
      scope: 'bom',
    })
  })

  it('maps every option and uses the debounced search text, not the raw input', () => {
    const params = buildLastPricesParams(
      {
        ...FILTERS,
        n: 10,
        group: 'Chai',
        suppliers: ['PHL', 'NCC02'],
        from: '2026-01-01',
        to: '2026-06-30',
        trend: 'up',
        minPct: 7.5,
        onlyPriced: false,
        bomOnly: true,
        scope: 'all',
      },
      ' nap ',
      { by: 'p2_price', dir: 'desc' },
    )
    expect(params).toEqual({
      n: 10,
      q: 'nap',
      group: 'Chai',
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
