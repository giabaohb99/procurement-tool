import { describe, expect, it } from 'vitest'

import { isBlankRichBody, stripRichBodyText } from './rich-body'

describe('stripRichBodyText', () => {
  it('drops tags but keeps the visible text in reading order', () => {
    expect(stripRichBodyText('<p>xin <strong>chào</strong></p><ol><li>một</li></ol>')).toBe(
      'xin chào một',
    )
  })

  it('treats &nbsp; as whitespace, not as content', () => {
    // trình soạn thảo chèn &nbsp; vào đoạn trống — coi là chữ thì bài rỗng
    // vượt được nút Đăng rồi bị backend 400, hai tầng cãi nhau
    expect(stripRichBodyText('<p>&nbsp;</p><p> &nbsp; </p>')).toBe('')
  })

  it('survives empty and tag-free input', () => {
    expect(stripRichBodyText('')).toBe('')
    expect(stripRichBodyText('chữ trơn')).toBe('chữ trơn')
  })
})

describe('isBlankRichBody', () => {
  it('flags editor-empty markup as blank but real text as not', () => {
    expect(isBlankRichBody('<p></p>')).toBe(true)
    expect(isBlankRichBody('<p><strong></strong></p>')).toBe(true)
    expect(isBlankRichBody('<p>a</p>')).toBe(false)
  })
})
