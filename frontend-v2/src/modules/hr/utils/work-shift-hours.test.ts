import { describe, expect, it } from 'vitest'

import { WORK_DAY_KIND_CODE } from '../types/work-schedule'
import {
  formatHourLabel,
  formatHourRange,
  formatHourRanges,
  initialRangesForCell,
  isValidRange,
  mergeRanges,
  OFFICE_HOURS_PRESET,
  templateDayToRanges,
} from './work-shift-hours'

describe('formatHourLabel / formatHourRange', () => {
  it('always shows full 24h HH:MM (owner rule 05/10/2026), 24 stays 24:00, never AM/PM', () => {
    expect(formatHourLabel(0)).toBe('00:00')
    expect(formatHourLabel(13)).toBe('13:00')
    expect(formatHourLabel(24)).toBe('24:00')
    expect(formatHourRange([8, 10])).toBe('08:00–10:00')
    expect(formatHourRanges([[8, 10], [14, 16]])).toBe('08:00–10:00 · 14:00–16:00')
    expect(formatHourRanges([])).toBe('')
  })
})

describe('isValidRange / mergeRanges', () => {
  it('rejects broken ranges: negative, past 24, empty, inverted, fractional', () => {
    expect(isValidRange([0, 24])).toBe(true)
    expect([[-1, 3], [5, 5], [10, 8], [20, 25], [1.5, 3]].some(isValidRange)).toBe(false)
  })

  it('sorts, merges overlapping AND touching ranges, drops broken ones', () => {
    expect(mergeRanges([[14, 16], [8, 10], [9, 12], [16, 18], [5, 5]])).toEqual([
      [8, 12],
      [14, 18],
    ])
  })

  it('null / undefined / empty → no range (a full day off)', () => {
    expect(mergeRanges(null)).toEqual([])
    expect(mergeRanges(undefined)).toEqual([])
    expect(mergeRanges([])).toEqual([])
  })
})

describe('templateDayToRanges', () => {
  const office = {
    day_kind: WORK_DAY_KIND_CODE.FULL,
    start_time: '08:00',
    end_time: '17:00',
    lunch_start: '12:00',
    lunch_end: '13:00',
  }

  it('splits around lunch: 08:00–17:00 lunch 12–13 → 08–12 + 13–17, not rounded', () => {
    expect(templateDayToRanges(office)).toEqual({ ranges: [[8, 12], [13, 17]], rounded: false })
  })

  it('odd minutes round OUTWARD (start down, end up) and flag it so the dialog can explain', () => {
    expect(templateDayToRanges({ ...office, start_time: '08:30', end_time: '17:30' })).toEqual({
      ranges: [[8, 12], [13, 18]],
      rounded: true,
    })
  })

  it('lunch edges round INWARD so the lunch gap is kept: 12:30–13:30 → 08–12 + 14–18', () => {
    expect(templateDayToRanges({ ...office, end_time: '17:30', lunch_start: '12:30', lunch_end: '13:30' })).toEqual({
      ranges: [[8, 12], [14, 18]],
      rounded: true,
    })
    //  Nghỉ trưa ngắn nằm gọn trong một tiếng vẫn để lại khoảng nghỉ, không dính hai ca.
    expect(templateDayToRanges({ ...office, lunch_start: '12:15', lunch_end: '12:45' }).ranges).toEqual([[8, 12], [13, 17]])
  })

  it('a morning shrunk to nothing by inward rounding is dropped, not sent as an empty range', () => {
    expect(templateDayToRanges({ ...office, start_time: '08:10', lunch_start: '08:50', lunch_end: '09:00' }).ranges).toEqual([[9, 17]])
  })

  it('a day off, a missing day or broken / inverted times give no range', () => {
    expect(templateDayToRanges({ ...office, day_kind: WORK_DAY_KIND_CODE.OFF }).ranges).toEqual([])
    expect(templateDayToRanges(null).ranges).toEqual([])
    expect(templateDayToRanges({ ...office, start_time: null }).ranges).toEqual([])
    expect(templateDayToRanges({ ...office, start_time: '17:00', end_time: '08:00' }).ranges).toEqual([])
    expect(templateDayToRanges({ ...office, start_time: 'abc' }).ranges).toEqual([])
  })

  it('ignores a lunch break that is inverted or outside the working hours', () => {
    expect(templateDayToRanges({ ...office, lunch_start: '13:00', lunch_end: '12:00' }).ranges).toEqual([[8, 17]])
    expect(templateDayToRanges({ ...office, lunch_start: '18:00', lunch_end: '19:00' }).ranges).toEqual([[8, 17]])
  })

  it('accepts a template ending at 24:00', () => {
    const night = { ...office, start_time: '18:00', end_time: '24:00', lunch_start: null, lunch_end: null }
    expect(templateDayToRanges(night).ranges).toEqual([[18, 24]])
  })

  it('the office preset is 08–12 + 13–17', () => {
    expect(OFFICE_HOURS_PRESET).toEqual([[8, 12], [13, 17]])
  })
})

describe('initialRangesForCell', () => {
  const cell = { work_kind: WORK_DAY_KIND_CODE.FULL, start_time: '08:00', end_time: '17:00' }
  const template = { day_kind: WORK_DAY_KIND_CODE.FULL, start_time: '08:00', end_time: '17:00', lunch_start: '12:00', lunch_end: '13:00' }

  it('an existing shift wins over the template', () => {
    const shiftCell = { ...cell, is_shift: true, shift: { segments: [], ranges: [[19, 22]], hours: 3, note: '', is_day_off: false } }
    expect(initialRangesForCell(shiftCell, template).ranges).toEqual([[19, 22]])
  })

  it('adjacent shift ranges stay two rows (08–10 + 10–12 are NOT merged when opening)', () => {
    const shiftCell = { ...cell, is_shift: true, shift: { segments: [], ranges: [[10, 12], [8, 10]], hours: 4, note: '', is_day_off: false } }
    expect(initialRangesForCell(shiftCell, template).ranges).toEqual([[8, 10], [10, 12]])
  })

  it('a day off set by shift opens with no range, not with the template', () => {
    const offCell = { ...cell, is_shift: true, shift: { segments: [], ranges: [], hours: 0, note: '', is_day_off: true } }
    expect(initialRangesForCell(offCell, template).ranges).toEqual([])
  })

  it('no shift: prefills the weekly template including lunch', () => {
    expect(initialRangesForCell({ ...cell, is_shift: false, shift: null }, template).ranges).toEqual([[8, 12], [13, 17]])
  })

  it('template not loaded / failed: NO guess from the cell hours (would silently prefill 08–17 without lunch)', () => {
    expect(initialRangesForCell({ ...cell, is_shift: false, shift: null }, undefined).ranges).toEqual([])
  })

  it('no cell at all (backend sent no day): no range', () => {
    expect(initialRangesForCell(undefined, undefined).ranges).toEqual([])
  })
})
