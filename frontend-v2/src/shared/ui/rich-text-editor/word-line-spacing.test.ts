import { describe, expect, it } from 'vitest'

import { LINE_HEIGHTS } from './editor-options'
import {
  cssToWordLineSpacing,
  DEFAULT_LINE_SPACING,
  parseLineSpacingInput,
  wordLineSpacingToCss,
} from './word-line-spacing'

describe('wordLineSpacingToCss', () => {
  //  ⚠️ Chỗ này TỪNG nhân thêm 1,15 để bản nhập nhìn giống Word, và người dùng
  //  bắt được là hỏng: trang giấy để sẵn `line-height: 1.15`, nên bấm nấc «1,0»
  //  ghi ra đúng 1.15 — không đổi một pixel nào, nhìn như tính năng chết. Chốt
  //  20/08/2026: giãn dòng 1 là 1.
  it('số trên thanh công cụ CHÍNH LÀ line-height, không quy đổi', () => {
    expect(wordLineSpacingToCss(1)).toBe('1')
    expect(wordLineSpacingToCss(1.5)).toBe('1.5')
    expect(wordLineSpacingToCss(2)).toBe('2')
  })

  it('bấm nấc 1,0 phải KHÁC mặc định của trang, không thì bấm như không bấm', () => {
    //  `.doc-page` để `line-height: 1.15`. Nấc nhỏ nhất mà trùng luôn số đó thì
    //  người dùng bấm mãi không thấy gì đổi — đúng lỗi đã báo trên văn bản 217.
    expect(wordLineSpacingToCss(1)).not.toBe(String(DEFAULT_LINE_SPACING))
  })

  it('không để đuôi số thực dấu phẩy động lọt vào style', () => {
    expect(wordLineSpacingToCss(1.15)).toBe('1.15')
    expect(wordLineSpacingToCss(0.1 + 0.2)).toBe('0.3')
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
