import { afterEach, describe, expect, it, vi } from 'vitest'

import { DATE_RANGES, type DateRangeKey } from './dashboard-date-range'

function giai(key: DateRangeKey) {
  const range = DATE_RANGES.find((item) => item.key === key)
  if (!range) throw new Error(`Không có mức "${key}"`)
  return range.resolve()
}

afterEach(() => {
  vi.useRealTimers()
})

describe('DATE_RANGES', () => {
  it('"Hôm nay" trả về đúng ngày địa phương, không lệch sang ngày UTC', () => {
    //  Giờ chạy test cố định Asia/Ho_Chi_Minh (UTC+7). 23:30 ngày 18/08 giờ VN
    //  là 16:30 ngày 18/08 UTC — nhưng 07:00 giờ VN thì `toISOString()` đã lùi
    //  về ngày hôm trước. Đó là lý do không dùng `toISOString()`.
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-08-18T00:30:00+07:00'))

    expect(giai('today')).toEqual({ from: '2026-08-18', to: '2026-08-18' })
  })

  it('"7 ngày qua" tính đủ 7 ngày kể cả hôm nay', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-08-18T10:00:00+07:00'))

    //  Từ 12 tới 18 là 7 ngày. Lùi 7 ngày thay vì 6 sẽ thành 8 ngày.
    expect(giai('week')).toEqual({ from: '2026-08-12', to: '2026-08-18' })
  })

  it('"Năm nay" bắt đầu từ 1/1, không phải 12 tháng gần nhất', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-08-18T10:00:00+07:00'))

    expect(giai('year')).toEqual({ from: '2026-01-01', to: '2026-08-18' })
  })

  it('"Tất cả" không chặn đầu nào', () => {
    expect(giai('all')).toEqual({})
  })

  it('lùi qua mốc đầu tháng vẫn ra đúng tháng trước', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-03-02T10:00:00+07:00'))

    //  2026 không nhuận: lùi 6 ngày từ 02/03 phải ra 24/02, không phải 26/02.
    expect(giai('week').from).toBe('2026-02-24')
  })
})
