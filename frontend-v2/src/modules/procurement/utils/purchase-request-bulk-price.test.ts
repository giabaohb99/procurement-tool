import { describe, expect, it } from 'vitest'

import { describeBulkPriceChange, parsePriceInput } from './purchase-request-bulk-price'

describe('parsePriceInput', () => {
  it('keeps the old price for blank, non-numeric or negative input', () => {
    for (const raw of ['', '   ', 'abc', '-1', 'NaN', 'Infinity', '1e999']) {
      expect(parsePriceInput(raw)).toBeUndefined()
    }
  })

  it('accepts zero, decimals and surrounding spaces', () => {
    expect(parsePriceInput('0')).toBe(0)
    expect(parsePriceInput(' 1200.5 ')).toBe(1200.5)
  })
})

// bao-CR-576 — dòng đổi giá phải nổi lên trên bảng; dòng giữ nguyên thì không tô gì.
describe('describeBulkPriceChange', () => {
  it('reports a real change with the new price', () => {
    expect(describeBulkPriceChange(1000, '1200')).toEqual({ next: 1200 })
    expect(describeBulkPriceChange(1000, '0')).toEqual({ next: 0 })
  })

  it('stays quiet when the typed price equals the current one', () => {
    expect(describeBulkPriceChange(1000, '1000')).toBeNull()
    expect(describeBulkPriceChange(1000, '1000.0')).toBeNull()
  })

  it('stays quiet for blank or invalid input, which keeps the old price', () => {
    for (const raw of ['', 'x', '-5']) expect(describeBulkPriceChange(1000, raw)).toBeNull()
  })

  it('treats a missing current price as zero', () => {
    expect(describeBulkPriceChange(undefined, '500')).toEqual({ next: 500 })
    expect(describeBulkPriceChange(null, '0')).toBeNull()
  })
})
