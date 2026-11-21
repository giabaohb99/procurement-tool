import { describe, expect, it } from 'vitest'

import type { PackagingHistoryStats } from '../types/packaging-cost-types'
import {
  buildChartPoints,
  buildHistoryParams,
  buildHistorySearch,
  buildHistorySummary,
  EMPTY_HISTORY_FILTERS,
  PACKAGING_HISTORY_MAX_CODES,
  packagingHistoryHref,
  packagingHistoryProductHref,
  parseHistorySearch,
  priceAxisDomain,
} from './packaging-history'

const stats = (over: Partial<PackagingHistoryStats> = {}): PackagingHistoryStats => ({
  purchase_count: 6,
  priced_count: 5,
  qty_total: 6050,
  weighted_avg: 1234.5678,
  min: 100,
  max: 130,
  supplier_count: 2,
  first_date: '2026-01-01',
  last_date: '2026-05-01',
  ...over,
})

describe('parseHistorySearch', () => {
  it('reads a deep link with codes as code mode, trimming blanks and duplicates', () => {
    const parsed = parseHistorySearch(new URLSearchParams('codes=CPT0075, NAP0085,,CPT0075'))
    expect(parsed).toEqual({ mode: 'code', codes: ['CPT0075', 'NAP0085'], hh: [] })
  })

  it('treats a bare ?hh= deep link as product mode, but an explicit mode wins', () => {
    expect(parseHistorySearch(new URLSearchParams('hh=HH0713')).mode).toBe('product')
    expect(parseHistorySearch(new URLSearchParams('hh=HH0713&mode=code')).mode).toBe('code')
    expect(parseHistorySearch(new URLSearchParams('hh=HH1&codes=A')).mode).toBe('code')
  })

  it('survives an empty or hostile query string', () => {
    expect(parseHistorySearch(new URLSearchParams(''))).toEqual({ mode: 'code', codes: [], hh: [] })
    expect(parseHistorySearch(new URLSearchParams('codes=,,,&mode=zzz')).codes).toEqual([])
    expect(parseHistorySearch(new URLSearchParams('codes=%3Cscript%3E')).codes).toEqual([
      '<script>',
    ])
  })

  it('caps a huge list at the server limit instead of sending a request the server would reject', () => {
    const many = Array.from({ length: PACKAGING_HISTORY_MAX_CODES + 50 }, (_, i) => `C${i}`).join(
      ',',
    )
    expect(parseHistorySearch(new URLSearchParams({ codes: many })).codes).toHaveLength(
      PACKAGING_HISTORY_MAX_CODES,
    )
  })
})

describe('buildHistorySearch', () => {
  it('round-trips both lists so switching mode back and forth keeps the other selection', () => {
    const selection = { mode: 'code' as const, codes: ['A'], hh: ['HH1'] }
    expect(parseHistorySearch(new URLSearchParams(buildHistorySearch(selection)))).toEqual(
      selection,
    )
    const product = { mode: 'product' as const, codes: ['A'], hh: ['HH1'] }
    expect(parseHistorySearch(new URLSearchParams(buildHistorySearch(product)))).toEqual(product)
  })

  it('writes nothing for the default empty code mode, and keeps code mode readable when only hh is stored', () => {
    expect(buildHistorySearch({ mode: 'code', codes: [], hh: [] })).toEqual({})
    const onlyHh = { mode: 'code' as const, codes: [], hh: ['HH1'] }
    expect(parseHistorySearch(new URLSearchParams(buildHistorySearch(onlyHh))).mode).toBe('code')
    expect(buildHistorySearch({ mode: 'product', codes: [], hh: [] })).toEqual({ mode: 'product' })
  })
})

describe('packagingHistoryHref', () => {
  it('links one code and escapes it', () => {
    expect(packagingHistoryHref('CPT0075')).toBe(
      '/procurement/packaging-cost/history?codes=CPT0075',
    )
    expect(packagingHistoryHref('A&B=1')).toBe(
      '/procurement/packaging-cost/history?codes=A%26B%3D1',
    )
  })
})

describe('packagingHistoryProductHref', () => {
  it('links one product in product mode (bare ?hh= deep link) and escapes it', () => {
    expect(packagingHistoryProductHref('HH0417.1')).toBe(
      '/procurement/packaging-cost/history?hh=HH0417.1',
    )
    expect(packagingHistoryProductHref('A&B')).toBe('/procurement/packaging-cost/history?hh=A%26B')
    expect(
      parseHistorySearch(new URLSearchParams(packagingHistoryProductHref('HH1').split('?')[1])),
    ).toEqual({ mode: 'product', codes: [], hh: ['HH1'] })
  })
})

