import { describe, expect, it } from 'vitest'

import { parseOffsetsParam, splitLineOffset } from './assistant-offsets'

describe('parseOffsetsParam', () => {
  it('parses id:amount pairs into a map', () => {
    const map = parseOffsetsParam('12:300,34:500.5')
    expect(map.get(12)).toBe(300)
    expect(map.get(34)).toBe(500.5)
    expect(map.size).toBe(2)
  })

  it('returns an empty map for null or empty input', () => {
    expect(parseOffsetsParam(null).size).toBe(0)
    expect(parseOffsetsParam('').size).toBe(0)
  })

  it('skips malformed pieces without dropping valid ones', () => {
    //  URL do người/tool khác ghép có thể hỏng từng mẩu — hỏng mẩu nào bỏ mẩu đó,
    //  đừng vứt cả chuỗi (form vẫn điền sẵn được phần lành).
    const map = parseOffsetsParam('abc,12:xyz,:100,7:,0:50,-3:20,5:250,8:0,9:-10,1.5:40')
    expect(map.size).toBe(1)
    expect(map.get(5)).toBe(250)
  })

  it('keeps the last amount when the same id appears twice', () => {
    const map = parseOffsetsParam('5:100,5:200')
    expect(map.get(5)).toBe(200)
  })
})

describe('splitLineOffset', () => {
  it('splits remaining into cash part and offset part', () => {
    expect(splitLineOffset(1000, 300)).toEqual({ amount: 700, offset: 300 })
  })

  it('clamps the offset to remaining — never proposes more than the debt', () => {
    //  Khoản nợ có thể đã được trả bớt giữa lúc chat và lúc mở form; đề xuất trên URL
    //  không được đè lên thực tế.
    expect(splitLineOffset(200, 999)).toEqual({ amount: 0, offset: 200 })
  })

  it('treats negative or non-finite suggestions as zero', () => {
    expect(splitLineOffset(500, -50)).toEqual({ amount: 500, offset: 0 })
    expect(splitLineOffset(500, Number.NaN)).toEqual({ amount: 500, offset: 0 })
  })

  it('treats negative or non-finite remaining as zero debt', () => {
    expect(splitLineOffset(-100, 50)).toEqual({ amount: 0, offset: 0 })
    expect(splitLineOffset(Number.NaN, 50)).toEqual({ amount: 0, offset: 0 })
  })

  it('rounds both parts to 2 decimals so cents do not drift', () => {
    const { amount, offset } = splitLineOffset(100.555, 33.333)
    expect(offset).toBe(33.33)
    expect(amount).toBe(67.23)
  })
})
