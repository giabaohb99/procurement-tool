import { describe, expect, it } from 'vitest'

import type { ReportGroupRow, ReportTrendPoint } from '../types/report-analytics'
import { buildChartPngFilename } from './report-flexible-chart-png'
import {
  buildFlexibleGroupSeries,
  buildFlexibleTimeSeries,
  canDrawDonut,
  describeSkippedGroups,
  FLEXIBLE_CHART_REST_KEY,
} from './report-flexible-chart-series'

const INT = { kind: 'int' } as const
const PCT = { kind: 'percent' } as const

function group(key: string, current: ReportGroupRow['current']): ReportGroupRow {
  return { key, label: key.toUpperCase(), current, compare: null }
}

describe('buildFlexibleTimeSeries', () => {
  const trend: ReportTrendPoint[] = [
    { key: 'a', label: '01/09', current: { n: 3 }, compare: { n: 1 } },
    { key: 'b', label: '02/09', current: {}, compare: null },
  ]

  it('mirrors the old trend chart: missing value is null (line stops), not zero', () => {
    expect(buildFlexibleTimeSeries(trend, 'n', 'previous')).toEqual([
      { label: '01/09', current: 3, previous: 1 },
      { label: '02/09', current: null, previous: null },
    ])
  })

  it('drops the comparison series entirely with compare=none', () => {
    expect(buildFlexibleTimeSeries(trend, 'n', 'none').map((p) => p.previous)).toEqual([null, null])
  })
})

describe('buildFlexibleGroupSeries', () => {
  it('sorts large → small regardless of backend order', () => {
    const s = buildFlexibleGroupSeries(
      [group('a', { n: 1 }), group('b', { n: 9 }), group('c', { n: 4 })],
      'n',
      null,
      INT,
    )
    expect(s.items.map((i) => i.key)).toEqual(['b', 'c', 'a'])
  })

  it('keeps top N and merges the remainder into "Khác" with the right sum', () => {
    const groups = [1, 2, 3, 4, 5, 6, 7].map((v) => group(`g${v}`, { n: v }))
    const s = buildFlexibleGroupSeries(groups, 'n', 5, INT)
    expect(s.items).toHaveLength(6)
    const rest = s.items[5]
    expect(rest?.isRest).toBe(true)
    expect(rest?.key).toBe(FLEXIBLE_CHART_REST_KEY)
    expect(rest?.value).toBe(1 + 2)
    expect(rest?.label).toBe('Khác (2 nhóm)')
  })

  it('does not add "Khác" when the groups fit exactly in top N', () => {
    const groups = [1, 2, 3, 4, 5].map((v) => group(`g${v}`, { n: v }))
    expect(buildFlexibleGroupSeries(groups, 'n', 5, INT).items.some((i) => i.isRest)).toBe(false)
  })

  it('skips suppressed groups (every value null) and counts them for the note', () => {
    const s = buildFlexibleGroupSeries(
      [group('a', { n: 5 }), group('b', { n: null, m: null }), group('c', { n: null, m: null })],
      'n',
      null,
      INT,
    )
    expect(s.items.map((i) => i.key)).toEqual(['a'])
    expect(s.suppressedCount).toBe(2)
    expect(describeSkippedGroups(s)).toEqual(['2 nhóm bị che không vẽ.'])
  })

  it('skips a lone null of a derived metric silently — that is "nothing to measure", not "hidden"', () => {
    const s = buildFlexibleGroupSeries([group('a', { n: 0, rate: null })], 'rate', null, PCT)
    expect(s.items).toEqual([])
    expect(s.suppressedCount).toBe(0)
  })

  it('never draws the backend __other__ row, even when it is the largest', () => {
    const s = buildFlexibleGroupSeries(
      [group('a', { n: 5 }), group('__other__', { n: 900 })],
      'n',
      null,
      INT,
    )
    expect(s.items.map((i) => i.key)).toEqual(['a'])
    expect(s.skippedServerOther).toBe(true)
  })

  it('leaves zero groups out of the picture but counts them in the note', () => {
    const s = buildFlexibleGroupSeries(
      [group('a', { n: 0 }), group('b', { n: 2 }), group('c', { n: 0 })],
      'n',
      null,
      INT,
    )
    expect(s.items.map((i) => i.key)).toEqual(['b'])
    expect(s.zeroCount).toBe(2)
    expect(describeSkippedGroups(s)).toEqual(['2 nhóm bằng 0 không vẽ.'])
  })

  it('keeps negative values (net change) — only exact zero is dropped', () => {
    const s = buildFlexibleGroupSeries([group('a', { n: -3 }), group('b', { n: 1 })], 'n', null, INT)
    expect(s.items.map((i) => i.value)).toEqual([1, -3])
  })

  it('flags a metric absent from every group (snapshot only on the Total row)', () => {
    const s = buildFlexibleGroupSeries([group('a', { other: 1 })], 'n', null, INT)
    expect(s.metricMissing).toBe(true)
    expect(buildFlexibleGroupSeries([], 'n', null, INT).metricMissing).toBe(false)
  })

  it('sums the remainder of an old-server metric without the additive flag', () => {
    const groups = [10, 20, 30].map((v) => group(`g${v}`, { n: v }))
    const s = buildFlexibleGroupSeries(groups, 'n', 1, { kind: 'money' })
    expect(s.items.at(-1)).toMatchObject({ isRest: true, value: 30 })
    expect(s.droppedRestCount).toBe(0)
  })

  it('drops the remainder of an average flagged additive=false even though kind is not percent', () => {
    //  Bình quân ngày nghỉ: cộng ba phòng ra "45 ngày" — con số không ai có.
    const groups = [10, 15, 20].map((v) => group(`g${v}`, { avg: v }))
    const s = buildFlexibleGroupSeries(groups, 'avg', 1, { kind: 'days', additive: false })
    expect(s.items.map((i) => i.key)).toEqual(['g20'])
    expect(s.droppedRestCount).toBe(2)
    expect(describeSkippedGroups(s)).toContain(
      'Còn 2 nhóm nhỏ hơn không vẽ (chỉ số này không cộng gộp được).',
    )
  })

  it('still drops the remainder of a percent metric even when the server claims additive=true', () => {
    const groups = [10, 20, 30].map((v) => group(`g${v}`, { r: v }))
    const s = buildFlexibleGroupSeries(groups, 'r', 1, { kind: 'percent', additive: true })
    expect(s.droppedRestCount).toBe(2)
    expect(s.items.some((i) => i.isRest)).toBe(false)
  })

  it('drops (does not sum) the remainder of a percent metric — summed rates are meaningless', () => {
    const groups = [10, 20, 30].map((v) => group(`g${v}`, { r: v }))
    const s = buildFlexibleGroupSeries(groups, 'r', 2, PCT)
    expect(s.items.map((i) => i.key)).toEqual(['g30', 'g20'])
    expect(s.droppedRestCount).toBe(1)
  })

  it('ignores a non-positive top instead of drawing nothing', () => {
    const groups = [1, 2].map((v) => group(`g${v}`, { n: v }))
    expect(buildFlexibleGroupSeries(groups, 'n', 0, INT).items).toHaveLength(2)
  })
})

