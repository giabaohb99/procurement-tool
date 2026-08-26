import { describe, expect, it } from 'vitest'

import {
  joinSections,
  splitHtmlSections,
  suggestExcerptTitle,
} from './split-html-sections'

const BAI = `
  <p style="text-align:center">CỘNG HÒA XÃ HỘI CHỦ NGHĨA VIỆT NAM</p>
  <h1>Chương I. Quy định chung</h1>
  <p>Nội dung chương một.</p>
  <h2>Điều 1. Phạm vi</h2>
  <p>Nội dung điều một.</p>
  <h2>Điều 2. Giải thích</h2>
  <p>Nội dung điều hai.</p>
  <h1>Chương II. Soạn thảo</h1>
  <p>Nội dung chương hai.</p>
`

describe('splitHtmlSections', () => {
  it('cắt theo tiêu đề, giữ đúng tên và cấp', () => {
    const item = splitHtmlSections(BAI)

    expect(item.map((m) => [m.level, m.title])).toEqual([
      [1, 'Chương I. Quy định chung'],
      [2, 'Điều 1. Phạm vi'],
      [2, 'Điều 2. Giải thích'],
      [1, 'Chương II. Soạn thảo'],
    ])
  })

  it('chọn chương thì lấy TRỌN các điều nằm trong chương đó', () => {
    //  Đây là lý do chính của việc chọn theo mục lục: tick một cái thay vì
    //  bôi đen cả trang.
    const chuongI = splitHtmlSections(BAI)[0]

    expect(chuongI.html).toContain('Điều 1. Phạm vi')
    expect(chuongI.html).toContain('Điều 2. Giải thích')
    expect(chuongI.html).not.toContain('Chương II')
  })

  it('mỗi điều vẫn là một mục riêng để tick lẻ được', () => {
    const dieu1 = splitHtmlSections(BAI)[1]

    expect(dieu1.html).toContain('Nội dung điều một.')
    expect(dieu1.html).not.toContain('Điều 2')
  })

  it('bỏ phần trước tiêu đề đầu tiên — đó là khối đầu văn bản', () => {
    //  Chép quốc hiệu sang bản trích là thành hai khối đầu chồng nhau.
    const item = splitHtmlSections(BAI)

    expect(item.every((m) => !m.html.includes('CỘNG HÒA'))).toBe(true)
  })

  it('văn bản chưa chia mục thì trả rỗng, không nổ', () => {
    expect(splitHtmlSections('<p>Chỉ có một đoạn.</p>')).toEqual([])
    expect(splitHtmlSections('')).toEqual([])
  })

  it('giữ nguyên bảng và danh sách nằm trong mục', () => {
    const item = splitHtmlSections(
      '<h1>A</h1><table><tbody><tr><td><p>ô</p></td></tr></tbody></table><ul><li>ý</li></ul>',
    )

    expect(item[0].html).toContain('<table>')
    expect(item[0].html).toContain('<ul>')
  })
})

describe('joinSections', () => {
  it('gộp theo ĐÚNG THỨ TỰ trong văn bản, không theo thứ tự tick', () => {
    const item = splitHtmlSections(BAI)
    const out = joinSections(item, [item[3].id, item[1].id])

    expect(out.indexOf('Điều 1')).toBeLessThan(out.indexOf('Chương II'))
  })

  it('không tick gì thì ra chuỗi rỗng', () => {
    expect(joinSections(splitHtmlSections(BAI), [])).toBe('')
  })
})

describe('suggestExcerptTitle', () => {
  it('một mục thì lấy thẳng tên mục', () => {
    const item = splitHtmlSections(BAI)

    expect(suggestExcerptTitle(item, [item[1].id])).toBe('Trích Điều 1. Phạm vi')
  })

  it('nhiều mục thì nói rõ còn bao nhiêu mục nữa', () => {
    const item = splitHtmlSections(BAI)

    expect(suggestExcerptTitle(item, [item[1].id, item[2].id, item[3].id])).toBe(
      'Trích Điều 1. Phạm vi và 2 mục khác',
    )
  })

  it('chưa tick gì thì không gợi ý gì', () => {
    expect(suggestExcerptTitle(splitHtmlSections(BAI), [])).toBe('')
  })
})
