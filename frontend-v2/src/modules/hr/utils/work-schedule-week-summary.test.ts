import { describe, expect, it } from 'vitest'

import { WORK_DAY_KIND_CODE, type WorkScheduleDay } from '../types/work-schedule'
import { describeDay, describeDayFull, describeLunch, summarizeWeek } from './work-schedule-week-summary'

const { OFF, FULL, MORNING, AFTERNOON } = WORK_DAY_KIND_CODE

function day(
  weekday: number,
  kind: number,
  start: string | null = null,
  end: string | null = null,
  lunch: [string, string] | null = null,
): WorkScheduleDay {
  return {
    weekday,
    day_kind: kind,
    start_time: start,
    end_time: end,
    lunch_start: lunch?.[0] ?? null,
    lunch_end: lunch?.[1] ?? null,
  }
}

const fullDay = (weekday: number) => day(weekday, FULL, '08:00', '17:00', ['12:00', '13:00'])

describe('describeDay / describeLunch / describeDayFull', () => {
  it('half days show their hours; full day shows range; OFF shows Nghỉ', () => {
    expect(describeDay(day(5, MORNING, '08:00', '12:00'))).toBe('Sáng 08:00–12:00')
    expect(describeDay(day(5, AFTERNOON, '13:00', '17:00'))).toBe('Chiều 13:00–17:00')
    expect(describeDay(fullDay(0))).toBe('08:00–17:00')
    expect(describeDay(day(6, OFF))).toBe('Nghỉ')
  })

  it('half days without hours (broken data) fall back to the bare label, not «undefined»', () => {
    expect(describeDay(day(5, MORNING))).toBe('Sáng')
    expect(describeDay(day(5, AFTERNOON))).toBe('Chiều')
    expect(describeDay(day(0, FULL))).toBe('Cả ngày')
  })

  it('lunch only appears for a FULL day that has both lunch times', () => {
    expect(describeLunch(fullDay(0))).toBe('nghỉ trưa 12:00–13:00')
    expect(describeLunch(day(0, FULL, '08:00', '17:00'))).toBe('')
    expect(describeLunch({ ...fullDay(0), lunch_end: null })).toBe('')
    expect(describeLunch(day(5, MORNING, '08:00', '12:00', ['10:00', '10:30']))).toBe('')
    expect(describeDayFull(fullDay(0))).toBe('08:00–17:00 (nghỉ trưa 12:00–13:00)')
    expect(describeDayFull(day(5, MORNING, '08:00', '12:00'))).toBe('Sáng 08:00–12:00')
  })
})

describe('summarizeWeek', () => {
  it('groups consecutive identical days, then half day with hours, then OFF', () => {
    const week = [0, 1, 2, 3, 4].map(fullDay)
    week.push(day(5, MORNING, '08:00', '12:00'), day(6, OFF))
    expect(summarizeWeek(week)).toBe('T2–T6 08:00–17:00 · T7 sáng 08:00–12:00 · CN nghỉ')
  })

  // Regression: T6 không khai giờ trưa từng ra «T2–T5 08:00–17:00 · T6 08:00–17:00»,
  // trông như bị lặp. Giờ trưa khác chuẩn / vắng phải được nói ra.
  it('never prints two adjacent groups with the same label: a lunch difference is spelled out', () => {
    const week = [0, 1, 2, 3].map(fullDay)
    week.push(day(4, FULL, '08:00', '17:00'))
    expect(summarizeWeek(week)).toBe('T2–T5 08:00–17:00 · T6 08:00–17:00 (không nghỉ trưa)')
    const shifted = [fullDay(0), day(1, FULL, '08:00', '17:00', ['11:30', '12:30'])]
    expect(summarizeWeek(shifted)).toBe('T2 08:00–17:00 · T3 08:00–17:00 (nghỉ trưa 11:30–12:30)')
  })

  it('half days ignore stray lunch values when grouping', () => {
    const week = [day(0, MORNING, '08:00', '12:00'), day(1, MORNING, '08:00', '12:00', ['10:00', '10:30'])]
    expect(summarizeWeek(week)).toBe('T2–T3 sáng 08:00–12:00')
  })

  it('does not group non-adjacent days (T2, T4 work; T3 off)', () => {
    const week = [fullDay(0), day(1, OFF), fullDay(2)]
    expect(summarizeWeek(week)).toBe('T2 08:00–17:00 · T3 nghỉ · T4 08:00–17:00')
  })

  it('different hours split the group', () => {
    const week = [fullDay(0), fullDay(1), day(2, FULL, '07:30', '16:30', ['12:00', '13:00'])]
    expect(summarizeWeek(week)).toBe('T2–T3 08:00–17:00 · T4 07:30–16:30')
  })

  it('seven OFF days -> «Nghỉ cả tuần»; empty / invalid -> «Chưa khai lịch»', () => {
    expect(summarizeWeek(Array.from({ length: 7 }, (_, i) => day(i, OFF)))).toBe('Nghỉ cả tuần')
    expect(summarizeWeek([])).toBe('Chưa khai lịch')
    expect(summarizeWeek(undefined)).toBe('Chưa khai lịch')
    expect(summarizeWeek(null)).toBe('Chưa khai lịch')
    expect(summarizeWeek([day(12, FULL)])).toBe('Chưa khai lịch')
  })

  it('missing weekdays are skipped, not invented as «nghỉ»; shuffled input gives the same output', () => {
    expect(summarizeWeek([fullDay(0)])).toBe('T2 08:00–17:00')
    expect(summarizeWeek([fullDay(1), fullDay(0)])).toBe('T2–T3 08:00–17:00')
  })
})
