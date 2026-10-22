import { describe, expect, it } from 'vitest'

import { DATE_RANGE_PRESETS, resolveNextDays, resolveThisMonth } from './date-range-presets'

describe('resolveThisMonth', () => {
  it('covers the whole month, including a 31st', () => {
    expect(resolveThisMonth(new Date(2026, 9, 22))).toEqual(['2026-10-01', '2026-10-31'])
  })

  it('ends February on the 28th in a common year and the 29th in a leap year', () => {
    expect(resolveThisMonth(new Date(2026, 1, 3))).toEqual(['2026-02-01', '2026-02-28'])
    expect(resolveThisMonth(new Date(2028, 1, 3))).toEqual(['2028-02-01', '2028-02-29'])
  })

  it('does not slip into the previous month on the 1st just after midnight', () => {
    //  Lỗi kinh điển khi đổi sang UTC: 00:30 ngày 01/11 giờ Việt Nam là 17:30 ngày 31/10 UTC.
    expect(resolveThisMonth(new Date(2026, 10, 1, 0, 30))).toEqual(['2026-11-01', '2026-11-30'])
  })
})

describe('resolveNextDays', () => {
  it('counts today as the first of the seven days', () => {
    expect(resolveNextDays(7, new Date(2026, 9, 22))).toEqual(['2026-10-22', '2026-10-28'])
  })

  it('rolls over the end of the year', () => {
    expect(resolveNextDays(7, new Date(2026, 11, 29))).toEqual(['2026-12-29', '2027-01-04'])
  })

  it('one day is just today', () => {
    expect(resolveNextDays(1, new Date(2026, 9, 22))).toEqual(['2026-10-22', '2026-10-22'])
  })
})

/** Lấy preset theo nhãn — tên nhãn đổi thì test đỏ ngay, đúng ý. */
function preset(label: string) {
  const found = DATE_RANGE_PRESETS.find((item) => item.label === label)
  if (!found) throw new Error(`Không có mức chọn nhanh "${label}"`)
  return found
}

/** 15/03/2026 — giữa tháng, giữa quý I, không dính đầu/cuối gì cả. */
const GIUA_THANG_BA = new Date(2026, 2, 15)

describe('DATE_RANGE_PRESETS', () => {
  it('Hôm nay = đúng một ngày, hai đầu bằng nhau', () => {
    expect(preset('Hôm nay').resolve(GIUA_THANG_BA)).toEqual(['2026-03-15', '2026-03-15'])
  })

  it('7 ngày qua tính CẢ hôm nay — 7 ngày chứ không phải 8', () => {
    //  Lùi 7 ngày tròn là ra khoảng 8 ngày. Lỗi lệch-một kinh điển, và người
    //  dùng chỉ phát hiện khi đối chiếu số liệu với báo cáo khác.
    expect(preset('7 ngày qua').resolve(GIUA_THANG_BA)).toEqual(['2026-03-09', '2026-03-15'])
  })

  it('30 ngày qua cũng tính cả hôm nay', () => {
    expect(preset('30 ngày qua').resolve(GIUA_THANG_BA)).toEqual(['2026-02-14', '2026-03-15'])
  })

  it('7 ngày qua bắc được qua đầu tháng và đầu năm', () => {
    expect(preset('7 ngày qua').resolve(new Date(2026, 0, 3))).toEqual([
      '2025-12-28',
      '2026-01-03',
    ])
  })

  it('Tháng này ra đúng ngày cuối của tháng 31 / 30 / 28 / 29 ngày', () => {
    const thisMonth = preset('Tháng này')
    expect(thisMonth.resolve(new Date(2026, 0, 20))).toEqual(['2026-01-01', '2026-01-31'])
    expect(thisMonth.resolve(new Date(2026, 3, 20))).toEqual(['2026-04-01', '2026-04-30'])
    expect(thisMonth.resolve(new Date(2026, 1, 20))).toEqual(['2026-02-01', '2026-02-28'])
    //  2028 nhuận — bảng cứng 28 ngày sẽ hụt mất ngày 29.
    expect(thisMonth.resolve(new Date(2028, 1, 20))).toEqual(['2028-02-01', '2028-02-29'])
  })

  it('Quý này ra đủ bốn quý, không lẫn sang quý bên cạnh', () => {
    const quy = preset('Quý này')
    expect(quy.resolve(new Date(2026, 0, 1))).toEqual(['2026-01-01', '2026-03-31'])
    expect(quy.resolve(new Date(2026, 4, 9))).toEqual(['2026-04-01', '2026-06-30'])
    expect(quy.resolve(new Date(2026, 8, 30))).toEqual(['2026-07-01', '2026-09-30'])
    expect(quy.resolve(new Date(2026, 11, 31))).toEqual(['2026-10-01', '2026-12-31'])
  })

  it('Năm nay trọn 01/01 → 31/12', () => {
    expect(preset('Năm nay').resolve(GIUA_THANG_BA)).toEqual(['2026-01-01', '2026-12-31'])
  })

  it('mọi mức đều trả yyyy-mm-dd và từ <= đến', () => {
    for (const item of DATE_RANGE_PRESETS) {
      const [from, to] = item.resolve(GIUA_THANG_BA)
      expect(from, item.label).toMatch(/^\d{4}-\d{2}-\d{2}$/)
      expect(to, item.label).toMatch(/^\d{4}-\d{2}-\d{2}$/)
      //  `yyyy-mm-dd` sắp theo bảng chữ cái trùng thứ tự thời gian nên so chuỗi là đủ.
      expect(from <= to, `${item.label}: từ phải <= đến`).toBe(true)
    }
  })

  it('không truyền ngày thì lấy hôm nay, KHÔNG phải lúc nạp mô-đun', () => {
    //  Trang danh sách hay mở từ tối hôm trước sang sáng hôm sau. Nếu `resolve`
    //  là hai chuỗi cố định tính lúc import thì sáng ra "Hôm nay" vẫn trỏ vào
    //  ngày hôm qua.
    const [from, to] = preset('Hôm nay').resolve()
    const now = new Date()
    const homNay = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(
      now.getDate(),
    ).padStart(2, '0')}`
    expect(from).toBe(homNay)
    expect(to).toBe(homNay)
  })

  it('KHÔNG có mục "Tất cả" — xóa khoảng đã có nút ✕ trên chính ô chọn', () => {
    expect(DATE_RANGE_PRESETS.map((item) => item.label)).not.toContain('Tất cả')
  })
})
