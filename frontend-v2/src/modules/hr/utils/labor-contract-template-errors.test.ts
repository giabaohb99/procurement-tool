import { describe, expect, it } from 'vitest'

import { extractUnknownPlaceholders } from './labor-contract-template-errors'

const wrap = (error: unknown) => ({ response: { data: { error } } })

describe('extractUnknownPlaceholders', () => {
  it('đọc danh sách biến lạ từ details.unknown của lỗi 422', () => {
    const err = wrap({ code: 'validation', message: 'x', details: { unknown: ['ho_ten_sai', 'luong'] } })
    expect(extractUnknownPlaceholders(err)).toEqual(['ho_ten_sai', 'luong'])
  })

  it('khử trùng, bỏ phần tử rỗng và phần tử không phải chuỗi', () => {
    const err = wrap({ details: { unknown: ['a', 'a', ' ', '', 5, null, ' b '] } })
    expect(extractUnknownPlaceholders(err)).toEqual(['a', 'b'])
  })

  it('details là MẢNG (lỗi Pydantic) thì không phải biến lạ', () => {
    expect(extractUnknownPlaceholders(wrap({ details: [{ loc: ['body', 'name'], msg: 'x' }] }))).toEqual([])
  })

  it.each([undefined, null, 'lỗi', 42, {}, { response: {} }, { response: { data: {} } }, wrap(null), wrap('x')])(
    'đầu vào lạ %p trả mảng rỗng, không ném lỗi',
    (input) => {
      expect(extractUnknownPlaceholders(input)).toEqual([])
    },
  )

  it('unknown không phải mảng thì bỏ qua', () => {
    expect(extractUnknownPlaceholders(wrap({ details: { unknown: 'ho_ten' } }))).toEqual([])
  })
})
