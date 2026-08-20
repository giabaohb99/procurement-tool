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
    expect(wordLineSpacingToCss(1)).toBe('1em')
    expect(wordLineSpacingToCss(1.5)).toBe('1.5em')
    expect(wordLineSpacingToCss(2)).toBe('2em')
  })

  it('LUÔN kèm đơn vị em — không đơn vị thì chữ to trong đoạn phá vỡ giãn dòng', () => {
    //  LỖI ĐÃ XẢY RA (chiều 20/08/2026): đặt giãn dòng 1 cho một đoạn mà nó vẫn
    //  thưa hơn đoạn dưới. `line-height` không đơn vị kế thừa xuống con dưới
    //  dạng CON SỐ, nên mỗi `<span style="font-size: 20pt">` lại nhân 1 với cỡ
    //  chữ của chính nó. Đo trên Chrome: đoạn không span cao 18,7px mỗi dòng,
    //  đoạn có span 20pt cao 26,7px — cùng đặt `line-height: 1`.
    //  `em` quy ra px ngay tại `<p>` rồi mới kế thừa nên con không nhân lại.
    for (const lines of [1, 1.15, 1.5, 2, 2.5, 3]) {
      expect(wordLineSpacingToCss(lines)).toMatch(/em$/)
    }
  })

  it('bấm nấc 1,0 phải KHÁC mặc định của trang, không thì bấm như không bấm', () => {
    //  `.doc-page` để `line-height: 1.15`. Nấc nhỏ nhất mà trùng luôn số đó thì
    //  người dùng bấm mãi không thấy gì đổi — đúng lỗi đã báo trên văn bản 217.
    expect(cssToWordLineSpacing(wordLineSpacingToCss(1))).not.toBe(DEFAULT_LINE_SPACING)
  })

  it('không để đuôi số thực dấu phẩy động lọt vào style', () => {
    expect(wordLineSpacingToCss(1.15)).toBe('1.15em')
    expect(wordLineSpacingToCss(0.1 + 0.2)).toBe('0.3em')
  })

  it('mọi nấc trong thanh công cụ đều là giá trị CSS hợp lệ và đọc ngược được', () => {
    for (const option of LINE_HEIGHTS) {
      expect(option.value).toMatch(/^\d+(\.\d+)?em$/)
      expect(cssToWordLineSpacing(option.value)).toBe(option.lines)
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

  it('vẫn đọc được số TRẦN của văn bản lưu trước 20/08/2026', () => {
    //  Bỏ nhánh này là mọi văn bản đã lưu thôi tick nấc nào cả.
    expect(cssToWordLineSpacing('1.5')).toBe(1.5)
    expect(cssToWordLineSpacing('1.5em')).toBe(1.5)
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
