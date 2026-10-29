import { describe, expect, it } from 'vitest'

import { suggestCostCode } from './hr-cost-item-code'

describe('auto code from the item name', () => {
  it('strips Vietnamese accents, uppercases and joins words with _', () => {
    expect(suggestCostCode('Phụ cấp đóng BH', [])).toBe('PHU_CAP_DONG_BH')
    expect(suggestCostCode('Bảo hiểm + công đoàn', [])).toBe('BAO_HIEM_CONG_DOAN')
    expect(suggestCostCode('Quà / phúc lợi theo đợt', [])).toBe('QUA_PHUC_LOI_THEO_DOT')
  })

  it('falls back to KHOAN when the name has nothing usable (empty, spaces, only symbols)', () => {
    expect(suggestCostCode('', [])).toBe('KHOAN')
    expect(suggestCostCode('   ', [])).toBe('KHOAN')
    expect(suggestCostCode('%%% ///', [])).toBe('KHOAN')
    expect(suggestCostCode('', ['KHOAN'])).toBe('KHOAN_2')
  })

  it('adds _2, _3… on clashes instead of reusing a taken code', () => {
    expect(suggestCostCode('Lương', ['LUONG'])).toBe('LUONG_2')
    expect(suggestCostCode('Lương', ['LUONG', 'LUONG_2'])).toBe('LUONG_3')
  })

  it('never exceeds 30 characters, even with a suffix — two long names must not collide', () => {
    const long = 'Phụ cấp trách nhiệm quản lý khu vực phía Nam mở rộng'
    const first = suggestCostCode(long, [])
    expect(first.length).toBeLessThanOrEqual(30)
    const second = suggestCostCode(long, [first])
    expect(second.length).toBeLessThanOrEqual(30)
    expect(second).not.toBe(first)
    expect(second.endsWith('_2')).toBe(true)
    expect(second).toMatch(/^[A-Z0-9_]+$/)
  })

  it('does not leave a double underscore when the cut lands right after a word break', () => {
    //  «_» nằm ở ký tự thứ 28: cắt thân còn 28 cho đuôi «_2» thì thân kết thúc bằng «_» — phải gọt đi.
    const name = 'AAAAAAAAAAAAAA BBBBBBBBBBBB CCCC'
    const code = suggestCostCode(name, [suggestCostCode(name, [])])
    expect(code).toBe('AAAAAAAAAAAAAA_BBBBBBBBBBBB_2')
  })
})
