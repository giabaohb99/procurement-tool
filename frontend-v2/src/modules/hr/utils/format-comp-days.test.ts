import { describe, expect, it } from 'vitest'

import { formatCompDays } from './format-comp-days'

describe('formatCompDays', () => {
  it('uses a decimal comma and drops trailing zeros', () => {
    expect(formatCompDays(0.5)).toBe('0,5')
    expect(formatCompDays(1)).toBe('1')
    expect(formatCompDays(0)).toBe('0')
  })
})
