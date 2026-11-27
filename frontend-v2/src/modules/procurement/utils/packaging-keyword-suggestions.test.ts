import { describe, expect, it } from 'vitest'

import { pickKeywordSuggestions as pickSuggestions } from './packaging-keyword-suggestions'

const PRODUCTS = [
  { code: 'HH0713', name: 'Phân bón lá Đầu Trâu 500ml' },
  { code: 'HH0714', name: 'Phân bón lá Đầu Trâu 1 lít' },
]
const COMPONENTS = [{ code: 'CPT0105', name: 'Chai PET 500ml' }]

describe('pickSuggestions', () => {
  it('returns nothing for a blank or whitespace keyword (the list stays closed)', () => {
    expect(pickSuggestions('', PRODUCTS, COMPONENTS)).toEqual([])
    expect(pickSuggestions('   ', PRODUCTS, COMPONENTS)).toEqual([])
  })

  it('matches accent-insensitively on code or name, products before components', () => {
    const got = pickSuggestions('500ml', PRODUCTS, COMPONENTS)
    expect(got.map((item) => [item.kind, item.code])).toEqual([
      ['product', 'HH0713'],
      ['component', 'CPT0105'],
    ])
    expect(pickSuggestions('dau trau 1 lit', PRODUCTS, COMPONENTS).map((item) => item.code)).toEqual(['HH0714'])
  })

  it('caps each kind at six rows so a short keyword does not dump the whole catalogue', () => {
    const many = Array.from({ length: 40 }, (_, i) => ({ code: `HH${1000 + i}`, name: 'Sản phẩm' }))
    expect(pickSuggestions('san pham', many, [])).toHaveLength(6)
  })
})
