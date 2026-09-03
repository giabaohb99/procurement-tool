import { describe, expect, it } from 'vitest'

import { parseCommentBody } from './parse-comment-body'

/**
 * Tách thẻ nhắc tên trong nội dung bình luận.
 *
 * Chỗ hỏng ÂM THẦM: sai một nhịp con trỏ là nuốt mất chữ quanh thẻ, mà nhìn
 * lướt vẫn thấy "có nội dung" nên chẳng ai báo. Backend lưu `@[12]` chứ không
 * lưu tên, nên hàm này chạy trên MỌI bình luận có nhắc tên.
 */

const NGUOI = [
  { user_id: 12, name: 'Trần Minh Được' },
  { user_id: 34, name: 'Mộc' },
]

/** Ghép lại thành chữ để so cho gọn: `@[12]` → `@Tên`. */
const noiLai = (body: string, mentions = NGUOI) =>
  parseCommentBody(body, mentions)
    .map((s) => (s.kind === 'text' ? s.text : `@${s.name}`))
    .join('')

describe('parseCommentBody', () => {
  it('giữ NGUYÊN chữ hai bên thẻ, không nuốt ký tự nào', () => {
    expect(noiLai('nhờ @[12] xem hộ nhé')).toBe('nhờ @Trần Minh Được xem hộ nhé')
  })

  it('tách đúng nhiều thẻ trong một câu', () => {
    expect(noiLai('@[12] và @[34] họp lúc 3h')).toBe('@Trần Minh Được và @Mộc họp lúc 3h')
  })

  it('hai thẻ DÍNH LIỀN nhau không làm mất thẻ nào', () => {
    expect(noiLai('@[12]@[34]')).toBe('@Trần Minh Được@Mộc')
  })

  it('gọi hai lần liên tiếp vẫn ra kết quả như nhau', () => {
    //  Biểu thức chính quy khai ở tầng module và có cờ `g`: dùng `exec` trong
    //  vòng `while` thì hai lần gọi ăn chung `lastIndex`, bình luận thứ hai mất
    //  thẻ đầu tiên. Bài này ghim đúng cái bẫy đó.
    const cau = 'nhờ @[12] xem'
    expect(noiLai(cau)).toBe(noiLai(cau))
  })

  it('thẻ trỏ người KHÔNG tra ra tên vẫn hiện chip, không biến mất', () => {
    //  Người bị xóa tài khoản. Bỏ thẻ đi là câu mất chủ ngữ: "@ xem hộ mình".
    expect(noiLai('@[99] xem hộ')).toBe('@không rõ xem hộ')
  })

  it('không có thẻ nào thì trả đúng một mẩu chữ', () => {
    const segs = parseCommentBody('bình luận thường', NGUOI)
    expect(segs).toEqual([{ kind: 'text', text: 'bình luận thường' }])
  })

  it('nội dung RỖNG trả mảng rỗng, không phải một mẩu chữ rỗng', () => {
    //  Bình luận chỉ có tệp thì `body` rỗng — vẽ một `<span>` trống là thừa.
    expect(parseCommentBody('', NGUOI)).toEqual([])
  })

  it('thẻ đứng ĐẦU và đứng CUỐI đều không sinh mẩu chữ rỗng', () => {
    expect(parseCommentBody('@[34] ơi', NGUOI)).toHaveLength(2)
    expect(parseCommentBody('gửi @[34]', NGUOI)).toHaveLength(2)
  })

  it('chuỗi trông GIỐNG thẻ nhưng sai dạng thì để nguyên là chữ', () => {
    //  Người dùng gõ tay `@[abc]` hay `@[]` — không phải thẻ, đừng nuốt.
    for (const cau of ['@[abc] xem', '@[] xem', '@12 xem']) {
      expect(noiLai(cau)).toBe(cau)
    }
  })

  it('xuống dòng và khoảng trắng quanh thẻ được giữ y nguyên', () => {
    expect(noiLai('dòng một\n@[34]  hai dấu cách')).toBe('dòng một\n@Mộc  hai dấu cách')
  })

  it('bộ người được nhắc RỖNG thì mọi thẻ về «không rõ», không nổ', () => {
    expect(noiLai('@[12] ơi', [])).toBe('@không rõ ơi')
  })

  it('chịu được nội dung dài với rất nhiều thẻ', () => {
    const cau = Array.from({ length: 200 }, () => '@[34]').join(' ')
    const segs = parseCommentBody(cau, NGUOI)
    expect(segs.filter((s) => s.kind === 'mention')).toHaveLength(200)
  })
})
