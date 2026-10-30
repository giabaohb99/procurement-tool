import { describe, expect, it } from 'vitest'

import { splitInlineEmphasis, stripInlineEmphasis } from './inline-emphasis'

/**
 * bao-CR-695: câu bot / Trợ lý chuyển từ ngoặc kép góc sang `**x**`. Ô chữ trơn vẽ thẳng thì lộ hai dấu sao — hàm này
 * tách ra để vẽ `<strong>` / `<em>`. Chỗ dễ sai: bắt nhầm dấu nhân, gạch đầu dòng `* mục`, dấu không đóng, dấu đứng
 * giữa chữ, chuỗi rỗng.
 */
describe('splitInlineEmphasis', () => {
  it('turns bot bold and italic into segments, keeping the text around them', () => {
    expect(splitInlineEmphasis('Hết lượt; bấm **Làm tiếp** để nối *phiên cũ*.')).toEqual([
      { text: 'Hết lượt; bấm ' },
      { text: 'Làm tiếp', bold: true },
      { text: ' để nối ' },
      { text: 'phiên cũ', italic: true },
      { text: '.' },
    ])
  })

  it('handles a bold label at the very start and several on one line', () => {
    expect(splitInlineEmphasis('**Kết luận:** sửa **a** và **b**')).toEqual([
      { text: 'Kết luận:', bold: true },
      { text: ' sửa ' },
      { text: 'a', bold: true },
      { text: ' và ' },
      { text: 'b', bold: true },
    ])
  })

  it('leaves unclosed, spaced or empty markers exactly as written', () => {
    for (const raw of ['bấm **Làm tiếp', '** cách **', '****', 'a ** b', '**\n**']) {
      expect(stripInlineEmphasis(raw), raw).toBe(raw)
    }
  })

  it('does not eat multiplication, bullet stars or stars inside words', () => {
    for (const raw of ['2*3*4 = 24', '* mục một\n* mục hai', 'file*.py và *.ts', 'a*b*c']) {
      expect(stripInlineEmphasis(raw), raw).toBe(raw)
    }
  })

  it('does not let an italic run across lines', () => {
    expect(stripInlineEmphasis('*đầu dòng\ncuối*')).toBe('*đầu dòng\ncuối*')
  })

  it('returns nothing for empty input and one plain segment for plain text', () => {
    expect(splitInlineEmphasis('')).toEqual([])
    expect(splitInlineEmphasis('chữ thường')).toEqual([{ text: 'chữ thường' }])
  })

  it('never treats markup inside as HTML: angle brackets stay plain text', () => {
    expect(splitInlineEmphasis('**<img src=x onerror=alert(1)>**')).toEqual([
      { text: '<img src=x onerror=alert(1)>', bold: true },
    ])
  })
})
