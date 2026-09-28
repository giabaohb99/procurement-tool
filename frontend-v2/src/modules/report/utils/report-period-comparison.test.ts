import { describe, expect, it } from 'vitest'

import {
  describeMetricChange,
  formatMetricChange,
  percentChange,
  percentPointChange,
  ratePercent,
  resolveMetricChange,
  compareCaption,
} from './report-period-comparison'

describe('percentChange', () => {
  it('returns relative change against the previous period', () => {
    expect(percentChange(150, 100)).toBe(50)
    expect(percentChange(50, 100)).toBe(-50)
    expect(percentChange(0, 100)).toBe(-100)
  })

  it('returns null when there is no previous period to compare against', () => {
    expect(percentChange(100, 0)).toBeNull()
    expect(percentChange(0, 0)).toBeNull()
    expect(percentChange(Number.NaN, 10)).toBeNull()
    expect(percentChange(10, Number.POSITIVE_INFINITY)).toBeNull()
  })

  //  Chỉ số DẪN XUẤT có thể là `null` ở một trong hai vế (mẫu số 0) — trước
  //  đây tầng gọi phải tự `?? 0` để tránh lỗi kiểu, mà đó chính là lỗi (H2):
  //  0% thật khác hẳn "chưa đo được gì".
  it('returns null when either side is null, without needing the caller to coerce to 0', () => {
    expect(percentChange(null, 100)).toBeNull()
    expect(percentChange(50, null)).toBeNull()
    expect(percentChange(null, null)).toBeNull()
  })

  it('keeps the sign right when the previous period is negative (refunds)', () => {
    expect(percentChange(-50, -100)).toBe(50)
  })
})

describe('ratePercent', () => {
  it('returns null for an empty sample instead of 0% or NaN', () => {
    expect(ratePercent(0, 0)).toBeNull()
    expect(ratePercent(3, -1)).toBeNull()
  })

  it('computes the share', () => {
    expect(ratePercent(3, 4)).toBe(75)
  })
})

describe('percentPointChange', () => {
  it('subtracts rather than computing a relative %', () => {
    //  80% → 40% là GIẢM 40 ĐIỂM, không phải "−50%" (Excel/thẻ KPI cũ nhầm chỗ này).
    expect(percentPointChange(40, 80)).toBe(-40)
    expect(percentPointChange(95.6, 100)).toBeCloseTo(-4.4)
  })

  it('returns null when either side is null or non-finite', () => {
    expect(percentPointChange(null, 80)).toBeNull()
    expect(percentPointChange(40, null)).toBeNull()
    expect(percentPointChange(Number.NaN, 80)).toBeNull()
  })
})

describe('resolveMetricChange — unit follows metric.kind', () => {
  it('uses percentage POINTS for kind: percent', () => {
    expect(resolveMetricChange(40, 80, 'percent')).toEqual({ value: -40, unit: 'điểm' })
  })

  it('uses relative % for every other kind', () => {
    expect(resolveMetricChange(150, 100, 'money')).toEqual({ value: 50, unit: '%' })
    expect(resolveMetricChange(150, 100, 'int')).toEqual({ value: 50, unit: '%' })
    expect(resolveMetricChange(150, 100, 'days')).toEqual({ value: 50, unit: '%' })
    expect(resolveMetricChange(150, 100, 'hours')).toEqual({ value: 50, unit: '%' })
  })

  it('propagates null from either helper untouched', () => {
    expect(resolveMetricChange(null, 80, 'percent')).toEqual({ value: null, unit: 'điểm' })
    expect(resolveMetricChange(null, 100, 'money')).toEqual({ value: null, unit: '%' })
  })
})

describe('formatMetricChange', () => {
  it('formats a relative % change with a leading sign', () => {
    expect(formatMetricChange(12.34, '%')).toBe('+12,3%')
    expect(formatMetricChange(-4, '%')).toBe('−4%')
    expect(formatMetricChange(0, '%')).toBe('0%')
  })

  it('formats a percentage-point change with "điểm", not "%"', () => {
    expect(formatMetricChange(3.5, 'điểm')).toBe('+3,5 điểm')
    expect(formatMetricChange(-4.4, 'điểm')).toBe('−4,4 điểm')
  })
})

