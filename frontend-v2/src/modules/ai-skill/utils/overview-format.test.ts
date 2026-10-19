import { describe, expect, it } from 'vitest'

import { describeChange, shortDay } from './overview-format'

describe('describeChange', () => {
  it('says there was nothing to compare with when the previous week had no calls', () => {
    expect(describeChange(null, 0)).toBe('7 ngày trước chưa có lượt nào')
  })

  it('stays silent on a null percent with a non-zero previous week, and on NaN or Infinity', () => {
    expect(describeChange(null, 5)).toBe('')
    expect(describeChange(Number.NaN, 5)).toBe('')
    expect(describeChange(Number.POSITIVE_INFINITY, 0)).toBe('')
  })

  it('signs growth, keeps the minus of a drop, and writes Vietnamese decimals', () => {
    expect(describeChange(25, 4)).toBe('+25% so với 7 ngày trước')
    expect(describeChange(-12.5, 8)).toBe('-12,5% so với 7 ngày trước')
    expect(describeChange(0, 3)).toBe('bằng 7 ngày trước')
  })
})

describe('shortDay', () => {
  it('turns an ISO day into day/month without going through Date (no time-zone shift)', () => {
    expect(shortDay('2026-10-17')).toBe('17/10')
    expect(shortDay('2026-01-01')).toBe('01/01')
  })

  it('leaves anything else untouched', () => {
    expect(shortDay('')).toBe('')
    expect(shortDay('hom-nay')).toBe('hom-nay')
  })
})
