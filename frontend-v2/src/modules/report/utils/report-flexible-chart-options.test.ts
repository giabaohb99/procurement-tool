import { describe, expect, it } from 'vitest'

import {
  buildFlexibleChartUrlPatch,
  parseChartTop,
  pickDefaultChartBy,
  resolveChartMetric,
  resolveFlexibleChartOptions,
  type FlexibleChartContext,
} from './report-flexible-chart-options'

const TIME_PAGE: FlexibleChartContext = {
  hasTime: true,
  hasGroup: true,
  preferGroup: false,
  donutAllowed: true,
}
const NO_RAW = { by: null, type: null, top: null }

describe('resolveFlexibleChartOptions — defaults', () => {
  it('keeps the old look by default: time axis, line, top 10', () => {
    expect(resolveFlexibleChartOptions(NO_RAW, TIME_PAGE)).toEqual({
      by: 'time',
      type: 'line',
      top: '10',
    })
  })

  it('defaults to a horizontal bar by group on hideTrend / snapshot pages', () => {
    const ctx = { ...TIME_PAGE, hasTime: false, preferGroup: true }
    expect(resolveFlexibleChartOptions(NO_RAW, ctx)).toEqual({ by: 'group', type: 'hbar', top: '10' })
  })

  it('prefers group even when a trend exists if the metric is a snapshot', () => {
    expect(pickDefaultChartBy({ ...TIME_PAGE, preferGroup: true })).toBe('group')
  })

  it('falls back to time when group is preferred but there is no group dimension', () => {
    expect(pickDefaultChartBy({ ...TIME_PAGE, hasGroup: false, preferGroup: true })).toBe('time')
  })

  it('falls back to group when nothing is preferred but there is no trend', () => {
    expect(pickDefaultChartBy({ ...TIME_PAGE, hasTime: false })).toBe('group')
  })

  it('still answers something (time) when neither axis is available — the card shows its empty state', () => {
    expect(pickDefaultChartBy({ ...TIME_PAGE, hasTime: false, hasGroup: false })).toBe('time')
  })
})

describe('resolveFlexibleChartOptions — raw URL values', () => {
  it('honours a valid shared link', () => {
    expect(
      resolveFlexibleChartOptions({ by: 'group', type: 'donut', top: '5' }, TIME_PAGE),
    ).toEqual({ by: 'group', type: 'donut', top: '5' })
  })

  it('ignores chart_by=time on a page with no time axis instead of drawing an empty chart', () => {
    const ctx = { ...TIME_PAGE, hasTime: false, preferGroup: true }
    expect(resolveFlexibleChartOptions({ by: 'time', type: 'line', top: null }, ctx).by).toBe('group')
  })

  it('drops a type that does not belong to the chosen axis (line drawn by group)', () => {
    expect(resolveFlexibleChartOptions({ by: 'group', type: 'line', top: null }, TIME_PAGE).type).toBe(
      'hbar',
    )
    expect(resolveFlexibleChartOptions({ by: 'time', type: 'donut', top: null }, TIME_PAGE).type).toBe(
      'line',
    )
  })

  it('falls back from donut to hbar when the data no longer allows a donut', () => {
    const ctx = { ...TIME_PAGE, donutAllowed: false }
    expect(resolveFlexibleChartOptions({ by: 'group', type: 'donut', top: null }, ctx).type).toBe('hbar')
  })

  it.each(['', 'GROUP', '0', '-5', '1e9', 'all ', '<script>'])(
    'treats hand-typed garbage %j as "not chosen"',
    (garbage) => {
      expect(
        resolveFlexibleChartOptions({ by: garbage, type: garbage, top: garbage }, TIME_PAGE),
      ).toEqual({ by: 'time', type: 'line', top: '10' })
    },
  )
})

describe('buildFlexibleChartUrlPatch', () => {
  const current = { by: 'time', type: 'line', top: '10' } as const

  it('writes all three params in ONE patch and resets the type when the axis changes', () => {
    //  Bẫy hai `setSearchParams` trong một lần bấm: đổi trục mà kiểu ghi ở lượt riêng thì mất.
    expect(buildFlexibleChartUrlPatch(current, { by: 'group' }, TIME_PAGE)).toEqual({
      chart_by: 'group',
      chart_type: null,
      chart_top: null,
    })
  })

  it('removes values equal to the default so the link stays clean', () => {
    expect(
      buildFlexibleChartUrlPatch({ by: 'group', type: 'bar', top: '5' }, { by: 'time' }, TIME_PAGE),
    ).toEqual({ chart_by: null, chart_type: null, chart_top: '5' })
  })

  it('keeps the explicit type when only the type changes', () => {
    expect(buildFlexibleChartUrlPatch(current, { type: 'bar' }, TIME_PAGE)).toEqual({
      chart_by: null,
      chart_type: 'bar',
      chart_top: null,
    })
  })

  it('does not write chart_by=group on a page where group is already the default', () => {
    const ctx = { ...TIME_PAGE, hasTime: false, preferGroup: true }
    expect(
      buildFlexibleChartUrlPatch({ by: 'group', type: 'hbar', top: '10' }, { top: 'all' }, ctx),
    ).toEqual({ chart_by: null, chart_type: null, chart_top: 'all' })
  })
})

describe('parseChartTop', () => {
  it('maps all to no limit and numbers to numbers', () => {
    expect(parseChartTop('all')).toBeNull()
    expect(parseChartTop('5')).toBe(5)
    expect(parseChartTop('20')).toBe(20)
  })
})

describe('resolveChartMetric', () => {
  const metrics = [
    { key: 'a', helper: false },
    { key: 'denominator', helper: true },
  ]

  it('takes a known metric from the URL', () => {
    expect(resolveChartMetric('a', 'x', metrics)).toBe('a')
  })

  it.each([null, '', 'unknown', 'denominator'])('falls back to the page default for %j', (raw) => {
    expect(resolveChartMetric(raw, 'x', metrics)).toBe('x')
  })

  it('trusts the URL until meta arrives (no flash to the default)', () => {
    expect(resolveChartMetric('a', 'x', undefined)).toBe('a')
    expect(resolveChartMetric('a', 'x', [])).toBe('a')
  })
})
