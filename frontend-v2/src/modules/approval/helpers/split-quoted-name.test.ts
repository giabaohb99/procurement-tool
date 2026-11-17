import { describe, expect, it } from 'vitest'

import { splitQuotedName } from './split-quoted-name'

describe('splitQuotedName', () => {
  //  Phiếu cũ trong CSDL còn ngoặc kép góc; người dùng không muốn thấy dấu đó (duoc-CR-766).
  it('turns an old angle-quoted flow name into a bold segment without the quotes', () => {
    expect(splitQuotedName('Trình duyệt theo luồng \u00abDuyệt đơn nghỉ phép\u00bb bản 3')).toEqual([
      { text: 'Trình duyệt theo luồng ', strong: false },
      { text: 'Duyệt đơn nghỉ phép', strong: true },
      { text: ' bản 3', strong: false },
    ])
  })

  it('treats the new straight-quoted wording the same way', () => {
    expect(splitQuotedName('Trình duyệt theo luồng "Duyệt nghỉ phép" bản 1')).toEqual([
      { text: 'Trình duyệt theo luồng ', strong: false },
      { text: 'Duyệt nghỉ phép', strong: true },
      { text: ' bản 1', strong: false },
    ])
  })

  it('keeps text untouched when there is no quote or the quote is not closed', () => {
    expect(splitQuotedName('Trình duyệt theo luồng phiên bản 8')).toEqual([
      { text: 'Trình duyệt theo luồng phiên bản 8', strong: false },
    ])
    expect(splitQuotedName('Luồng "chưa đóng bản 2')).toEqual([
      { text: 'Luồng "chưa đóng bản 2', strong: false },
    ])
    expect(splitQuotedName('')).toEqual([])
  })

  it('leaves empty quotes as plain text instead of an empty bold segment', () => {
    expect(splitQuotedName('Luồng "" bản 1')).toEqual([{ text: 'Luồng "" bản 1', strong: false }])
  })
})
