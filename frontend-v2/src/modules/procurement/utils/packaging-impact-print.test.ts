import { describe, expect, it } from 'vitest'

import type { PackagingImpactRequest } from '../types/packaging-cost-types'
import {
  buildImpactPrintSearch,
  buildImpactSummaryCards,
  describeImpactFilters,
  describeImpactSummaryDetail,
  IMPACT_PRINT_MAX_CODES,
  packagingImpactPrintHref,
  parseImpactPrintSearch,
} from './packaging-impact-print'

const parse = (query: string) => parseImpactPrintSearch(new URLSearchParams(query))

describe('buildImpactPrintSearch / parseImpactPrintSearch', () => {
  it('round-trips codes, assumed prices, date range, keyword and sort', () => {
    const request: PackagingImpactRequest = {
      codes: ['CPT0105', 'NAP0085'],
      assumed_prices: { CPT0105: 1250.5, NAP0085: 300 },
      date_from: '2026-01-01',
      date_to: '2026-05-31',
      q: 'b07',
      sort_by: 'diff_carton',
      sort_dir: 'desc',
    }
    expect(parse(buildImpactPrintSearch(request))).toEqual(request)
  })

  it('writes assumed prices as CODE:PRICE pairs and keeps a code that contains a colon', () => {
    expect(buildImpactPrintSearch({ codes: ['A'], assumed_prices: { A: 12 } })).toBe(
      'codes=A&assumed=A%3A12',
    )
    expect(parse('codes=X:Y&assumed=X:Y:5').assumed_prices).toEqual({ 'X:Y': 5 })
  })

  it('drops assumed prices that are zero, negative, NaN, text, for an unselected code, or malformed', () => {
    const parsed = parse(
      'codes=A,B&assumed=A:0&assumed=B:-5&assumed=B:abc&assumed=B:Infinity&assumed=C:9&assumed=:7&assumed=nocolon',
    )
    expect(parsed.assumed_prices).toBeUndefined()
    expect(parse('codes=A&assumed=A:0.5').assumed_prices).toEqual({ A: 0.5 })
  })

  it('returns no codes (link broken) instead of guessing', () => {
    expect(parse('').codes).toEqual([])
    expect(parse('codes=,, ,').codes).toEqual([])
  })

  it('removes duplicate and over-long codes and caps the list at the server limit', () => {
    expect(parse('codes=A,A, A ,B').codes).toEqual(['A', 'B'])
    expect(parse(`codes=${'x'.repeat(51)},ok`).codes).toEqual(['ok'])
    const many = Array.from({ length: IMPACT_PRINT_MAX_CODES + 20 }, (_, i) => `C${i}`)
    expect(parse(`codes=${many.join(',')}`).codes).toHaveLength(IMPACT_PRINT_MAX_CODES)
  })

  it('ignores bad dates, unknown sort keys and an over-long keyword', () => {
    const parsed = parse(`codes=A&date_from=2026-02-30&date_to=x&sort_by=password&sort_dir=desc&q=${'y'.repeat(900)}`)
    expect(parsed).toMatchObject({ codes: ['A'] })
    expect(parsed.date_from).toBeUndefined()
    expect(parsed.date_to).toBeUndefined()
    expect(parsed.sort_by).toBeUndefined()
    expect(parsed.q).toHaveLength(100)
    expect(parse('codes=A&sort_by=pct&sort_dir=sideways')).toMatchObject({ sort_by: 'pct', sort_dir: 'asc' })
  })

  it('builds the print link on the dedicated route', () => {
    expect(packagingImpactPrintHref({ codes: ['A', 'B'] })).toBe('/print/packaging-impact?codes=A%2CB')
  })
})

describe('describeImpactFilters', () => {
  it('lists assumed prices, the min-max date range and the product keyword', () => {
    expect(
      describeImpactFilters({
        codes: ['CPT0105', 'NAP0085'],
        assumed_prices: { CPT0105: 1250.5 },
        date_from: '2026-01-01',
        date_to: '2026-05-31',
        q: 'b07',
      }),
    ).toEqual([
      'Giá giả định: CPT0105 = 1.250,5',
      'Khoảng ngày tính min – max: 01/01/2026 – 31/05/2026',
      'Tìm sản phẩm: "b07"',
    ])
  })

  it('is empty when only codes are chosen and handles a one-sided date range', () => {
    expect(describeImpactFilters({ codes: ['A'] })).toEqual([])
    expect(describeImpactFilters({ codes: ['A'], date_to: '2026-05-31' })).toEqual([
      'Khoảng ngày tính min – max: đến 31/05/2026',
    ])
  })
})

