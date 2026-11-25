import { describe, expect, it } from 'vitest'

import type { PackagingHistoryParams } from '../types/packaging-cost-types'
import { PACKAGING_HISTORY_MAX_CODES } from './packaging-history'
import {
  buildHistoryPrintSearch,
  describeCappedPrint,
  describeHistoryFilters,
  HISTORY_PRINT_ROW_CAP,
  packagingHistoryPrintHref,
  parseHistoryPrintSearch,
  planHistoryPrintRows,
} from './packaging-history-print'

const parse = (query: string) => parseHistoryPrintSearch(new URLSearchParams(query))

describe('buildHistoryPrintSearch / parseHistoryPrintSearch', () => {
  it('round-trips every filter of the screen, including sort', () => {
    const params: PackagingHistoryParams = {
      mode: 'code',
      codes: ['CET0028', 'NAP0085'],
      q: 'chai 1l',
      supplier: ['NCC01', 'NCC02'],
      date_from: '2026-01-01',
      date_to: '2026-05-31',
      sort_by: 'price',
      sort_dir: 'asc',
    }
    expect(parse(buildHistoryPrintSearch(params))).toEqual(params)
  })

  it('round-trips product mode and keeps only the codes of the active mode', () => {
    const params: PackagingHistoryParams = { mode: 'product', hh_codes: ['HH0417.1', 'HH0500'] }
    const parsed = parse(buildHistoryPrintSearch(params))
    expect(parsed.mode).toBe('product')
    expect(parsed.hh_codes).toEqual(['HH0417.1', 'HH0500'])
    expect(parsed.codes).toBeUndefined()
    // Link tay có cả hai danh sách: chế độ code thì bỏ hh_codes, chế độ product thì bỏ codes.
    expect(parse('mode=code&codes=A&hh_codes=HH1')).toMatchObject({ codes: ['A'], hh_codes: undefined })
    expect(parse('mode=product&codes=A&hh_codes=HH1')).toMatchObject({ codes: undefined, hh_codes: ['HH1'] })
  })

  it('keeps a supplier code that contains a comma as ONE value', () => {
    const search = buildHistoryPrintSearch({ mode: 'code', supplier: ['A,B', 'C'] })
    expect(parse(search).supplier).toEqual(['A,B', 'C'])
  })

  it('falls back safely on hostile or empty input', () => {
    expect(parse('')).toEqual({ mode: 'code' })
    expect(parse('mode=<script>&codes=,,, ,&q=%20%20&supplier=&supplier=%20')).toEqual({ mode: 'code' })
    // Ngày sai khuôn / ngoài lịch bị bỏ, không gửi lên máy chủ.
    expect(parse('date_from=2026-13-45&date_to=hom-nay')).toEqual({ mode: 'code' })
    expect(parse('date_from=2026-02-30')).toEqual({ mode: 'code' })
    expect(parse('date_from=2028-02-29').date_from).toBe('2028-02-29')
    // Khóa xếp ngoài danh sách bị bỏ; chiều xếp lạ về giảm dần.
    expect(parse('sort_by=id;drop&sort_dir=asc')).toEqual({ mode: 'code' })
    expect(parse('sort_by=date&sort_dir=sideways')).toMatchObject({ sort_by: 'date', sort_dir: 'desc' })
  })

  it('keeps every sort key the server accepts, including warehouse and the product-mode columns', () => {
    for (const key of ['warehouse', 'hh_code', 'hh_name', 'role', 'amount']) {
      expect(parse(`mode=product&sort_by=${key}&sort_dir=asc`)).toMatchObject({ sort_by: key, sort_dir: 'asc' })
    }
  })

  it('caps codes at the server limit, drops duplicates and truncates the keyword', () => {
    const many = Array.from({ length: PACKAGING_HISTORY_MAX_CODES + 50 }, (_, i) => `C${i}`)
    expect(parse(`codes=${many.join(',')},C0`).codes).toHaveLength(PACKAGING_HISTORY_MAX_CODES)
    expect(parse(`q=${'x'.repeat(5000)}`).q).toHaveLength(100)
  })

  it('does not write empty filters into the URL', () => {
    expect(buildHistoryPrintSearch({ mode: 'code' })).toBe('mode=code')
    expect(packagingHistoryPrintHref({ mode: 'code', codes: ['CET0028'] })).toBe(
      '/print/packaging-history?mode=code&codes=CET0028',
    )
  })
})

describe('describeHistoryFilters', () => {
  it('lists only the conditions that are on, resolving supplier names', () => {
    expect(
      describeHistoryFilters(
        {
          mode: 'product',
          hh_codes: ['HH1'],
          supplier: ['NCC01', 'ZZZ'],
          date_from: '2026-01-01',
          date_to: '2026-05-31',
          q: 'chai',
        },
        [{ code: 'NCC01', name: 'Công ty Nhựa A' }],
      ),
    ).toEqual(['NCC: Công ty Nhựa A, ZZZ', 'Ngày mua: 01/01/2026 – 31/05/2026', 'Từ khóa: "chai"'])
  })

  it('is empty when only codes are chosen and handles a one-sided date range', () => {
    expect(describeHistoryFilters({ mode: 'code', codes: ['CET0028'] })).toEqual([])
    expect(describeHistoryFilters({ mode: 'code', date_from: '2026-03-01' })).toEqual(['Ngày mua: từ 01/03/2026'])
    expect(describeHistoryFilters({ mode: 'product', date_to: '2026-03-01' })).toEqual(['Ngày mua: đến 01/03/2026'])
  })
})

describe('planHistoryPrintRows', () => {
  it('prints everything up to the cap and flags anything above it', () => {
    expect(planHistoryPrintRows(9)).toEqual({ rows: 9, capped: false })
    expect(planHistoryPrintRows(HISTORY_PRINT_ROW_CAP)).toEqual({ rows: 5000, capped: false })
    expect(planHistoryPrintRows(HISTORY_PRINT_ROW_CAP + 1)).toEqual({ rows: 5000, capped: true })
  })

  it('treats a broken total (0, negative, NaN, fraction) as safe', () => {
    expect(planHistoryPrintRows(0)).toEqual({ rows: 0, capped: false })
    expect(planHistoryPrintRows(-5)).toEqual({ rows: 0, capped: false })
    expect(planHistoryPrintRows(Number.NaN)).toEqual({ rows: 0, capped: false })
    expect(planHistoryPrintRows(2.9)).toEqual({ rows: 2, capped: false })
  })

  it('tells the reader how many rows were printed out of how many', () => {
    expect(describeCappedPrint(12345)).toContain('12.345')
    expect(describeCappedPrint(12345)).toContain('5.000')
    expect(describeCappedPrint(12345, 'sản phẩm')).toContain('12.345 sản phẩm')
  })
})
