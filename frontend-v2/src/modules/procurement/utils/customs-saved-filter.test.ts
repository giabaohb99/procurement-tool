// bao-CR-496 — bộ lọc đã lưu chỉ mang các Ô LỌC, và chọn nó là màn hình về đúng trạng thái đó.
import { describe, expect, it } from 'vitest'

import { collectFilterParams, parseFilterParams, sameFilterParams } from './customs-saved-filter'

const NAMES = ['q', 'hs_code', 'origin', 'date_from', 'date_to'] as const

describe('collectFilterParams', () => {
  it('keeps only filter keys, in declared order, and drops blanks', () => {
    const url = new URLSearchParams('page=3&origin=CN&q=abamectin+3.6&hs_code=&tab=chart')
    expect(collectFilterParams(url, NAMES)).toBe('q=abamectin+3.6&origin=CN')
  })

  it('keeps every value of a multi-value key', () => {
    const url = new URLSearchParams('origin=CN&origin=IN')
    expect(collectFilterParams(url, NAMES)).toBe('origin=CN&origin=IN')
  })

  it('returns an empty string when nothing is filtered', () => {
    expect(collectFilterParams(new URLSearchParams('page=2'), NAMES)).toBe('')
  })
})

describe('parseFilterParams', () => {
  it('sets present keys and NULLS every absent filter so the screen resets to the saved state', () => {
    expect(parseFilterParams('q=abamectin&origin=CN', NAMES)).toEqual({
      q: 'abamectin',
      hs_code: null,
      origin: 'CN',
      date_from: null,
      date_to: null,
    })
  })

  it('ignores keys that are not filters — a stray string in the DB cannot write page/tab', () => {
    const out = parseFilterParams('page=9&tab=chart&hs_code=3808', NAMES)
    expect(out).not.toHaveProperty('page')
    expect(out).not.toHaveProperty('tab')
    expect(out.hs_code).toBe('3808')
  })

  it('joins multi-value keys with a comma and survives garbage input', () => {
    expect(parseFilterParams('origin=CN&origin=IN', NAMES).origin).toBe('CN,IN')
    expect(parseFilterParams('', NAMES).q).toBeNull()
    expect(parseFilterParams('%%%&&==', NAMES).q).toBeNull()
  })
})

describe('sameFilterParams', () => {
  it('compares only filter keys regardless of order or page noise', () => {
    expect(sameFilterParams('origin=CN&q=a&page=2', 'q=a&origin=CN', NAMES)).toBe(true)
    expect(sameFilterParams('q=a', 'q=b', NAMES)).toBe(false)
    expect(sameFilterParams('', 'page=5', NAMES)).toBe(true)
  })
})