describe('describeImpactSummaryDetail', () => {
  const kpis = {
    selected_count: 3,
    selected_by_group: { Chai: 2, Nắp: 1 },
    assumed_count: 1,
    affected_products: 284,
    increased: 0,
    decreased: 0,
    max_increase_carton: null,
    max_increase_bottle: null,
    max_increase_product: null,
  }

  it('matches the on-screen wording and is empty when there is nothing to say', () => {
    expect(describeImpactSummaryDetail(kpis)).toBe('2 chai · 1 nắp · 1 mã giả định')
    expect(describeImpactSummaryDetail({ ...kpis, selected_by_group: {}, assumed_count: 0 })).toBe('')
  })
})

describe('buildImpactSummaryCards', () => {
  const kpis = {
    selected_count: 3,
    selected_by_group: { Chai: 2, Nắp: 1 },
    assumed_count: 1,
    affected_products: 1284,
    increased: 10,
    decreased: 0,
    max_increase_carton: 20000,
    max_increase_bottle: 500,
    max_increase_product: {
      hh_code: 'HH0417.1',
      hh_name: 'Nước tương 450ml',
      diff_bottle: 500,
      diff_carton: 20000,
      carton_qty: 40,
    },
  }

  it('builds the three cards with the biggest per-carton rise highlighted green', () => {
    const [selected, affected, top] = buildImpactSummaryCards(kpis)
    expect(selected).toMatchObject({ label: 'Mã đã chọn', value: '3', sub: '2 chai · 1 nắp · 1 mã giả định' })
    expect(affected).toMatchObject({ label: 'Sản phẩm bị ảnh hưởng', value: '1.284', sub: 'Dùng ít nhất 1 mã đã chọn' })
    expect(top).toMatchObject({
      label: 'Tăng nhiều nhất /thùng',
      value: '+20.000',
      unit: 'VNĐ/thùng',
      sub: '+500 /chai',
      detail: 'HH0417.1 — Nước tương 450ml',
      tone: 'up',
    })
    expect(top.product?.hh_code).toBe('HH0417.1')
  })

  it('says "Đang lọc: x / M" only while filtering, and M stays the unfiltered count', () => {
    expect(buildImpactSummaryCards(kpis, 0)[1].sub).toBe('Đang lọc: 0 / 1.284')
    expect(buildImpactSummaryCards(kpis, 12)[1].sub).toBe('Đang lọc: 12 / 1.284')
  })

  it('shows the empty sentence, never a number, when no product rises', () => {
    const [, , top] = buildImpactSummaryCards({ ...kpis, max_increase_carton: -300, max_increase_product: null })
    expect(top).toMatchObject({ value: 'Không có sản phẩm tăng', unit: '', sub: '', detail: '', tone: undefined, product: null })
  })

  it('survives a backend that has not sent the new field yet, and a missing per-bottle figure', () => {
    const old = { ...kpis } as Partial<typeof kpis>
    delete old.max_increase_product
    expect(buildImpactSummaryCards(old as typeof kpis)[2].value).toBe('Không có sản phẩm tăng')
    const noBottle = { ...kpis, max_increase_product: { ...kpis.max_increase_product, diff_bottle: null } }
    expect(buildImpactSummaryCards(noBottle)[2]).toMatchObject({ value: '+20.000', sub: '' })
  })

  it('formats a sub-100.000 fractional rise with at most two decimals', () => {
    const fractional = { ...kpis, max_increase_product: { ...kpis.max_increase_product, diff_carton: 1234.567, diff_bottle: 85.5 } }
    expect(buildImpactSummaryCards(fractional)[2]).toMatchObject({ value: '+1.234,57', sub: '+85,5 /chai' })
  })
})
