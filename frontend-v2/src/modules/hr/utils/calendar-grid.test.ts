import { describe, expect, it } from 'vitest'

import {
  addDays,
  buildMonthGrid,
  buildWeekDays,
  holidayNamesOn,
  isWeekend,
  MONTH_GRID_WEEKS,
  rangeLabel,
  rangeOf,
  shiftAnchor,
  startOfMonth,
  startOfWeek,
  toISODate,
} from './calendar-grid'
import type { Holiday } from '../types/leave'

/**
 * Lưới lịch nghỉ.
 *
 * Múi giờ khi chạy test cố định `Asia/Ho_Chi_Minh` (`vitest.config.ts`) — đúng
 * múi giờ làm lộ ra lỗi `toISOString()`, nên đừng đổi nó đi.
 */
function holiday(overrides: Partial<Holiday> = {}): Holiday {
  return {
    id: 1,
    company_id: 0,
    date: '2026-01-01',
    name: 'Tết Dương lịch',
    is_recurring: true,
    is_active: true,
    ...overrides,
  }
}

describe('toISODate', () => {
  it('cắt theo giờ ĐỊA PHƯƠNG, không lệch một ngày như `toISOString()`', () => {
    //  Lỗi kinh điển: `new Date(2026, 8, 1).toISOString()` ra "2026-08-31T17:00Z"
    //  ở múi +7, và cả cái lịch lùi một ngày.
    expect(toISODate(new Date(2026, 8, 1))).toBe('2026-09-01')
  })

  it('đệm 0 cho tháng và ngày một chữ số', () => {
    expect(toISODate(new Date(2026, 0, 5))).toBe('2026-01-05')
  })

  it('giữ đúng ngày ở mốc nửa đêm và mốc cuối ngày', () => {
    expect(toISODate(new Date(2026, 8, 1, 0, 0, 0))).toBe('2026-09-01')
    expect(toISODate(new Date(2026, 8, 1, 23, 59, 59))).toBe('2026-09-01')
  })
})

describe('startOfWeek', () => {
  it('tuần bắt đầu THỨ HAI, không phải Chủ nhật', () => {
    //  01/09/2026 là Thứ Ba → tuần bắt đầu 31/08 (Thứ Hai).
    expect(toISODate(startOfWeek(new Date(2026, 8, 1)))).toBe('2026-08-31')
  })

  it('CHỦ NHẬT thuộc tuần TRƯỚC nó, không mở đầu tuần mới', () => {
    //  `getDay()` trả 0 cho Chủ nhật; quên nắn thì Chủ nhật nhảy về đầu tuần sau
    //  và cả tuần lệch bảy ngày.
    expect(toISODate(startOfWeek(new Date(2026, 8, 6)))).toBe('2026-08-31')
  })

  it('chính Thứ Hai thì giữ nguyên', () => {
    expect(toISODate(startOfWeek(new Date(2026, 7, 31)))).toBe('2026-08-31')
  })

  it('KHÔNG sửa đối tượng gốc của người gọi', () => {
    const goc = new Date(2026, 8, 1, 15, 30)
    startOfWeek(goc)
    expect(goc.getDate()).toBe(1)
    expect(goc.getHours()).toBe(15)
  })
})

describe('shiftAnchor', () => {
  it('chế độ tháng cộng THÁNG, không cộng 30 ngày', () => {
    expect(toISODate(shiftAnchor(new Date(2026, 0, 15), 'month', 1))).toBe('2026-02-01')
  })

  it('ngày 31 sang tháng ngắn KHÔNG bị tràn sang tháng kế tiếp', () => {
    //  `new Date(2026,0,31)` cộng một tháng theo kiểu ngây thơ ra 03/03 vì tháng
    //  2 không có ngày 31 — nhảy vọt hai tháng, và người dùng bấm "tháng sau"
    //  một cái thì mất trắng tháng 2.
    expect(toISODate(shiftAnchor(new Date(2026, 0, 31), 'month', 1))).toBe('2026-02-01')
  })

  it('lùi qua mốc GIAO THỪA đổi đúng năm', () => {
    expect(toISODate(shiftAnchor(new Date(2026, 0, 10), 'month', -1))).toBe('2025-12-01')
    expect(toISODate(shiftAnchor(new Date(2026, 0, 1), 'day', -1))).toBe('2025-12-31')
  })

  it('năm NHUẬN: 29/02 tồn tại và cộng ngày qua nó không hụt', () => {
    expect(toISODate(addDays(new Date(2028, 1, 28), 1))).toBe('2028-02-29')
    expect(toISODate(addDays(new Date(2028, 1, 29), 1))).toBe('2028-03-01')
    //  Năm thường thì 28/02 nhảy thẳng sang 01/03.
    expect(toISODate(addDays(new Date(2026, 1, 28), 1))).toBe('2026-03-01')
  })

  it('bước 0 giữ nguyên mốc ở mọi chế độ', () => {
    const anchor = new Date(2026, 8, 15)
    expect(toISODate(shiftAnchor(anchor, 'day', 0))).toBe('2026-09-15')
    expect(toISODate(shiftAnchor(anchor, 'week', 0))).toBe('2026-09-15')
    //  Chế độ tháng nắn về ngày 1 — đó là mốc của cả tháng.
    expect(toISODate(shiftAnchor(anchor, 'month', 0))).toBe('2026-09-01')
  })

  it('bước lớn vẫn đúng, không tích lũy sai số', () => {
    expect(toISODate(shiftAnchor(new Date(2026, 0, 1), 'month', 24))).toBe('2028-01-01')
    expect(toISODate(shiftAnchor(new Date(2026, 0, 1), 'week', -52))).toBe('2025-01-02')
  })
})

