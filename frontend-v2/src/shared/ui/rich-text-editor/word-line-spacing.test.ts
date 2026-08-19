import { describe, expect, it } from 'vitest'

import { LINE_HEIGHTS } from './editor-options'
import {
  cssToWordLineSpacing,
  parseLineSpacingInput,
  wordLineSpacingToCss,
} from './word-line-spacing'

describe('wordLineSpacingToCss', () => {
  // Lỗi từng gặp: trang giấy để `line-height: 1.5` y như số ghi trong Word, đặt
  // cạnh bản Word thì dòng chật hơn 15% vì Word nhân theo chiều cao dòng đơn.
  it('đổi 1,5 dòng của Word thành 1.725 chứ không giữ nguyên 1.5', () => {
    expect(wordLineSpacingToCss(1.5)).toBe('1.725')
  })

  it('giãn dòng đơn vẫn cao hơn cỡ chữ — bằng đúng dòng đơn của Times New Roman', () => {
    expect(wordLineSpacingToCss(1)).toBe('1.15')
  })

  it('không để đuôi số thực dấu phẩy động lọt vào style', () => {
    expect(wordLineSpacingToCss(1.15)).toBe('1.3225')
    expect(wordLineSpacingToCss(2)).toBe('2.3')
  })

  it('mọi nấc trong thanh công cụ đều là số CSS hợp lệ', () => {
    for (const option of LINE_HEIGHTS) {
      expect(Number.isNaN(Number(option.value))).toBe(false)
    }
  })

  it('bày đúng bộ nấc của Word, nhãn viết theo lối tiếng Việt', () => {
    expect(LINE_HEIGHTS.map((option) => option.label)).toEqual([
      '1,0',
      '1,15',
      '1,5',
      '2,0',
      '2,5',
      '3,0',
    ])
  })
})

describe('cssToWordLineSpacing', () => {
  it('đọc ngược ra đúng số dòng để menu tick được nấc đang dùng', () => {
    expect(cssToWordLineSpacing(wordLineSpacingToCss(1.5))).toBe(1.5)
    expect(cssToWordLineSpacing(wordLineSpacingToCss(1))).toBe(1)
  })

  it('đoạn không đặt riêng, hoặc đặt chiều cao tuyệt đối, thì không tick nấc nào', () => {
    expect(cssToWordLineSpacing(null)).toBeNull()
    expect(cssToWordLineSpacing('')).toBeNull()
    // "Exactly 18pt" của Word, tệp .docx nhập vào có thể mang theo.
    expect(cssToWordLineSpacing('24px')).toBeNull()
  })
})

describe('parseLineSpacingInput', () => {
  it('nhận dấu phẩy thập phân vì người Việt gõ 1,3 chứ không gõ 1.3', () => {
    expect(parseLineSpacingInput('1,3')).toBe(1.3)
    expect(parseLineSpacingInput(' 2.25 ')).toBe(2.25)
  })

  it('chặn số ngoài khoảng và chữ không phải số', () => {
    expect(parseLineSpacingInput('0.2')).toBeNull()
    expect(parseLineSpacingInput('99')).toBeNull()
    expect(parseLineSpacingInput('abc')).toBeNull()
    expect(parseLineSpacingInput('')).toBeNull()
  })
})
