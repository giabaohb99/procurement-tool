import { describe, expect, it } from 'vitest'

import { USAGE_STYLE } from '@/shared/constants/statuses'

import { USAGE_STYLE_HINTS, styleLabel } from './usage-style-hints'

describe('usage style hints', () => {
  it('has a hint for every backend style code and none for codes that do not exist', () => {
    const codes = USAGE_STYLE.map((o) => Number(o.value)).sort((a, b) => a - b)
    expect(Object.keys(USAGE_STYLE_HINTS).map(Number).sort((a, b) => a - b)).toEqual(codes)
  })

  it('takes the style name from the generated set and survives unknown codes', () => {
    expect(styleLabel(2)).toBe(USAGE_STYLE.find((o) => o.value === '2')?.label)
    expect(styleLabel(99)).toBe('Kiểu 99')
    expect(styleLabel(0)).toBe('Kiểu 0')
  })
})
