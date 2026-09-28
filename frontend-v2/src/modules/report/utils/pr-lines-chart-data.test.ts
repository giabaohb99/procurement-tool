import { describe, expect, it } from 'vitest'

import { PR_LINE_STATUS } from '@/shared/constants/statuses'

import { fillPrLinesMonths, labelAssignee, orderPrLineStatuses } from './pr-lines-chart-data'

const bucket = (month: string, lines: number, idle: number) => ({
  month,
  lines,
  idle_lines: idle,
  amount: 0,
  idle_amount: 0,
})

describe('fillPrLinesMonths', () => {
  it('always returns 12 months and splits handled vs idle', () => {
    const out = fillPrLinesMonths(2026, [bucket('2026-03', 10, 4)])
    expect(out).toHaveLength(12)
    expect(out[2]).toEqual({ label: 'T3', handled: 6, idle: 4 })
    expect(out[0]).toEqual({ label: 'T1', handled: 0, idle: 0 })
  })

  it('drops points of another year or malformed months', () => {
    const out = fillPrLinesMonths(2026, [
      bucket('2025-03', 9, 9),
      bucket('2026-00', 9, 9),
      bucket('2026-13', 9, 9),
      bucket('garbage', 9, 9),
    ])
    expect(out.every((m) => m.handled === 0 && m.idle === 0)).toBe(true)
  })

  //  Dữ liệu lệch (idle > lines) không được vẽ thành một khúc cột ÂM.
  it('never produces a negative handled segment', () => {
    expect(fillPrLinesMonths(2026, [bucket('2026-01', 2, 5)])[0].handled).toBe(0)
  })
})

describe('orderPrLineStatuses', () => {
  it('follows the line lifecycle with cancelled last, not magnitude', () => {
    const out = orderPrLineStatuses([
      { code: 'cancelled', lines: 50, amount: 0 },
      { code: 'completed', lines: 1, amount: 0 },
      { code: 'no_po', lines: 3, amount: 0 },
    ])
    const label = (code: string) => PR_LINE_STATUS.find((s) => s.value === code)?.label
    expect(out.map((d) => d.label)).toEqual([label('no_po'), label('completed'), label('cancelled')])
  })

  it('hides zero-count statuses and keeps unknown codes visible at the end', () => {
    const out = orderPrLineStatuses([
      { code: 'ordered', lines: 0, amount: 0 },
      { code: 'la_ma_moi', lines: 2, amount: 0 },
      { code: 'no_po', lines: 1, amount: 0 },
    ])
    expect(out.map((d) => d.label)).toEqual([
      PR_LINE_STATUS.find((s) => s.value === 'no_po')?.label,
      'la_ma_moi',
    ])
  })

  it('returns an empty list for no data', () => {
    expect(orderPrLineStatuses([])).toEqual([])
  })
})

describe('labelAssignee', () => {
  it('prefers name, falls back to code, then to an explicit unassigned label', () => {
    expect(labelAssignee({ code: 'NV1', name: 'An' })).toBe('An')
    expect(labelAssignee({ code: 'NV1', name: '' })).toBe('NV1')
    expect(labelAssignee({ code: '', name: '' })).toBe('(Chưa gán NSTM)')
  })
})
