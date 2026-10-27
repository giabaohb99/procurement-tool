import { describe, expect, it } from 'vitest'

import { formatAmountParam, parseAmountParam } from './benefit-amount-param'

describe('parseAmountParam / formatAmountParam', () => {
  it('accepts plain digits and drops a fractional part', () => {
    expect(parseAmountParam('500000')).toBe(500000)
    expect(parseAmountParam(' 250000.9 ')).toBe(250000)
  })

  it('turns garbage, negatives, exponents and VN-formatted text from a hand-typed link into 0', () => {
    for (const raw of ['', null, undefined, 'abc', '-5', '1e9', '1.000.000', '5,5']) {
      expect(parseAmountParam(raw)).toBe(0)
    }
  })

  it('clamps above one billion so the screen never shows a value the backend rejects', () => {
    expect(parseAmountParam('99999999999999999999')).toBe(1_000_000_000)
    expect(formatAmountParam(2_000_000_000)).toBe('1000000000')
  })

  it('writes 0, negatives and NaN as an empty param (removed from the URL)', () => {
    expect(formatAmountParam(0)).toBe('')
    expect(formatAmountParam(-1)).toBe('')
    expect(formatAmountParam(Number.NaN)).toBe('')
    expect(formatAmountParam(300000.7)).toBe('300000')
  })
})
