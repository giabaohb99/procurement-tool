import { describe, expect, it } from 'vitest'

import { bodyToEditableText, editableTextToBody } from './comment-edit-text'

const mentions = [
  { user_id: 12, name: 'Lan' },
  { user_id: 13, name: 'Lan Anh' },
]

describe('comment-edit-text', () => {
  it('đổi thẻ nhắc tên thành @Tên để sửa', () => {
    expect(bodyToEditableText('Chào @[12] và @[13]', mentions)).toBe('Chào @Lan và @Lan Anh')
  })

  it('giữ nguyên thẻ không tra ra tên', () => {
    expect(bodyToEditableText('Xem @[99]', mentions)).toBe('Xem @[99]')
  })

  it('đổi ngược @Tên thành thẻ, tên dài khớp trước', () => {
    expect(editableTextToBody('Chào @Lan và @Lan Anh', mentions)).toBe('Chào @[12] và @[13]')
  })

  it('khứ hồi không đổi nội dung', () => {
    const body = 'Nhờ @[13] kiểm lại giúp'
    expect(editableTextToBody(bodyToEditableText(body, mentions), mentions)).toBe(body)
  })

  it('cắt khoảng trắng thừa hai đầu', () => {
    expect(editableTextToBody('  xin chào  ', [])).toBe('xin chào')
  })
})
