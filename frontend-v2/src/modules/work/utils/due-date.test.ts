import { describe, expect, it } from 'vitest'

import { addDays, dueTone, formatDueLabel, today } from './due-date'

/**
 * Hạn chót lưu dạng chuỗi `"YYYY-MM-DD"` và được so bằng CHUỖI.
 *
 * Bài học đứng sau bộ test này: dựng `new Date("2026-08-28")` ra mốc UTC, ở múi
 * giờ +07 nó lùi về hôm trước — hạn hôm nay bỗng bị tô đỏ "quá hạn". Vitest ghim
 * múi giờ `Asia/Ho_Chi_Minh` nên `today()` ở đây đúng là ngày người dùng thấy.
 */

describe('dueTone', () => {
  it('hạn ĐÚNG hôm nay không được tính là quá hạn', () => {
    expect(dueTone(today())).toBe('today')
  })

  it('hôm qua là quá hạn, ngày mai là bình thường', () => {
    expect(dueTone(addDays(-1))).toBe('overdue')
    expect(dueTone(addDays(1))).toBe('normal')
  })

  it('việc ĐÃ XONG thì quá hạn cũng thôi tô đỏ', () => {
    //  Tô đỏ việc đã hoàn thành là dọa người dùng bằng một việc không còn nữa.
    expect(dueTone(addDays(-30), true)).toBe('normal')
  })

  it('chưa đặt hạn thì không có sắc thái nào', () => {
    expect(dueTone('')).toBe('none')
  })
})

describe('formatDueLabel', () => {
  it('cùng năm thì bỏ năm cho thẻ đỡ chật', () => {
    const nam = today().slice(0, 4)
    expect(formatDueLabel(`${nam}-09-05`)).toBe('05/09')
  })

  it('khác năm thì phải hiện năm, không thì 05/09 của hai năm nhìn y hệt nhau', () => {
    expect(formatDueLabel('2019-09-05')).toBe('05/09/2019')
  })

  it('chuỗi rỗng hoặc dữ liệu rác trả về rỗng chứ không vẽ "NaN/NaN"', () => {
    expect(formatDueLabel('')).toBe('')
    expect(formatDueLabel('hôm qua')).toBe('')
  })
})

describe('addDays', () => {
  it('luôn ra chuỗi 10 ký tự có đệm số 0', () => {
    expect(addDays(0)).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    expect(addDays(45)).toMatch(/^\d{4}-\d{2}-\d{2}$/)
    expect(addDays(-400)).toMatch(/^\d{4}-\d{2}-\d{2}$/)
  })

  it('cộng 0 ngày chính là hôm nay', () => {
    expect(addDays(0)).toBe(today())
  })
})
