import { describe, expect, it } from 'vitest'

import { describeSuggestedDays } from './leave-suggested-days-note'

describe('describeSuggestedDays', () => {
  // Regression: loại nghỉ exclude_holiday=false từng nhận câu «đã trừ ngày nghỉ… và ngày lễ»
  // dù số ngày đếm cả hai — câu nói ngược với con số.
  it('a calendar-day leave type says weekly days off and holidays ARE counted, never «đã trừ»', () => {
    const note = describeSuggestedDays(30, false, 'Hành chính T2–T7')
    expect(note).toContain('tính cả ngày nghỉ tuần và ngày lễ')
    expect(note).not.toContain('đã trừ')
    expect(note).not.toContain('Hành chính')
  })

  it('a normal leave type says the schedule days off and holidays were deducted, naming the schedule', () => {
    expect(describeSuggestedDays(3, true, 'Hành chính T2–T7')).toBe(
      'Khoảng ngày đã chọn có 3 ngày công (đã trừ ngày nghỉ theo lịch làm việc «Hành chính T2–T7» và ngày lễ).',
    )
  })

  it('unknown leave type (nothing chosen yet) behaves like a normal type; missing or empty schedule name is omitted', () => {
    for (const name of [undefined, '']) {
      const note = describeSuggestedDays(0, undefined, name)
      expect(note).toBe('Khoảng ngày đã chọn có 0 ngày công (đã trừ ngày nghỉ theo lịch làm việc và ngày lễ).')
    }
  })

  it('does not lose fractional and zero day counts', () => {
    expect(describeSuggestedDays(0.5, false)).toContain('có 0.5 ngày')
  })
})
