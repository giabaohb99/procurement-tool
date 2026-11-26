import { describe, expect, it } from 'vitest'

import type { PackagingHistorySeriesLine } from '../types/packaging-cost-types'
import {
  assignHistoryLineStyles,
  buildSeriesRows,
  HISTORY_LINE_STYLES,
  historyLineLegend,
  seriesAxisDomain,
} from './packaging-history-series'

const line = (
  code: string,
  role: number,
  points: [string, number][],
): PackagingHistorySeriesLine => ({
  code,
  name: `Tên ${code}`,
  role,
  points: points.map(([date, price]) => ({ date, price })),
})

describe('packaging history series by component', () => {
  it('builds the legend as role + code', () => {
    expect(historyLineLegend({ role: 1, code: 'CPT0105' })).toBe('Chai · CPT0105')
    expect(historyLineLegend({ role: 4, code: 'NHT01' })).toBe('Nhãn thùng · NHT01')
  })

  it('colours by role, not by order of presence', () => {
    const styles = assignHistoryLineStyles([line('NAP', 2, []), line('THG', 5, [])])
    expect(styles[0]).toBe(HISTORY_LINE_STYLES[1])
    expect(styles[1]).toBe(HISTORY_LINE_STYLES[4])
    expect(styles[1].dash).not.toBe('')
  })

  it('gives a second code of the same role the next free style', () => {
    const styles = assignHistoryLineStyles([line('A', 1, []), line('B', 1, [])])
    expect(styles[0]).toBe(HISTORY_LINE_STYLES[0])
    expect(styles[1]).toBe(HISTORY_LINE_STYLES[1])
  })

  it('merges lines into date-ascending rows, one row per purchase of a code on the same day', () => {
    const rows = buildSeriesRows([
      line('CPT', 1, [['2026-01-01', 100], ['2026-02-01', 110], ['2026-02-01', 120]]),
      line('NAP', 2, [['2026-02-01', 200], ['2026-03-01', 210]]),
    ])
    expect(rows.map((row) => [row.date, row.line0, row.line1])).toEqual([
      ['2026-01-01', 100, undefined],
      ['2026-02-01', 110, 200],
      ['2026-02-01', 120, undefined],
      ['2026-03-01', undefined, 210],
    ])
    expect(rows[0].label).toBe('01/01/2026')
  })

  it('returns no rows for no lines and a shared axis for every line', () => {
    expect(buildSeriesRows([])).toEqual([])
    const [low, high] = seriesAxisDomain([line('A', 1, [['2026-01-01', 1000]]), line('B', 2, [['2026-01-01', 5000]])])
    expect(low).toBeLessThan(1000)
    expect(high).toBeGreaterThan(5000)
  })
})
