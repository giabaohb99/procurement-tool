import { describe, expect, it } from 'vitest'

import { FILTER_ANY, toFilterId } from './employee-filter-id'

describe('toFilterId', () => {
  it('turns a picked id into a number', () => {
    expect(toFilterId('7')).toBe(7)
  })

  it('drops "any", empty, zero, negatives, decimals and garbage so the field is omitted (backend ge=1)', () => {
    for (const raw of [FILTER_ANY, '', '0', '-3', '1.5', 'abc', 'NaN', 'Infinity']) {
      expect(toFilterId(raw)).toBeUndefined()
    }
  })
})
