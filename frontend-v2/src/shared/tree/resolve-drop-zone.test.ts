import { describe, expect, it } from 'vitest'

import { resolveDropZone } from './resolve-drop-zone'

describe('resolveDropZone', () => {
  it('không khả năng nào hợp lệ → null bất kể vị trí con trỏ', () => {
    expect(resolveDropZone(0, { canDropInto: false, canReorder: false })).toBeNull()
    expect(resolveDropZone(0.5, { canDropInto: false, canReorder: false })).toBeNull()
    expect(resolveDropZone(1, { canDropInto: false, canReorder: false })).toBeNull()
  })

  it('chỉ đổi CHA hợp lệ → cả dòng là "into", không phụ thuộc vị trí con trỏ', () => {
    expect(resolveDropZone(0, { canDropInto: true, canReorder: false })).toBe('into')
    expect(resolveDropZone(0.5, { canDropInto: true, canReorder: false })).toBe('into')
    expect(resolveDropZone(0.99, { canDropInto: true, canReorder: false })).toBe('into')
  })

  it('chỉ đổi THỨ TỰ hợp lệ → chia đôi dòng ở đúng ratioY = 0.5, không có vùng "into"', () => {
    expect(resolveDropZone(0, { canDropInto: false, canReorder: true })).toBe('before')
    expect(resolveDropZone(0.49, { canDropInto: false, canReorder: true })).toBe('before')
    expect(resolveDropZone(0.5, { canDropInto: false, canReorder: true })).toBe('after')
    expect(resolveDropZone(1, { canDropInto: false, canReorder: true })).toBe('after')
  })

  it('cả hai hợp lệ → chia ba, mép trên/dưới 30% là đổi thứ tự, giữa là đổi cha', () => {
    const opts = { canDropInto: true, canReorder: true }
    expect(resolveDropZone(0, opts)).toBe('before')
    expect(resolveDropZone(0.29, opts)).toBe('before')
    expect(resolveDropZone(0.3, opts)).toBe('into')
    expect(resolveDropZone(0.5, opts)).toBe('into')
    expect(resolveDropZone(0.7, opts)).toBe('into')
    expect(resolveDropZone(0.71, opts)).toBe('after')
    expect(resolveDropZone(1, opts)).toBe('after')
  })

  it('ratioY âm hoặc vượt 1 (con trỏ ra ngoài dòng do làm tròn số) vẫn không nổ, xử lý như biên gần nhất', () => {
    expect(resolveDropZone(-0.5, { canDropInto: true, canReorder: true })).toBe('before')
    expect(resolveDropZone(1.5, { canDropInto: true, canReorder: true })).toBe('after')
  })

  it('ratioY = NaN (dòng cao 0px trong môi trường test không đo được DOM) rơi về "into" khi có, không văng lỗi', () => {
    expect(resolveDropZone(NaN, { canDropInto: true, canReorder: false })).toBe('into')
    expect(resolveDropZone(NaN, { canDropInto: true, canReorder: true })).toBe('into')
    expect(resolveDropZone(NaN, { canDropInto: false, canReorder: true })).toBe('after')
  })
})
