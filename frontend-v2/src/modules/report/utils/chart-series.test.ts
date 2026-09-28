import { describe, expect, it } from 'vitest'

import { PO_PROGRESS_STATUS, type StatusOption } from '@/shared/constants/statuses'

import { fillYearMonths, orderByLifecycle, topBars } from './chart-series'

describe('fillYearMonths', () => {
  it('returns 12 zero-filled months and sums every requested field', () => {
    const out = fillYearMonths(2026, [{ month: '2026-02', a: 1, b: 2 }], ['a', 'b'] as const)
    expect(out).toHaveLength(12)
    expect(out[1]).toEqual({ label: 'T2', a: 1, b: 2 })
    expect(out[11]).toEqual({ label: 'T12', a: 0, b: 0 })
  })

  it('adds duplicate months together and treats a missing field as 0', () => {
    const out = fillYearMonths(
      2026,
      [
        { month: '2026-05', a: 1 },
        { month: '2026-05', a: 2, b: 7 },
      ],
      ['a', 'b'] as const,
    )
    expect(out[4]).toEqual({ label: 'T5', a: 3, b: 7 })
  })

  it('ignores other years and malformed months', () => {
    const out = fillYearMonths(
      2026,
      [
        { month: '2025-05', a: 9 },
        { month: '2026-00', a: 9 },
        { month: '2026-13', a: 9 },
        { month: '', a: 9 },
        { month: '2026', a: 9 },
      ],
      ['a'] as const,
    )
    expect(out.reduce((s, p) => s + p.a, 0)).toBe(0)
  })
})

describe('orderByLifecycle', () => {
  const label = (code: string) => PO_PROGRESS_STATUS.find((s) => s.value === code)?.label

  it('orders by lifecycle with exception codes (paused, cancelled) last', () => {
    const out = orderByLifecycle(PO_PROGRESS_STATUS, [
      { code: 'cancelled', value: 99 },
      { code: 'completed', value: 1 },
      { code: 'not_ordered', value: 5 },
    ])
    expect(out.map((d) => d.label)).toEqual([label('not_ordered'), label('completed'), label('cancelled')])
  })

  it('merges repeated codes, hides zeros and keeps unknown codes at the end', () => {
    const out = orderByLifecycle(PO_PROGRESS_STATUS, [
      { code: 'ordered', value: 1 },
      { code: 'ordered', value: 2 },
      { code: 'received', value: 0 },
      { code: 'ma_la', value: 4 },
    ])
    expect(out).toEqual([
      { label: label('ordered'), value: 3 },
      { label: 'ma_la', value: 4 },
    ])
  })

  it('handles an empty option set without dropping data', () => {
    const none: StatusOption[] = []
    expect(orderByLifecycle(none, [{ code: 'x', value: 1 }])).toEqual([{ label: 'x', value: 1 }])
  })
})

describe('topBars', () => {
  it('keeps backend order, drops zero rows, then cuts to n', () => {
    const rows = [
      { k: 'a', v: 5 },
      { k: 'b', v: 0 },
      { k: 'c', v: 3 },
      { k: 'd', v: 1 },
    ]
    expect(topBars(rows, 2, (r) => r.k, (r) => r.v)).toEqual([
      { label: 'a', value: 5 },
      { label: 'c', value: 3 },
    ])
    expect(topBars([], 5, String, Number)).toEqual([])
  })
})
