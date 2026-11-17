import { describe, expect, it } from 'vitest'

import {
  applyPriceAfterVatInput,
  applyPriceBeforeVatInput,
  computePriceAfterVat,
  computePriceBeforeVat,
  normalizeVatPercent,
  repriceOnVatChange,
  resolveLinePriceAfterVat,
  stripPriceAfterVatInput,
} from './vat-price'

// duoc-CR-776 — nhập giá sau VAT, tự tính giá trước thuế.
describe('computePriceAfterVat / computePriceBeforeVat', () => {
  it('turns 100.000 pre-VAT at 8% into 108.000 and back', () => {
    expect(computePriceAfterVat(100000, 8)).toBe(108000)
    expect(computePriceBeforeVat(108000, 8)).toBe(100000)
  })

  it('back-computes 100.000 post-VAT at 8% to 92.592,5926 (4 decimals, matches the price column)', () => {
    expect(computePriceBeforeVat(100000, 8)).toBe(92592.5926)
  })

  it('rounds post-VAT to 2 decimals so 166.666,67 at 8% is exactly 180.000 (bao-CR-307)', () => {
    expect(computePriceAfterVat(166666.67, 8)).toBe(180000)
  })

  it('keeps both prices equal at VAT 0 (imported goods force line VAT to 0)', () => {
    expect(computePriceAfterVat(12345.6789, 0)).toBe(12345.68)
    expect(computePriceBeforeVat(12345.67, 0)).toBe(12345.67)
  })

  it('treats empty, negative and non-number VAT as 0', () => {
    for (const vat of [undefined, null, '', '   ', -8, 'abc', Number.NaN]) {
      expect(computePriceAfterVat(1000, vat)).toBe(1000)
      expect(computePriceBeforeVat(1000, vat)).toBe(1000)
    }
  })

  it('returns null (no compute) for empty, negative or non-number prices', () => {
    for (const price of [undefined, null, '', '  ', -1, 'abc', Number.NaN, Number.POSITIVE_INFINITY]) {
      expect(computePriceAfterVat(price, 8)).toBeNull()
      expect(computePriceBeforeVat(price, 8)).toBeNull()
    }
  })

  it('accepts numeric strings as typed by the user', () => {
    expect(computePriceBeforeVat('108000', '8')).toBe(100000)
  })

  it('handles zero price as a real value, not as empty', () => {
    expect(computePriceAfterVat(0, 8)).toBe(0)
    expect(computePriceBeforeVat(0, 8)).toBe(0)
  })

  it('stays exact on large prices and never returns Infinity on overflow', () => {
    expect(computePriceAfterVat(1_000_000_000_000, 8)).toBe(1_080_000_000_000)
    expect(computePriceBeforeVat(1_080_000_000_000, 8)).toBe(1_000_000_000_000)
    expect(computePriceAfterVat(Number.MAX_VALUE, 8)).toBeNull()
  })

  it('survives a round trip post -> pre -> post for odd amounts', () => {
    for (const gross of [1, 0.01, 99999.99, 1234567.89]) {
      for (const vat of [5, 8, 10]) {
        const pre = computePriceBeforeVat(gross, vat)
        expect(computePriceAfterVat(pre, vat)).toBe(gross)
      }
    }
  })
})

describe('normalizeVatPercent', () => {
  it('keeps a valid percent and zeroes anything else', () => {
    expect(normalizeVatPercent(8)).toBe(8)
    expect(normalizeVatPercent('10')).toBe(10)
    expect(normalizeVatPercent(-5)).toBe(0)
    expect(normalizeVatPercent(undefined)).toBe(0)
  })
})

describe('line draft helpers', () => {
  it('typing post-VAT stores the typed value and the back-computed pre-VAT price', () => {
    expect(applyPriceAfterVatInput(100000, 8)).toEqual({
      price: 92592.5926,
      price_after_vat_input: 100000,
    })
  })

  it('typing an invalid post-VAT clears the price instead of leaving a stale one', () => {
    expect(applyPriceAfterVatInput(-5, 8)).toEqual({ price: 0, price_after_vat_input: undefined })
  })

  it('typing pre-VAT drops the typed post-VAT value', () => {
    expect(applyPriceBeforeVatInput(5000)).toEqual({ price: 5000, price_after_vat_input: undefined })
  })

  it('shows the typed post-VAT value while it still matches the price', () => {
    const line = { price: 92592.5926, price_after_vat_input: 100000 }
    expect(resolveLinePriceAfterVat(line, 8)).toBe(100000)
  })

  it('ignores a typed post-VAT value once something else changed the price (eg. purchase history)', () => {
    const line = { price: 50000, price_after_vat_input: 100000 }
    expect(resolveLinePriceAfterVat(line, 8)).toBe(54000)
  })

  it('computes post-VAT from price for a line just loaded from the server', () => {
    expect(resolveLinePriceAfterVat({ price: 100000 }, 8)).toBe(108000)
  })

  it('changing VAT after typing post-VAT keeps post-VAT and recomputes pre-VAT', () => {
    const line = { price: 92592.5926, price_after_vat_input: 100000 }
    expect(repriceOnVatChange(line, 8, 10)).toEqual({
      price: 90909.0909,
      price_after_vat_input: 100000,
    })
  })

  it('changing VAT after typing pre-VAT (or on a loaded line) keeps the pre-VAT price', () => {
    expect(repriceOnVatChange({ price: 100000 }, 8, 10)).toEqual({
      price: 100000,
      price_after_vat_input: undefined,
    })
  })

  it('changing VAT with a stale typed post-VAT value falls back to keeping pre-VAT', () => {
    const line = { price: 50000, price_after_vat_input: 100000 }
    expect(repriceOnVatChange(line, 8, 0)).toEqual({ price: 50000, price_after_vat_input: undefined })
  })

  it('changing VAT to 0 after typing post-VAT makes both prices equal', () => {
    const line = { price: 92592.5926, price_after_vat_input: 100000 }
    expect(repriceOnVatChange(line, 8, 0)).toEqual({ price: 100000, price_after_vat_input: 100000 })
  })

  it('strips the client-only field from the payload line', () => {
    const stripped = stripPriceAfterVatInput({ price: 1, vat: 8, price_after_vat_input: 1.08 })
    expect(stripped).toEqual({ price: 1, vat: 8 })
    expect('price_after_vat_input' in stripped).toBe(false)
  })
})
