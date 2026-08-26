import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  DATE_RANGES,
  toDashboardParams,
  type DateRangeKey,
} from './dashboard-date-range'

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

describe('khoảng ngày TỰ CHỌN', () => {
  it('mức «custom» lấy hai đầu người dùng chấm trên lịch', () => {
    //  Hai đầu KHÔNG suy được từ `rangeKey` như mấy mức bày sẵn — chúng nằm ở
    //  state của trang và truyền vào qua tham số cuối.
    expect(
      toDashboardParams(undefined, undefined, 'custom', {
        from: '2026-09-11',
        to: '2026-09-14',
      }),
    ).toMatchObject({ from_date: '2026-09-11', to_date: '2026-09-14' })
  })

  it('mức bày sẵn thì BỎ QUA khoảng tự chọn còn sót lại', () => {
    //  Người dùng chấm một khoảng rồi đổi về «Hôm nay»: khoảng cũ vẫn nằm trong
    //  state, ăn nhầm nó là trang hiện số liệu của kỳ họ vừa bỏ.
    const out = toDashboardParams(undefined, undefined, 'today', {
      from: '2020-01-01',
      to: '2020-12-31',
    })
    expect(out.from_date).not.toBe('2020-01-01')
  })

  it('chọn «custom» mà chưa chấm ngày nào thì không gửi tham số rỗng lên backend', () => {
    //  `from_date=` là một tham số CÓ MẶT nhưng vô nghĩa — backend sẽ đem so với
    //  chuỗi rỗng thay vì bỏ qua.
    const out = toDashboardParams(undefined, undefined, 'custom', { from: '', to: '' })
    expect(out.from_date).toBeUndefined()
    expect(out.to_date).toBeUndefined()
  })
})