describe('rangeOf', () => {
  it('chế độ NGÀY hỏi đúng một ngày', () => {
    expect(rangeOf(new Date(2026, 8, 1), 'day')).toEqual({
      from: '2026-09-01',
      to: '2026-09-01',
    })
  })

  it('chế độ TUẦN hỏi từ Thứ Hai tới Chủ nhật', () => {
    expect(rangeOf(new Date(2026, 8, 1), 'week')).toEqual({
      from: '2026-08-31',
      to: '2026-09-06',
    })
  })

  it('chế độ THÁNG hỏi theo CẢ LƯỚI 42 ô, không theo mốc đầu/cuối tháng', () => {
    //  Lưới chừa chỗ cho mấy ngày cuối tháng trước và đầu tháng sau. Hỏi đúng
    //  phạm vi tháng thì những ô rìa đó luôn trống, đọc ra thành "hôm đó không
    //  ai nghỉ" — sai hẳn.
    const { from, to } = rangeOf(new Date(2026, 8, 15), 'month')
    expect(from).toBe('2026-08-31')
    expect(to).toBe('2026-10-11')
  })

  it('khoảng luôn có from <= to ở mọi chế độ', () => {
    for (const mode of ['day', 'week', 'month'] as const) {
      const { from, to } = rangeOf(new Date(2026, 1, 1), mode)
      expect(from <= to).toBe(true)
    }
  })
})

describe('buildMonthGrid', () => {
  it('LUÔN 42 ô, kể cả tháng chỉ cần bốn tuần', () => {
    //  Để số hàng đổi theo tháng thì bấm sang tháng sau là cả lưới nhảy cao
    //  thấp, và mọi thứ bên dưới giật theo.
    for (const month of [0, 1, 5, 11]) {
      expect(buildMonthGrid(new Date(2026, month, 1))).toHaveLength(MONTH_GRID_WEEKS * 7)
    }
    //  Tháng 2/2027 bắt đầu đúng Thứ Hai và có 28 ngày — vừa khít 4 tuần.
    expect(buildMonthGrid(new Date(2027, 1, 1))).toHaveLength(42)
  })

  it('ô đầu tiên luôn là THỨ HAI', () => {
    for (const month of [0, 3, 8, 11]) {
      const grid = buildMonthGrid(new Date(2026, month, 1))
      expect(grid[0].date.getDay()).toBe(1)
    }
  })

  it('đánh dấu ngày NGOÀI tháng để tô mờ', () => {
    const grid = buildMonthGrid(new Date(2026, 8, 1))
    //  01/09/2026 là Thứ Ba → ô đầu là 31/08, thuộc tháng trước.
    expect(grid[0]).toMatchObject({ inMonth: false })
    expect(toISODate(grid[0].date)).toBe('2026-08-31')
    expect(grid[1]).toMatchObject({ inMonth: true })
  })

  it('đủ ngày của tháng, không thiếu không thừa', () => {
    const grid = buildMonthGrid(new Date(2026, 8, 1))
    expect(grid.filter((c) => c.inMonth)).toHaveLength(30)
    //  Tháng 2 năm nhuận phải ra 29.
    expect(buildMonthGrid(new Date(2028, 1, 1)).filter((c) => c.inMonth)).toHaveLength(29)
  })

  it('mốc là ngày nào trong tháng cũng ra cùng một lưới', () => {
    const dau = buildMonthGrid(new Date(2026, 8, 1)).map((c) => toISODate(c.date))
    const cuoi = buildMonthGrid(new Date(2026, 8, 30)).map((c) => toISODate(c.date))
    expect(dau).toEqual(cuoi)
  })
})

describe('buildWeekDays', () => {
  it('bảy ngày liên tiếp từ Thứ Hai', () => {
    const days = buildWeekDays(new Date(2026, 8, 3)).map(toISODate)
    expect(days).toEqual([
      '2026-08-31',
      '2026-09-01',
      '2026-09-02',
      '2026-09-03',
      '2026-09-04',
      '2026-09-05',
      '2026-09-06',
    ])
  })
})