describe('buildHistoryParams', () => {
  const sort = { by: 'date', dir: 'desc' as const }

  it('sends only the list of the active mode', () => {
    const selection = { mode: 'product' as const, codes: ['A'], hh: ['HH1'] }
    expect(buildHistoryParams(selection, EMPTY_HISTORY_FILTERS, '', sort)).toEqual({
      mode: 'product',
      codes: undefined,
      hh_codes: ['HH1'],
      q: undefined,
      supplier: undefined,
      date_from: undefined,
      date_to: undefined,
      sort_by: 'date',
      sort_dir: 'desc',
    })
    const byCode = buildHistoryParams(
      { ...selection, mode: 'code' },
      EMPTY_HISTORY_FILTERS,
      '',
      sort,
    )
    expect(byCode.codes).toEqual(['A'])
    expect(byCode.hh_codes).toBeUndefined()
  })

  it('omits an empty selection (= all), blank search and the sort when the user cleared it', () => {
    const params = buildHistoryParams(
      { mode: 'code', codes: [], hh: [] },
      EMPTY_HISTORY_FILTERS,
      '   ',
      {
        by: '',
        dir: 'asc',
      },
    )
    expect(params).not.toHaveProperty('sort_by')
    expect(params.codes).toBeUndefined()
    expect(params.q).toBeUndefined()
  })

  it('passes supplier and date filters through', () => {
    const params = buildHistoryParams(
      { mode: 'code', codes: [], hh: [] },
      { q: 'x', suppliers: ['NCC1'], from: '2026-01-01', to: '2026-02-01' },
      ' nhựa ',
      sort,
    )
    expect(params).toMatchObject({
      supplier: ['NCC1'],
      date_from: '2026-01-01',
      date_to: '2026-02-01',
      q: 'nhựa',
    })
  })
})

describe('buildHistorySummary', () => {
  it('shows price figures only for a single code, and says how many rows are priced', () => {
    const labels = (items: { label: string }[]) => items.map((i) => i.label)
    expect(labels(buildHistorySummary(stats(), true))).toEqual([
      'Số lần mua',
      'Tổng SL',
      'Giá BQ gia quyền',
      'Thấp nhất',
      'Cao nhất',
      'Số NCC',
      'Khoảng ngày',
    ])
    expect(labels(buildHistorySummary(stats(), false))).toEqual([
      'Số lần mua',
      'Số NCC',
      'Khoảng ngày',
    ])
    expect(buildHistorySummary(stats(), false)[0].value).toBe('6 (5 có giá)')
    expect(buildHistorySummary(stats({ priced_count: 6 }), false)[0].value).toBe('6')
  })

  it('shows dashes, not zero, when nothing has a price or a quantity (edge: all rows price 0)', () => {
    const items = buildHistorySummary(
      stats({ priced_count: 0, weighted_avg: null, min: null, max: null, qty_total: null }),
      true,
    )
    const byLabel = Object.fromEntries(items.map((i) => [i.label, i.value]))
    expect(byLabel['Giá BQ gia quyền']).toBe('—')
    expect(byLabel['Thấp nhất']).toBe('—')
    expect(byLabel['Tổng SL']).toBe('0')
  })

  it('collapses a one-day range and drops the range when there are no purchases', () => {
    const one = buildHistorySummary(
      stats({ first_date: '2026-03-01', last_date: '2026-03-01' }),
      false,
    )
    expect(one.at(-1)).toEqual({ label: 'Khoảng ngày', value: '01/03/2026' })
    const none = buildHistorySummary(
      stats({ purchase_count: 0, priced_count: 0, first_date: null, last_date: null }),
      false,
    )
    expect(none.map((i) => i.label)).toEqual(['Số lần mua', 'Số NCC'])
  })
})

describe('chart helpers', () => {
  it('labels points with a Vietnamese date and keeps order', () => {
    const points = buildChartPoints([
      { date: '2026-01-05', price: 100, supplier_code: 'A', supplier: 'A', qty: 1 },
      { date: '2026-02-05', price: 110, supplier_code: 'A', supplier: 'A', qty: null },
    ])
    expect(points.map((p) => p.label)).toEqual(['05/01/2026', '05/02/2026'])
  })

  it('pads the axis so a flat or single price still has room, and never goes below zero', () => {
    const [low, high] = priceAxisDomain([100, 100, 100])
    expect(low).toBeLessThan(100)
    expect(high).toBeGreaterThan(100)
    expect(priceAxisDomain([5])[0]).toBeGreaterThanOrEqual(0)
    expect(priceAxisDomain([])).toEqual([0, 1])
  })

  it('does not stretch the axis down to zero for prices that move by a few percent', () => {
    const [low, high] = priceAxisDomain([2377, 2500])
    expect(low).toBeGreaterThan(2000)
    expect(high).toBeLessThan(2800)
  })
})
