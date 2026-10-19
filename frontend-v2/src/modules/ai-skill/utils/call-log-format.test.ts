import { describe, expect, it } from 'vitest'

import { formatResultChars } from './call-log-format'

describe('formatResultChars', () => {
  it('prints a dash for 0 — non tools/call rows and rows before ai-CR-228 are not "empty result"', () => {
    expect(formatResultChars(0)).toBe('—')
  })

  it('prints a dash when an older server does not send the field at all', () => {
    expect(formatResultChars(undefined)).toBe('—')
    expect(formatResultChars(null)).toBe('—')
  })

  it('never shows negative or broken numbers as real lengths', () => {
    expect(formatResultChars(-5)).toBe('—')
    expect(formatResultChars(Number.NaN)).toBe('—')
    expect(formatResultChars(Number.POSITIVE_INFINITY)).toBe('—')
  })

  it('uses Vietnamese thousand separators (dot), not commas', () => {
    expect(formatResultChars(1)).toBe('1')
    expect(formatResultChars(999)).toBe('999')
    expect(formatResultChars(1000)).toBe('1.000')
    expect(formatResultChars(10000)).toBe('10.000')
    expect(formatResultChars(1234567)).toBe('1.234.567')
  })

  it('does not leak a decimal part even if the server ever sends one', () => {
    expect(formatResultChars(1234.6)).toBe('1.235')
  })
})