describe('rangeLabel', () => {
  it('tuần vắt qua HAI THÁNG thì ghi cả hai', () => {
    //  "31 – 6/9" mà thiếu tháng ở vế trái thì đọc ra là 31/9 — một ngày không
    //  tồn tại.
    expect(rangeLabel(new Date(2026, 8, 1), 'week')).toBe('31/8 – 6/9/2026')
  })

  it('tuần gọn trong một tháng thì không lặp lại tháng', () => {
    expect(rangeLabel(new Date(2026, 8, 10), 'week')).toBe('7 – 13/9/2026')
  })

  it('chế độ ngày ghi rõ thứ mấy', () => {
    expect(rangeLabel(new Date(2026, 8, 1), 'day')).toBe('T3, 1/9/2026')
    expect(rangeLabel(new Date(2026, 8, 6), 'day')).toBe('CN, 6/9/2026')
  })

  it('chế độ tháng ghi tháng và năm', () => {
    expect(rangeLabel(new Date(2026, 8, 15), 'month')).toBe('Tháng 9/2026')
  })
})

describe('holidayNamesOn', () => {
  it('ngày lễ LẶP khớp mọi năm, chỉ so ngày/tháng', () => {
    const list = [holiday()]
    expect(holidayNamesOn(list, '2026-01-01')).toEqual(['Tết Dương lịch'])
    expect(holidayNamesOn(list, '2030-01-01')).toEqual(['Tết Dương lịch'])
  })

  it('ngày lễ KHÔNG lặp chỉ khớp đúng năm của nó', () => {
    //  Tết Âm trôi theo lịch âm — khớp cả những năm khác là báo nghỉ nhầm ngày.
    const list = [holiday({ date: '2026-02-17', name: 'Tết Nguyên đán', is_recurring: false })]
    expect(holidayNamesOn(list, '2026-02-17')).toEqual(['Tết Nguyên đán'])
    expect(holidayNamesOn(list, '2027-02-17')).toEqual([])
  })

  it('bỏ qua ngày lễ đã TẮT', () => {
    expect(holidayNamesOn([holiday({ is_active: false })], '2026-01-01')).toEqual([])
  })

  it('hai pháp nhân khai hai lễ khác nhau cùng ngày thì hiện ĐỦ CẢ HAI', () => {
    //  Giấu bớt một cái đi thì lịch nói sai với một nửa công ty.
    const list = [
      holiday({ id: 1, company_id: 1, name: 'Nghỉ bù nhà máy', is_recurring: false, date: '2026-05-02' }),
      holiday({ id: 2, company_id: 2, name: 'Nghỉ bù văn phòng', is_recurring: false, date: '2026-05-02' }),
    ]
    expect(holidayNamesOn(list, '2026-05-02')).toEqual(['Nghỉ bù nhà máy', 'Nghỉ bù văn phòng'])
  })

  it('trùng TÊN thì chỉ hiện một lần', () => {
    //  Hai pháp nhân cùng khai "Quốc khánh" — in hai lần đọc như dữ liệu hỏng.
    const list = [
      holiday({ id: 1, company_id: 1, name: 'Quốc khánh', date: '2026-09-02' }),
      holiday({ id: 2, company_id: 2, name: 'Quốc khánh', date: '2026-09-02' }),
    ]
    expect(holidayNamesOn(list, '2026-09-02')).toEqual(['Quốc khánh'])
  })

  it('danh sách rỗng thì trả rỗng, không nổ', () => {
    expect(holidayNamesOn([], '2026-01-01')).toEqual([])
  })

  it('29/02 lặp hằng năm chỉ trúng năm NHUẬN', () => {
    //  Chuỗi ngày của năm thường không bao giờ có "02-29", nên không cần luật
    //  riêng — nhưng phải chắc nó không lỡ trúng 01/03.
    const list = [holiday({ date: '2028-02-29', name: 'Ngày lạ' })]
    expect(holidayNamesOn(list, '2028-02-29')).toEqual(['Ngày lạ'])
    expect(holidayNamesOn(list, '2026-03-01')).toEqual([])
  })
})

describe('isWeekend', () => {
  it('CHỈ Chủ nhật — công ty làm cả ngày thứ Bảy', () => {
    //  ⚠️ Đừng "sửa lại cho đúng lệ thường" thành T7+CN. DEGO Holding làm thứ
    //  Bảy (chốt 04/09/2026), và luật này phải khớp `WEEKEND_DAYS` của
    //  `backend/app/modules/leave/workday_service.py`. Lệch nhau thì lịch tô T7
    //  màu nghỉ trong khi backend vẫn trừ phép ngày đó.
    expect(isWeekend(new Date(2026, 8, 6))).toBe(true)   // Chủ nhật
    expect(isWeekend(new Date(2026, 8, 5))).toBe(false)  // Thứ Bảy — vẫn đi làm
    expect(isWeekend(new Date(2026, 8, 4))).toBe(false)
    expect(isWeekend(new Date(2026, 8, 7))).toBe(false)
  })
})

describe('startOfMonth', () => {
  it('về ngày 1 và bỏ phần giờ', () => {
    const d = startOfMonth(new Date(2026, 8, 20, 18, 45))
    expect(toISODate(d)).toBe('2026-09-01')
    expect(d.getHours()).toBe(0)
  })
})
