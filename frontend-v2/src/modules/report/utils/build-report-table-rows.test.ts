import { describe, expect, it } from 'vitest'

import type { ReportGroupRow } from '../types/report-analytics'
import { buildReportTableRows, REPORT_TOTAL_ROW_KEY } from './build-report-table-rows'

const TOTALS = { current: { lines: 100, amount: 900 }, compare: { lines: 80, amount: 700 } }
const GROUPS: ReportGroupRow[] = [
  {
    key: 'kd',
    label: 'Kinh doanh',
    current: { lines: 30, amount: 500 },
    compare: { lines: 20, amount: 400 },
  },
  {
    key: 'kt',
    label: 'Kế toán',
    current: { lines: 70, amount: 100 },
    compare: { lines: 60, amount: 90 },
  },
]

describe('buildReportTableRows — Tổng row placement', () => {
  it('always puts Tổng first, even with no sort applied', () => {
    const rows = buildReportTableRows(TOTALS, GROUPS, null)
    expect(rows[0].key).toBe(REPORT_TOTAL_ROW_KEY)
    expect(rows[0].isTotal).toBe(true)
    expect(rows).toHaveLength(3)
  })

  it('stays first when sorting descending — the group with the largest metric would otherwise rank above it', () => {
    const rows = buildReportTableRows(TOTALS, GROUPS, 'lines', 'desc')
    expect(rows[0].key).toBe(REPORT_TOTAL_ROW_KEY)
    //  Ngay sau Tổng phải là "kt" (70 dòng) rồi "kd" (30 dòng).
    expect(rows[1].key).toBe('kt')
    expect(rows[2].key).toBe('kd')
  })

  it('stays first when sorting ascending too — the SMALLEST group would otherwise rank above it', () => {
    const rows = buildReportTableRows(TOTALS, GROUPS, 'lines', 'asc')
    expect(rows[0].key).toBe(REPORT_TOTAL_ROW_KEY)
    expect(rows[1].key).toBe('kd')
    expect(rows[2].key).toBe('kt')
  })

  it('never sums the groups into the total (multi-value dimensions can make totals ≠ Σgroups)', () => {
    //  100 ≠ 30 + 70 would coincidentally match GROUPS above, so assert the value
    //  is the TOTALS object passed in, not a computed sum — use a case where it diverges.
    const skewedTotals = { current: { lines: 55 }, compare: null }
    const skewedRows = buildReportTableRows(skewedTotals, GROUPS, null)
    expect(skewedRows[0].current.lines).toBe(55)
  })
})

describe('buildReportTableRows — edge cases', () => {
  it('returns just the Tổng row when there are no groups', () => {
    const rows = buildReportTableRows(TOTALS, [], 'lines')
    expect(rows).toHaveLength(1)
    expect(rows[0].key).toBe(REPORT_TOTAL_ROW_KEY)
  })

  it('treats a missing metric on a group as 0 when sorting, instead of throwing or sorting as NaN', () => {
    const partialGroups: ReportGroupRow[] = [
      { key: 'a', label: 'A', current: { lines: 5 }, compare: null },
      { key: 'b', label: 'B', current: {}, compare: null },
    ]
    const rows = buildReportTableRows(TOTALS, partialGroups, 'lines', 'desc')
    expect(rows.map((r) => r.key)).toEqual([REPORT_TOTAL_ROW_KEY, 'a', 'b'])
  })
})
