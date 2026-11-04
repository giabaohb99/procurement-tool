import { describe, expect, it } from 'vitest'

import { computeEmployeeMilestones, formatTenure } from './employee-milestones'

const on = (y: number, m: number, d: number) => new Date(y, m - 1, d)

describe('computeEmployeeMilestones', () => {
  it('flags the birthday only on the matching day and month', () => {
    expect(computeEmployeeMilestones('1990-11-02', null, on(2026, 11, 2)).isBirthday).toBe(true)
    expect(computeEmployeeMilestones('1990-11-03', null, on(2026, 11, 2)).isBirthday).toBe(false)
    expect(computeEmployeeMilestones('1990-10-02', null, on(2026, 11, 2)).isBirthday).toBe(false)
  })

  it('ignores the time of day on "today"', () => {
    const lateEvening = new Date(2026, 10, 2, 23, 59)
    expect(computeEmployeeMilestones('1990-11-02', '2020-11-02', lateEvening)).toMatchObject({
      isBirthday: true,
      anniversaryYears: 6,
    })
  })

  it('never shows a birthday when the masked date comes back empty or null', () => {
    //  Người thiếu employee_sensitive.read nhận '' / null — không được hiện gì.
    for (const masked of ['', null, undefined]) {
      expect(computeEmployeeMilestones(masked, null, on(2026, 11, 2)).isBirthday).toBe(false)
    }
  })

  it('treats garbage date strings as missing instead of crashing', () => {
    expect(computeEmployeeMilestones('not-a-date', '02/11/2020', on(2026, 11, 2))).toEqual({
      isBirthday: false,
      anniversaryYears: 0,
      tenure: null,
    })
  })

  it('does not call a future birth date a birthday', () => {
    expect(computeEmployeeMilestones('2030-11-02', null, on(2026, 11, 2)).isBirthday).toBe(false)
  })

  it('celebrates a 29 Feb birthday on 28 Feb of a non-leap year, and not on 1 Mar', () => {
    expect(computeEmployeeMilestones('2000-02-29', null, on(2027, 2, 28)).isBirthday).toBe(true)
    expect(computeEmployeeMilestones('2000-02-29', null, on(2027, 3, 1)).isBirthday).toBe(false)
    //  Năm nhuận thì đúng ngày 29, ngày 28 KHÔNG phải sinh nhật.
    expect(computeEmployeeMilestones('2000-02-29', null, on(2028, 2, 28)).isBirthday).toBe(false)
    expect(computeEmployeeMilestones('2000-02-29', null, on(2028, 2, 29)).isBirthday).toBe(true)
  })

  it('counts work anniversaries only from the first full year', () => {
    expect(computeEmployeeMilestones(null, '2026-11-02', on(2026, 11, 2)).anniversaryYears).toBe(0)
    expect(computeEmployeeMilestones(null, '2025-11-02', on(2026, 11, 2)).anniversaryYears).toBe(1)
    expect(computeEmployeeMilestones(null, '2016-11-02', on(2026, 11, 2)).anniversaryYears).toBe(10)
    expect(computeEmployeeMilestones(null, '2016-11-03', on(2026, 11, 2)).anniversaryYears).toBe(0)
  })

  it('computes tenure in full months and stays null before the hire date', () => {
    expect(computeEmployeeMilestones(null, '2023-09-15', on(2026, 11, 2)).tenure).toEqual({
      years: 3,
      months: 1,
    })
    //  Chưa tới ngày 15 của tháng thì tháng đó chưa tròn.
    expect(computeEmployeeMilestones(null, '2026-10-15', on(2026, 11, 14)).tenure).toEqual({
      years: 0,
      months: 0,
    })
    expect(computeEmployeeMilestones(null, '2026-10-15', on(2026, 11, 15)).tenure).toEqual({
      years: 0,
      months: 1,
    })
    expect(computeEmployeeMilestones(null, '2027-01-01', on(2026, 11, 2)).tenure).toBeNull()
    expect(computeEmployeeMilestones(null, null, on(2026, 11, 2)).tenure).toBeNull()
  })

  it('treats the last day of a shorter month as a full month for month-end hire dates', () => {
    //  31/01 → 28/02: tháng 2 không có ngày 31, ngày cuối tháng là đã tròn 1 tháng.
    expect(computeEmployeeMilestones(null, '2026-01-31', on(2026, 2, 28)).tenure).toEqual({
      years: 0,
      months: 1,
    })
    expect(computeEmployeeMilestones(null, '2026-01-31', on(2026, 2, 27)).tenure).toEqual({
      years: 0,
      months: 0,
    })
    expect(computeEmployeeMilestones(null, '2026-01-31', on(2026, 4, 30)).tenure).toEqual({
      years: 0,
      months: 3,
    })
  })

  it('keeps tenure and the anniversary badge in agreement for a 29 Feb hire date', () => {
    //  Lỗi do review bắt: 28/02/2025 từng hiện "Tròn 1 năm" cạnh thâm niên "11 tháng".
    expect(computeEmployeeMilestones(null, '2024-02-29', on(2025, 2, 28))).toEqual({
      isBirthday: false,
      anniversaryYears: 1,
      tenure: { years: 1, months: 0 },
    })
  })
})

describe('formatTenure', () => {
  it('reads years and months in Vietnamese and never prints an empty string', () => {
    expect(formatTenure({ years: 3, months: 2 })).toBe('3 năm 2 tháng')
    expect(formatTenure({ years: 3, months: 0 })).toBe('3 năm')
    expect(formatTenure({ years: 0, months: 5 })).toBe('5 tháng')
    expect(formatTenure({ years: 0, months: 0 })).toBe('Dưới 1 tháng')
  })
})
