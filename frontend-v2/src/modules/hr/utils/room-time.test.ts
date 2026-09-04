import { describe, expect, it } from 'vitest'

import {
  defaultSlot,
  formatTimeRange,
  fromApiTime,
  minutesBetween,
  toApiTime,
  toLocalInput,
} from './room-time'

/** Múi giờ khi chạy test cố định `Asia/Ho_Chi_Minh` (xem `vitest.config.ts`). */

describe('toLocalInput', () => {
  it('giữ đúng GIỜ ĐỊA PHƯƠNG, không lùi 7 tiếng như `toISOString`', () => {
    //  LỖI KINH ĐIỂN: máy ở UTC+7 mà dùng `toISOString()` thì 9:00 sáng gửi lên
    //  thành 2:00 sáng, và cuộc họp đầu giờ nhảy sang hôm trước.
    expect(toLocalInput(new Date(2026, 8, 10, 9, 0))).toBe('2026-09-10T09:00')
  })

  it('đệm số 0 cho tháng, ngày, giờ, phút một chữ số', () => {
    expect(toLocalInput(new Date(2026, 0, 5, 7, 5))).toBe('2026-01-05T07:05')
  })

  it('nửa đêm KHÔNG rơi sang ngày hôm trước', () => {
    expect(toLocalInput(new Date(2026, 8, 10, 0, 0))).toBe('2026-09-10T00:00')
  })
})

describe('toApiTime / fromApiTime', () => {
  it('thêm giây khi gửi lên, cắt giây khi nhận về', () => {
    expect(toApiTime('2026-09-10T09:00')).toBe('2026-09-10T09:00:00')
    expect(fromApiTime('2026-09-10T09:00:00')).toBe('2026-09-10T09:00')
  })

  it('chuỗi đã có giây thì giữ nguyên, không thêm lần hai', () => {
    expect(toApiTime('2026-09-10T09:00:30')).toBe('2026-09-10T09:00:30')
  })

  it('rỗng / null vẫn ra chuỗi rỗng, không ra "undefined"', () => {
    expect(toApiTime('')).toBe('')
    expect(fromApiTime(null)).toBe('')
    expect(fromApiTime(undefined)).toBe('')
  })
})

describe('formatTimeRange', () => {
  it('cùng ngày thì chỉ hiện hai đầu giờ', () => {
    expect(formatTimeRange('2026-09-10T09:00:00', '2026-09-10T10:30:00')).toBe('09:00 – 10:30')
  })

  it('VẮT sang ngày khác thì phải nói ra ngày', () => {
    //  "23:00 – 01:00" đọc như một cuộc họp đi ngược thời gian.
    expect(formatTimeRange('2026-09-10T23:00:00', '2026-09-11T01:00:00')).toBe(
      '23:00 10/09 – 01:00 11/09',
    )
  })
})

describe('minutesBetween', () => {
  it('đếm đúng số phút', () => {
    expect(minutesBetween('2026-09-10T09:00:00', '2026-09-10T10:30:00')).toBe(90)
  })

  it('khoảng ÂM trả 0 — chiều cao khối trên lịch không được âm', () => {
    expect(minutesBetween('2026-09-10T10:00:00', '2026-09-10T09:00:00')).toBe(0)
  })
})

describe('defaultSlot', () => {
  it('nhảy tới GIỜ TRÒN kế tiếp, dài một tiếng', () => {
    //  Không ai đặt phòng cho 14:37; để người dùng phải sửa hai ô ngay khi mở
    //  form là bắt họ làm việc của máy.
    expect(defaultSlot(new Date(2026, 8, 10, 14, 37))).toEqual({
      start: '2026-09-10T15:00',
      end: '2026-09-10T16:00',
    })
  })

  it('gần nửa đêm thì trôi sang ngày hôm sau chứ không quay về 0h hôm nay', () => {
    expect(defaultSlot(new Date(2026, 8, 10, 23, 10))).toEqual({
      start: '2026-09-11T00:00',
      end: '2026-09-11T01:00',
    })
  })

  it('đúng giờ tròn thì vẫn nhảy sang giờ kế — quá khứ một phút cũng là quá khứ', () => {
    expect(defaultSlot(new Date(2026, 8, 10, 9, 0)).start).toBe('2026-09-10T10:00')
  })
})
