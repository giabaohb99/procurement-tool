import { describe, expect, it } from 'vitest'

import type { PackagingImpactRequest } from '../types/packaging-cost-types'
import {
  buildImpactPrintSearch,
  describeImpactFilters,
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
