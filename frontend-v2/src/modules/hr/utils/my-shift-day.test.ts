import { describe, expect, it } from 'vitest'

import type { MyShiftDay } from '../types/work-shift'
import { describeMyShiftDay } from './my-shift-day'

function day(over: Partial<MyShiftDay> = {}): MyShiftDay {
  return {
    date: '2026-11-16',
    weekday: 0,
    is_shift: false,
    work_kind: 2,
    work_kind_label: 'Cả ngày',
    start_time: '08:00',
    end_time: '17:00',
    segments: ['08:00–12:00', '13:00–17:00'],
    ranges: [],
    hours: 8,
    note: '',
    is_day_off: false,
    is_holiday: false,
    holiday_name: '',
    schedule_name: 'Hành chính',
    ...over,
  }
}

describe('describeMyShiftDay', () => {
  it('a template day shows its split hours and the schedule name', () => {
    expect(describeMyShiftDay(day())).toEqual({
      tone: 'work',
      text: '08:00–12:00 · 13:00–17:00',
      parts: ['08:00–12:00', '13:00–17:00'],
      hoursText: '8 giờ',
      source: 'Hành chính',
    })
  })

  it('a shift day is flagged as an exception with its own source label', () => {
    const view = describeMyShiftDay(day({ is_shift: true, segments: ['19:00–23:00'], hours: 4, schedule_name: 'Xếp ca theo ngày' }))
    expect(view).toMatchObject({ tone: 'shift', text: '19:00–23:00', hoursText: '4 giờ', source: 'Ca xếp riêng' })
  })

  it('a day off by shift is not confused with a weekly day off', () => {
    expect(describeMyShiftDay(day({ is_shift: true, segments: [], hours: 0, is_day_off: true })).tone).toBe('shift-off')
    expect(describeMyShiftDay(day({ segments: [], hours: 0, is_day_off: true, weekday: 6 }))).toMatchObject({ tone: 'off', text: 'Nghỉ', hoursText: '' })
  })

  it('a holiday wins over the template; a shift on a holiday is still shown', () => {
    expect(describeMyShiftDay(day({ is_holiday: true, holiday_name: 'Quốc khánh' }))).toMatchObject({ tone: 'holiday', text: 'Lễ: Quốc khánh', hoursText: '' })
    expect(describeMyShiftDay(day({ is_holiday: true, holiday_name: '', is_shift: true, segments: ['08:00–10:00'], hours: 2 }))).toMatchObject({
      text: 'Ngày lễ · 08:00–10:00',
      hoursText: '2 giờ',
    })
  })

  it('segments present but flagged off (inconsistent payload) reads as off, never as work with 0 hours', () => {
    expect(describeMyShiftDay(day({ is_day_off: true })).tone).toBe('off')
  })
})
