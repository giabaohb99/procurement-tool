import { describe, expect, it } from 'vitest'

import { buildRegulationParams, resolveRegulationEmptyMessage } from './customs-regulation'

describe('buildRegulationParams', () => {
  it('sends nothing for the defaults', () => {
    expect(buildRegulationParams('', 'all')).toEqual({})
  })

  //  `list_code` ở backend là `int | None`: gửi «all» hay chuỗi rỗng là 422 và cả bảng đỏ.
  it.each(['all', '', ' ', 'abc', '-1', '4.5'])('never sends a non-numeric list code (%j)', (code) => {
    expect(buildRegulationParams('', code)).not.toHaveProperty('list_code')
  })

  it('trims the keyword and keeps a real list code, including 0', () => {
    expect(buildRegulationParams('  H2SO4 ', '4')).toEqual({ q: 'H2SO4', list_code: '4' })
    expect(buildRegulationParams('   ', '0')).toEqual({ list_code: '0' })
  })
})

describe('resolveRegulationEmptyMessage', () => {
  it('blames the filter only when the catalog has rows', () => {
    expect(resolveRegulationEmptyMessage(12)).toMatch(/khớp/)
    expect(resolveRegulationEmptyMessage(0)).toMatch(/Chưa có danh mục/)
  })
})
