import { describe, expect, it } from 'vitest'

import {
  formatPackagingDiff,
  formatPackagingPercent,
  formatPackagingPrice,
  isOutsidePriceLimit,
  packagingDiffTone,
} from './packaging-price-format'

describe('formatPackagingPrice', () => {
  it('keeps two decimals under 100.000 and rounds to the đồng above it', () => {
    expect(formatPackagingPrice(85.456)).toBe('85,46')
    expect(formatPackagingPrice(1234.5)).toBe('1.234,5')
    expect(formatPackagingPrice(123456.78)).toBe('123.457')
  })

  it('shows 0 as a real price but null / NaN as blank (no price yet)', () => {
    expect(formatPackagingPrice(0)).toBe('0')
    expect(formatPackagingPrice(null)).toBe('')
    expect(formatPackagingPrice(undefined)).toBe('')
    expect(formatPackagingPrice(Number.NaN)).toBe('')
  })
})

describe('formatPackagingDiff / formatPackagingPercent', () => {
  it('prefixes a plus only on increases', () => {
    expect(formatPackagingDiff(150)).toBe('+150')
    expect(formatPackagingDiff(-85.5)).toBe('-85,5')
    expect(formatPackagingDiff(0)).toBe('0')
  })

  it('reads the input as a ratio from the server (diff / old), not an already-multiplied percent', () => {
    expect(formatPackagingPercent(0.125)).toBe('+12,5%')
    expect(formatPackagingPercent(-0.03)).toBe('-3,0%')
    expect(formatPackagingPercent(null)).toBe('')
  })
})

describe('packagingDiffTone', () => {
  it('does not colour float noise around zero', () => {
    expect(packagingDiffTone(1e-9)).toBeUndefined()
    expect(packagingDiffTone(-1e-9)).toBeUndefined()
    expect(packagingDiffTone(0.01)).toContain('emerald')
  })
})

describe('isOutsidePriceLimit', () => {
  it('flags prices below the floor or above the ceiling', () => {
    expect(isOutsidePriceLimit(90, 100, null)).toBe(true)
    expect(isOutsidePriceLimit(130, null, 120)).toBe(true)
    expect(isOutsidePriceLimit(110, 100, 120)).toBe(false)
  })

  it('treats the limits themselves as inside', () => {
    expect(isOutsidePriceLimit(100, 100, 120)).toBe(false)
    expect(isOutsidePriceLimit(120, 100, 120)).toBe(false)
  })

  it('treats a 0 ceiling as a real limit, and a missing price as never outside', () => {
    expect(isOutsidePriceLimit(1, null, 0)).toBe(true)
    expect(isOutsidePriceLimit(null, 100, 120)).toBe(false)
  })
})
