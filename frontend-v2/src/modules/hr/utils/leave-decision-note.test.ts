import { describe, expect, it } from 'vitest'

import { BAD_LEAVE_OUTCOMES, decisionNoteOf, isBadLeaveOutcome } from './leave-decision-note'
import { LEAVE_STATUS } from '../types/leave'

/**
 * Lý do KHÔNG-DUYỆT in trên một dòng của bảng danh sách.
 *
 * Ô này nhận chữ người dùng gõ tự do, dài tới 500 ký tự, và nằm trong một ô bảng
 * có bề rộng cố định — tức là đúng chỗ dễ vỡ bố cục nhất màn hình. Nhóm bài dưới
 * cố tình ném vào những chuỗi tệ nhất có thể gõ được.
 */

const rejected = (note?: string | null) => ({ status: LEAVE_STATUS.REJECTED, decision_note: note })

describe('isBadLeaveOutcome', () => {
  it('đúng ba kết cục không-duyệt, không hơn không kém', () => {
    expect(BAD_LEAVE_OUTCOMES.slice().sort()).toEqual(
      [LEAVE_STATUS.REJECTED, LEAVE_STATUS.RETURNED, LEAVE_STATUS.CANCELLED].sort(),
    )
  })

  it('nháp · chờ duyệt · ĐÃ DUYỆT đều không phải kết cục xấu', () => {
    //  Đã duyệt lọt vào đây là ghi chú của người duyệt bị tô đỏ, người đọc hiểu
    //  ngược thành đơn bị từ chối.
    expect(isBadLeaveOutcome(LEAVE_STATUS.DRAFT)).toBe(false)
    expect(isBadLeaveOutcome(LEAVE_STATUS.PENDING)).toBe(false)
    expect(isBadLeaveOutcome(LEAVE_STATUS.APPROVED)).toBe(false)
  })

  it('trạng thái lạ (0, số âm, số ngoài dải) thì coi như không phải kết cục xấu', () => {
    expect(isBadLeaveOutcome(0)).toBe(false)
    expect(isBadLeaveOutcome(-1)).toBe(false)
    expect(isBadLeaveOutcome(99)).toBe(false)
  })
})

describe('decisionNoteOf', () => {
  it('im lặng với đơn ĐÃ DUYỆT dù có ghi chú', () => {
    expect(
      decisionNoteOf({ status: LEAVE_STATUS.APPROVED, decision_note: 'nhớ bàn giao trước khi đi' }),
    ).toBe('')
  })

  it('in lý do cho cả ba kết cục xấu', () => {
    for (const status of BAD_LEAVE_OUTCOMES) {
      expect(decisionNoteOf({ status, decision_note: 'đổi ý' })).toBe('đổi ý')
    }
  })

  it('thiếu hẳn khóa, `null`, chuỗi rỗng đều ra chuỗi rỗng — không ra "null"', () => {
    expect(decisionNoteOf({ status: LEAVE_STATUS.CANCELLED })).toBe('')
    expect(decisionNoteOf(rejected(null))).toBe('')
    expect(decisionNoteOf(rejected(''))).toBe('')
  })

  it('chuỗi TOÀN khoảng trắng coi như không ghi lý do', () => {
    //  Không dọn thì ô hiện một vệt đỏ trống rỗng cạnh huy hiệu.
    expect(decisionNoteOf(rejected('   '))).toBe('')
    expect(decisionNoteOf(rejected('\n\t  \n'))).toBe('')
  })

  it('gộp xuống dòng và tab thành MỘT dấu cách — ô một dòng không có chỗ cho `\\n`', () => {
    expect(decisionNoteOf(rejected('trùng lịch\nvới chuyến công tác'))).toBe(
      'trùng lịch với chuyến công tác',
    )
    expect(decisionNoteOf(rejected('a\r\n\r\n\t\tb'))).toBe('a b')
  })

  it('gộp cả cụm khoảng trắng dài giữa hai chữ', () => {
    //  Dán từ Word ra hay gặp. Để nguyên thì hai chữ cách nhau nửa ô bảng.
    expect(decisionNoteOf(rejected('nghỉ            quá nhiều'))).toBe('nghỉ quá nhiều')
  })

  it('KHÔNG cắt bớt lý do dài — cắt là mất chữ, việc thu gọn để CSS lo', () => {
    const long = 'x'.repeat(500)
    expect(decisionNoteOf(rejected(long))).toBe(long)
    expect(decisionNoteOf(rejected(long)).length).toBe(500)
  })

  it('một từ dài liền mạch không dấu cách vẫn giữ nguyên', () => {
    //  Đây là chuỗi phá bố cục kinh điển: không có chỗ nào để xuống dòng. Hàm
    //  giữ nguyên, ô bảng phải tự chịu bằng `truncate` + `min-w-0`.
    const wall = 'a'.repeat(300)
    expect(decisionNoteOf(rejected(wall))).toBe(wall)
  })

  it('giữ nguyên dấu tiếng Việt và ký tự lạ, không chuẩn hóa gì thêm', () => {
    expect(decisionNoteOf(rejected('Nghỉ trùng đợt kiểm kê — «Q4/2026»'))).toBe(
      'Nghỉ trùng đợt kiểm kê — «Q4/2026»',
    )
  })

  it('lý do vỏn vẹn một ký tự vẫn hiện, không bị coi là rỗng', () => {
    expect(decisionNoteOf(rejected('x'))).toBe('x')
  })
})