describe('canDrawDonut', () => {
  const series = (values: number[]) =>
    buildFlexibleGroupSeries(
      values.map((v, i) => group(`g${i}`, { n: v })),
      'n',
      null,
      INT,
    )

  it('allows up to 6 groups with a value and forbids the 7th', () => {
    expect(canDrawDonut(series([1, 2, 3, 4, 5, 6]), INT)).toBe(true)
    expect(canDrawDonut(series([1, 2, 3, 4, 5, 6, 7]), INT)).toBe(false)
  })

  it('counts only drawable groups — suppressed ones do not use up a slice', () => {
    const groups = [
      ...[1, 2, 3, 4, 5, 6].map((v) => group(`g${v}`, { n: v })),
      group('hidden', { n: null }),
      group('__other__', { n: 99 }),
    ]
    expect(canDrawDonut(buildFlexibleGroupSeries(groups, 'n', null, INT), INT)).toBe(true)
  })

  it('forbids negative values, an all-zero total, an empty list and percent metrics', () => {
    expect(canDrawDonut(series([5, -1]), INT)).toBe(false)
    expect(canDrawDonut(series([0, 0]), INT)).toBe(false)
    //  Số 0 không chiếm lát: 6 nhóm có số + 3 nhóm 0 vẫn vẽ vành khuyên được.
    expect(canDrawDonut(series([1, 2, 3, 4, 5, 6, 0, 0, 0]), INT)).toBe(true)
    expect(canDrawDonut(series([]), INT)).toBe(false)
    expect(canDrawDonut(series([10, 20]), PCT)).toBe(false)
    expect(canDrawDonut(series([10, 20]), { kind: 'days', additive: false })).toBe(false)
    expect(canDrawDonut(series([10, 20]), { kind: 'int', additive: true })).toBe(true)
  })
})

describe('buildChartPngFilename', () => {
  it('uses the report period', () => {
    expect(buildChartPngFilename('hr-headcount', { date_from: '2026-10-01', date_to: '2026-10-31' })).toBe(
      'bieu-do-hr-headcount-2026-10-01-2026-10-31.png',
    )
  })

  it('falls back to the given day while the period is still loading', () => {
    expect(buildChartPngFilename('x', undefined, new Date(2026, 9, 27))).toBe(
      'bieu-do-x-2026-10-27-2026-10-27.png',
    )
  })
})
