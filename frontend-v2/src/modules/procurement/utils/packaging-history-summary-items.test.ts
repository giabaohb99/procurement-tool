import { describe, expect, it } from 'vitest'

import type { PackagingHistoryStats } from '../types/packaging-cost-types'
import {
  buildHistorySummary,
  getLatestVsFirstRatio,
  type HistorySummaryItem,
} from './packaging-history-summary-items'

/** Số của CET0028 trong bản mẫu HTML (40 lần mua, 3 NCC). */
const stats = (over: Partial<PackagingHistoryStats> = {}): PackagingHistoryStats => ({
  purchase_count: 40,
  priced_count: 40,
  qty_total: 170427,
  weighted_avg: 2550.8123,
  min: 500,
  max: 2773,
  supplier_count: 3,
  first_date: '2025-01-06',
  last_date: '2025-11-08',
  amount_total: 434726851,
  code_count: 1,
  unit: 'Cái',
  first_price: 2477,
  last_price: 2477,
  ...over,
})

const single = { singleCode: true, mode: 'code' as const, selectedCount: 1 }
const byLabel = (items: HistorySummaryItem[]) =>
  Object.fromEntries(items.map((item) => [item.label, item]))

describe('buildHistorySummary — one code (the six cards of the HTML template)', () => {
  it('builds the same six cards, values and sub-lines as the template', () => {
    const items = buildHistorySummary(stats(), single)
    expect(items.map((item) => item.label)).toEqual([
      'Tổng số lần mua',
      'Tổng số lượng mua',
      'Tổng giá trị mua',
      'Giá thấp nhất – cao nhất',
      'Gần nhất so với lần đầu',
      'Số nhà cung cấp',
    ])
    const cards = byLabel(items)
    expect(cards['Tổng số lần mua']).toMatchObject({ value: '40', sub: '06/01/2025 → 08/11/2025' })
    expect(cards['Tổng số lượng mua']).toMatchObject({ value: '170.427', sub: 'Cái' })
    expect(cards['Tổng giá trị mua']).toMatchObject({ value: '434.726.851', sub: '40/40 lần có giá' })
    expect(cards['Giá thấp nhất – cao nhất']).toMatchObject({
      value: '500 – 2.773',
      sub: 'BQ gia quyền 2.550,81',
    })
    expect(cards['Gần nhất so với lần đầu']).toMatchObject({ value: '0,0%', sub: '2.477 → 2.477' })
    expect(cards['Gần nhất so với lần đầu'].tone).toBeUndefined()
    expect(cards['Số nhà cung cấp']).toMatchObject({ value: '3' })
  })

  it('colours a rise green-side ("up") and a drop red-side ("down"), with the sign on the percent', () => {
    const up = byLabel(buildHistorySummary(stats({ first_price: 623, last_price: 700 }), single))
    expect(up['Gần nhất so với lần đầu']).toMatchObject({ value: '+12,4%', tone: 'up', sub: '623 → 700' })
    const down = byLabel(buildHistorySummary(stats({ first_price: 700, last_price: 623 }), single))
    expect(down['Gần nhất so với lần đầu']).toMatchObject({ value: '-11,0%', tone: 'down' })
  })

  it('shows dashes, not zero or NaN, when nothing has a price (edge: every row has price 0)', () => {
    const cards = byLabel(
      buildHistorySummary(
        stats({
          priced_count: 0,
          weighted_avg: null,
          min: null,
          max: null,
          amount_total: 0,
          first_price: null,
          last_price: null,
        }),
        single,
      ),
    )
    expect(cards['Giá thấp nhất – cao nhất']).toMatchObject({ value: '—', sub: undefined })
    expect(cards['Gần nhất so với lần đầu']).toMatchObject({ value: '—', sub: undefined })
    expect(cards['Tổng giá trị mua']).toMatchObject({ value: '0', sub: '0/40 lần có giá' })
  })

  it('collapses a one-day span and leaves no unit line when the ledger has none', () => {
    const cards = byLabel(
      buildHistorySummary(
        stats({ first_date: '2026-03-01', last_date: '2026-03-01', unit: '' }),
        single,
      ),
    )
    expect(cards['Tổng số lần mua'].sub).toBe('01/03/2026')
    expect(cards['Tổng số lượng mua'].sub).toBeUndefined()
  })
})

describe('buildHistorySummary — many codes, all codes, by product', () => {
  it('drops price cards for several codes and says how many of them were ever bought', () => {
    const items = buildHistorySummary(stats({ code_count: 3 }), {
      singleCode: false,
      mode: 'code',
      selectedCount: 5,
    })
    expect(items.map((item) => item.label)).toEqual([
      'Số mã đã chọn',
      'Tổng số lần mua',
      'Tổng giá trị mua',
      'Số nhà cung cấp',
    ])
    expect(items[0]).toMatchObject({ value: '5', sub: '3 mã có lịch sử mua' })
  })

  it('counts every code with history when nothing is selected', () => {
    const [first] = buildHistorySummary(stats({ code_count: 1234 }), {
      singleCode: false,
      mode: 'code',
      selectedCount: 0,
    })
    expect(first).toMatchObject({ label: 'Số mã hàng', value: '1.234' })
  })

  it('switches to product cards in product mode', () => {
    const items = buildHistorySummary(stats({ code_count: 4 }), {
      singleCode: false,
      mode: 'product',
      selectedCount: 2,
    })
    expect(items.map((item) => item.label)).toEqual([
      'Số sản phẩm',
      'Mã vật tư liên quan',
      'Số dòng lịch sử',
      'Số nhà cung cấp',
    ])
    expect(items[0]).toMatchObject({ value: '2', sub: 'đã chọn' })
    expect(items[1].value).toBe('4')
  })

  it('has no date line when there are no purchases at all (edge: empty result)', () => {
    const items = buildHistorySummary(
      stats({
        purchase_count: 0,
        priced_count: 0,
        first_date: null,
        last_date: null,
        code_count: 0,
        supplier_count: 0,
      }),
      { singleCode: false, mode: 'code', selectedCount: 2 },
    )
    expect(byLabel(items)['Tổng số lần mua']).toMatchObject({ value: '0', sub: '' })
  })
})

describe('getLatestVsFirstRatio', () => {
  it('returns null instead of Infinity when the first price is 0 or missing', () => {
    expect(getLatestVsFirstRatio(stats({ first_price: 0 }))).toBeNull()
    expect(getLatestVsFirstRatio(stats({ first_price: null }))).toBeNull()
    expect(getLatestVsFirstRatio(stats({ last_price: null }))).toBeNull()
  })
})
