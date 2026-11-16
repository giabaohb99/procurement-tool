import { describe, expect, it } from 'vitest'

import { bulkLimitMessage } from './work-shift-bulk-limits'
import {
  describeShiftRejections,
  formatCopyWeekResult,
  formatVnDate,
  MAX_REJECTION_LINES,
  readShiftRejections,
  toShiftErrorView,
} from './work-shift-errors'

/** Lỗi axios giả với phong bì lỗi của backend. */
function axiosError(status: number, error: Record<string, unknown>) {
  return { message: `Request failed with status code ${status}`, response: { status, data: { success: false, error } } }
}

const names: Record<number, string> = { 7: 'Nguyễn An', 8: 'Trần Bình' }
const nameOf = (id: number) => names[id]

describe('readShiftRejections', () => {
  it('reads the rejected cells of a shift_rejected envelope', () => {
    const err = axiosError(422, {
      code: 'shift_rejected',
      message: 'Không xếp được 2 ô (Chỉ xếp ca từ hôm nay trở đi); chưa ghi ô nào',
      details: {
        rejected: [
          { employee_id: 7, work_date: '2026-11-14', code: 'past_date', message: 'Chỉ xếp ca từ hôm nay trở đi' },
          { employee_id: 8, work_date: null, code: 'not_found', message: 'Nhân sự được xếp ca không tồn tại hoặc ngoài phạm vi của bạn' },
        ],
      },
    })
    expect(readShiftRejections(err)).toEqual([
      { employee_id: 7, work_date: '2026-11-14', code: 'past_date', message: 'Chỉ xếp ca từ hôm nay trở đi' },
      { employee_id: 8, work_date: null, code: 'not_found', message: 'Nhân sự được xếp ca không tồn tại hoặc ngoài phạm vi của bạn' },
    ])
  })

  it('returns null for any other error — 409, plain 422, network', () => {
    expect(readShiftRejections(axiosError(409, { code: 'conflict', message: 'x' }))).toBeNull()
    expect(readShiftRejections(axiosError(422, { message: 'Mỗi ngày tối đa 12 khung giờ' }))).toBeNull()
    expect(readShiftRejections(new Error('Network Error'))).toBeNull()
    expect(readShiftRejections(null)).toBeNull()
    expect(readShiftRejections('boom')).toBeNull()
  })

  it('survives a malformed details block without throwing', () => {
    expect(readShiftRejections(axiosError(403, { code: 'shift_rejected', details: null }))).toEqual([])
    expect(readShiftRejections(axiosError(403, { code: 'shift_rejected', details: { rejected: 'x' } }))).toEqual([])
    const junk = axiosError(403, { code: 'shift_rejected', details: { rejected: [null, 5, { employee_id: '7' }, { employee_id: 7, code: 'self' }] } })
    //  Dòng hỏng bị bỏ; dòng thiếu message có câu mặc định, thiếu ngày thì là cấp nhân sự.
    expect(readShiftRejections(junk)).toEqual([{ employee_id: 7, work_date: null, code: 'self', message: 'Không xếp được ô này' }])
  })
})

describe('describeShiftRejections', () => {
  it('names the person and the date, and falls back to the id for someone not on the page', () => {
    const lines = describeShiftRejections(
      [
        { employee_id: 7, work_date: '2026-11-14', code: 'past_date', message: 'Chỉ xếp ca từ hôm nay trở đi' },
        { employee_id: 99, work_date: null, code: 'self', message: 'Bạn không được tự xếp ca cho chính mình' },
      ],
      nameOf,
    )
    expect(lines).toEqual([
      'Nguyễn An · 14/11/2026: Chỉ xếp ca từ hôm nay trở đi',
      'Nhân sự #99: Bạn không được tự xếp ca cho chính mình',
    ])
  })

  it('caps a 500-cell rejection to a readable list plus a remainder line', () => {
    const many = Array.from({ length: 500 }, (_, i) => ({ employee_id: 7, work_date: '2026-11-14', code: 'past_date', message: `m${i}` }))
    const lines = describeShiftRejections(many, nameOf)
    expect(lines).toHaveLength(MAX_REJECTION_LINES + 1)
    expect(lines.at(-1)).toBe(`và ${500 - MAX_REJECTION_LINES} ô khác`)
  })
})

