import { describe, expect, it } from 'vitest'

import { isRichEmpty, plainText, toRichHtml } from './description-html'

describe('plainText', () => {
  it('bỏ thẻ nhưng không dính hai từ ở hai thẻ liền nhau vào nhau', () => {
    expect(plainText('<p>In tem</p><p>nhãn</p>')).toBe('In tem nhãn')
  })

  it('đổi thực thể về ký tự thật để tìm kiếm gõ "&" vẫn ra', () => {
    expect(plainText('<p>R&amp;D&nbsp;team</p>')).toBe('R&D team')
  })

  it('chuỗi rỗng và chuỗi chỉ có thẻ đều ra rỗng', () => {
    expect(plainText('')).toBe('')
    expect(plainText('<p></p><p><br></p>')).toBe('')
  })
})

describe('isRichEmpty', () => {
  //  Tiptap trả đúng chuỗi này cho ô vừa bị xóa sạch — coi nó là "có nội dung"
  //  thì panel hiện một khối trắng thay cho câu mời «Thêm mô tả».
  it('coi <p></p> của Tiptap là trống', () => {
    expect(isRichEmpty('<p></p>')).toBe(true)
    expect(isRichEmpty('   ')).toBe(true)
  })

  it('bài chỉ có ảnh / bảng / đường kẻ thì KHÔNG trống dù không có chữ nào', () => {
    expect(isRichEmpty('<img src="a.png">')).toBe(false)
    expect(isRichEmpty('<table><tr><td></td></tr></table>')).toBe(false)
    expect(isRichEmpty('<hr>')).toBe(false)
  })

  it('có chữ thì không trống', () => {
    expect(isRichEmpty('<p>x</p>')).toBe(false)
  })
})

describe('toRichHtml', () => {
  it('giữ nguyên chuỗi đã là HTML', () => {
    expect(toRichHtml('<p>đã có thẻ</p>')).toBe('<p>đã có thẻ</p>')
  })

  it('bọc từng dòng của chữ trơn cũ vào <p> để không mất chỗ xuống dòng', () => {
    expect(toRichHtml('dòng 1\ndòng 2')).toBe('<p>dòng 1</p><p>dòng 2</p>')
  })

  it('thoát ký tự để mô tả kiểu "a < b" không biến thành thẻ', () => {
    expect(toRichHtml('a < b & c')).toBe('<p>a &lt; b &amp; c</p>')
  })

  it('rỗng vào thì rỗng ra, không đẻ ra <p></p> thừa', () => {
    expect(toRichHtml('')).toBe('')
  })
})