describe('describeMetricChange — the single classifier behind the change pill and the group-row tooltip', () => {
  it('tones GOOD when the direction matches metric.good (spend down is good)', () => {
    const d = describeMetricChange(80, 100, 'money', 'down')
    expect(d).toEqual({ kind: 'value', text: '−20%', tone: 'good', direction: 'down' })
  })

  it('tones BAD when the direction is the opposite of metric.good', () => {
    const d = describeMetricChange(120, 100, 'money', 'down')
    expect(d).toEqual({ kind: 'value', text: '+20%', tone: 'bad', direction: 'up' })
  })

  it('tones NEUTRAL when metric.good is null — a number without a "good" meaning', () => {
    const d = describeMetricChange(120, 100, 'money', null)
    expect(d.tone).toBe('neutral')
    expect(d.kind).toBe('value')
  })

  it('rounds a near-zero relative change to "flat" and reports "Không đổi"', () => {
    //  0,04% làm tròn 1 chữ số thập phân về đúng 0 — phải ra "Không đổi", không
    //  phải "+0%" (đọc như có thay đổi thật, dù cực nhỏ).
    const d = describeMetricChange(100.04, 100, 'money', 'down')
    expect(d).toEqual({ kind: 'flat', text: 'Không đổi', tone: 'neutral', direction: 'flat' })
  })

  it('treats an exact-zero change the same way regardless of metric.good', () => {
    expect(describeMetricChange(100, 100, 'int', 'up').kind).toBe('flat')
    expect(describeMetricChange(0, 0, 'percent', 'up').kind).toBe('flat')
  })

  it('reports "Mới" (not "+∞%") when the previous period was 0 and this period is positive', () => {
    const d = describeMetricChange(50, 0, 'money', 'up')
    expect(d).toEqual({ kind: 'new', text: 'Mới', tone: 'neutral', direction: null })
  })

  it('does NOT treat kind: "percent" the same way — a 0 → 12 move is a real "+12 điểm"', () => {
    //  `percentPointChange` là phép TRỪ, không phải tỷ lệ tương đối — kỳ trước
    //  0% vẫn ra một con số có nghĩa, không phải trường hợp "Mới".
    const d = describeMetricChange(12, 0, 'percent', 'up')
    expect(d).toEqual({ kind: 'value', text: '+12 điểm', tone: 'good', direction: 'up' })
  })

  it('still shows a real "−100%" (not "Mới") when this period dropped to 0 from a positive previous period — only meant for the Tổng row', () => {
    //  `good: 'up'` (vd doanh thu — tăng là tốt): rơi về 0 là XẤU, tone phải là
    //  'bad', không phải trung tính hay 'good'.
    const d = describeMetricChange(0, 80, 'money', 'up')
    expect(d).toEqual({ kind: 'value', text: '−100%', tone: 'bad', direction: 'down' })
  })

  it('is "unavailable" (no pill, no tooltip line) when either side is null — missing data, not a real zero', () => {
    expect(describeMetricChange(null, 80, 'money', 'up').kind).toBe('unavailable')
    expect(describeMetricChange(80, null, 'money', 'up').kind).toBe('unavailable')
    expect(describeMetricChange(null, null, 'money', 'up').kind).toBe('unavailable')
  })

  it('is "flat" (Không đổi), not "Mới", when BOTH sides are 0 — nothing actually appeared', () => {
    expect(describeMetricChange(0, 0, 'money', 'up')).toEqual({
      kind: 'flat',
      text: 'Không đổi',
      tone: 'neutral',
      direction: 'flat',
    })
  })
})

describe('compareCaption', () => {
  it('stays short enough for five KPI cards in one row', () => {
    expect(compareCaption('year')).toBe('so với năm trước')
    expect(compareCaption('previous')).toBe('so với kỳ trước')
  })
})