describe('toShiftErrorView', () => {
  it('rejections → headline with the count + one line per cell', () => {
    const err = axiosError(422, {
      code: 'shift_rejected',
      message: 'gộp',
      details: { rejected: [{ employee_id: 8, work_date: '2026-11-15', code: 'past_date', message: 'Chỉ xếp ca từ hôm nay trở đi' }] },
    })
    expect(toShiftErrorView(err, nameOf)).toEqual({
      message: 'Không ô nào được lưu — 1 ô bị từ chối:',
      lines: ['Trần Bình · 15/11/2026: Chỉ xếp ca từ hôm nay trở đi'],
    })
  })

  it('other errors keep the backend sentence and no list', () => {
    const err = axiosError(409, { message: 'Ca của ngày này vừa được người khác xếp, hãy tải lại rồi xếp lại' })
    expect(toShiftErrorView(err, nameOf)).toEqual({
      message: 'Ca của ngày này vừa được người khác xếp, hãy tải lại rồi xếp lại',
      lines: [],
    })
  })
})

describe('formatVnDate', () => {
  it('formats ISO dates and leaves garbage untouched', () => {
    expect(formatVnDate('2026-11-07')).toBe('07/11/2026')
    expect(formatVnDate('')).toBe('')
    expect(formatVnDate('2026-11-07T10:00')).toBe('2026-11-07T10:00')
  })
})

describe('formatCopyWeekResult', () => {
  it('reports every counter that is not zero, past days included', () => {
    expect(formatCopyWeekResult({ created: 3, updated: 1, changed: 4, skipped: 2, skipped_past: 2 })).toBe(
      'Đã chép ca: thêm 3 ngày, ghi đè 1 ngày, giữ nguyên 2 ngày đã có ca, bỏ qua 2 ngày đã qua.',
    )
  })

  it('says plainly when last week had no shift to copy', () => {
    expect(formatCopyWeekResult({ created: 0, updated: 0, changed: 0, skipped: 0, skipped_past: 0 })).toBe(
      'Tuần trước không có ca xếp riêng nào để chép.',
    )
  })

  //  Lỗi đã bắt (rà soát 16/11): bản đầu đọc `skipped_leave_items`, backend trả `leave_conflicts` → danh sách luôn rỗng.
  it('names the days skipped because of a leave request (leave_conflicts), capped to three', () => {
    const result = {
      created: 2,
      updated: 0,
      changed: 2,
      skipped: 0,
      skipped_past: 0,
      skipped_leave: 4,
      leave_conflicts: [
        { employee_id: 7, work_date: '2026-11-24', request_code: 'NP012' },
        { employee_id: 8, work_date: '2026-11-25', request_code: 'NP013' },
        { employee_id: 99, work_date: '2026-11-26', request_code: '' },
        { employee_id: 7, work_date: '2026-11-27', request_code: '' },
      ],
    }
    expect(formatCopyWeekResult(result, nameOf)).toBe(
      'Đã chép ca: thêm 2 ngày, bỏ qua 4 ngày đã có đơn nghỉ: Nguyễn An 24/11 (NP012), Trần Bình 25/11 (NP013), Nhân sự #99 26/11 (đơn nghỉ) và 1 ngày khác.',
    )
  })

  it('an older backend without skipped_leave still reads fine; a count without items gives no list', () => {
    expect(formatCopyWeekResult({ created: 1, updated: 0, changed: 1, skipped: 0, skipped_past: 0 })).toBe('Đã chép ca: thêm 1 ngày.')
    expect(formatCopyWeekResult({ created: 0, updated: 0, changed: 0, skipped: 0, skipped_past: 0, skipped_leave: 2 })).toBe(
      'Không có ngày nào được chép: bỏ qua 2 ngày đã có đơn nghỉ.',
    )
  })

  it('nothing changed but cells were skipped → not "Đã chép ca"', () => {
    expect(formatCopyWeekResult({ created: 0, updated: 0, changed: 0, skipped: 0, skipped_past: 5 })).toBe(
      'Không có ngày nào được chép: bỏ qua 5 ngày đã qua.',
    )
  })
})

describe('bulkLimitMessage', () => {
  it('blocks above the backend caps (50 people, 42 days, 500 cells) and allows exactly the cap', () => {
    expect(bulkLimitMessage(50, 10)).toBeNull()
    expect(bulkLimitMessage(51, 1)).toBe('Mỗi lượt tối đa 50 người.')
    expect(bulkLimitMessage(1, 43)).toBe('Mỗi lượt tối đa 42 ngày.')
    expect(bulkLimitMessage(12, 42)).toBe('Mỗi lượt tối đa 500 ô (người × ngày).')
    expect(bulkLimitMessage(25, 20)).toBeNull()
  })
})
