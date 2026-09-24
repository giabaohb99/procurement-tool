import { afterEach, describe, expect, it, vi } from 'vitest'

import { recentBookYears } from './recent-book-years'

afterEach(() => {
  vi.useRealTimers()
})

describe('recentBookYears', () => {
  it('trả đúng bốn năm, năm hiện tại đứng đầu và giảm dần liên tiếp', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-09-23T10:00:00+07:00'))

    expect(recentBookYears()).toEqual([2026, 2025, 2024, 2023])
  })

  it('đổi năm theo đồng hồ hệ thống, không khai cứng', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2031-01-01T00:30:00+07:00'))

    expect(recentBookYears()).toEqual([2031, 2030, 2029, 2028])
  })
})
