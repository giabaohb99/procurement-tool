import { describe, expect, it } from 'vitest'

import { TONE_CLASS } from '@/shared/ui/status-tone'

import {
  changeSummaryText,
  changeValueText,
  defaultLogRange,
  formatDuration,
  formatHourLabel,
  httpStatusHint,
  httpStatusTone,
  spansMultipleDays,
  tableLabel,
} from './system-log-format'

describe('httpStatusTone', () => {
  it('keeps "blocked" (401/403) apart from "broken" (5xx)', () => {
    //  Lý do bài kiểm này không được xóa: gộp hai nhóm vào một tông đỏ thì màn
    //  hình đầy đỏ mỗi ngày vì 403 của người thiếu quyền, và sự cố thật chìm
    //  trong đó. Backend cũng tách hai lựa chọn lọc vì đúng lý do này.
    expect(httpStatusTone(403)).not.toBe(httpStatusTone(500))
    expect(httpStatusTone(401)).toBe(httpStatusTone(403))
  })

  it('treats status 0 as unknown, not as success', () => {
    //  `0` = chưa ghi được mã trả về (tiến trình chết giữa chừng). Tô xanh là
    //  nói dối đúng lúc người ta đang tìm chỗ hỏng.
    expect(httpStatusTone(0)).toBe('neutral')
    expect(httpStatusTone(200)).toBe('done')
  })

  it('returns only tones that really exist in TONE_CLASS', () => {
    //  Bảng tông là của module khác. Đổi tên một khóa bên đó mà không sửa bên
    //  này thì ô trạng thái mất hẳn màu, im lặng — TS không bắt được vì
    //  `TONE_CLASS[tone]` vẫn hợp kiểu cho tới khi khóa bị xóa.
    for (const status of [0, 199, 200, 204, 301, 400, 401, 403, 404, 422, 499, 500, 503, 599]) {
      expect(Object.keys(TONE_CLASS)).toContain(httpStatusTone(status))
    }
  })

  it('survives absurd status codes without throwing', () => {
    expect(Object.keys(TONE_CLASS)).toContain(httpStatusTone(-1))
    expect(Object.keys(TONE_CLASS)).toContain(httpStatusTone(999999))
  })
})

describe('httpStatusHint', () => {
  it('explains 403 as missing permission, not as a system fault', () => {
    expect(httpStatusHint(403)).toContain('quyền')
    expect(httpStatusHint(500)).toContain('Lỗi hệ thống')
  })

  it('says the process died instead of calling status 0 a success', () => {
    expect(httpStatusHint(0)).not.toContain('Thành công')
  })
})

describe('formatDuration', () => {
  it('keeps milliseconds below one second', () => {
    //  200-900ms là dải mọi câu hỏi hiệu năng diễn ra; quy sang "0,4 s" là ném
    //  mất phần phân biệt.
    expect(formatDuration(84)).toBe('84 ms')
    expect(formatDuration(999)).toBe('999 ms')
  })

  it('switches to seconds from one second up', () => {
    expect(formatDuration(1000)).toBe('1 s')
    expect(formatDuration(4281)).toBe('4,3 s')
  })

  it('shows a dash for zero, negative and missing values', () => {
    expect(formatDuration(0)).toBe('—')
    expect(formatDuration(-5)).toBe('—')
  })
})

describe('changeSummaryText', () => {
  it('drops the table part when a single table was touched', () => {
    expect(changeSummaryText(3, 1)).toBe('3 trường')
  })

  it('shows both numbers when one click reached several tables', () => {
    //  Đây là thứ phân biệt một cú sửa ô đơn giá với một cú Duyệt kéo theo bảng
    //  việc + bảng thông báo + bảng chứng từ.
    expect(changeSummaryText(7, 3)).toBe('7 trường / 3 bảng')
  })

  it('shows a dash when nothing changed', () => {
    expect(changeSummaryText(0, 0)).toBe('—')
    //  Số bảng > 0 mà số trường = 0 là dữ liệu vô lý; vẫn không được in "0 trường".
    expect(changeSummaryText(0, 2)).toBe('—')
  })
})

describe('formatHourLabel', () => {
  it('reads the backend bucket "YYYY-MM-DD HH" as an hour', () => {
    expect(formatHourLabel('2026-09-15 10')).toBe('10:00')
  })

  it('accepts the ISO "T" separator too', () => {
    //  MySQL `CAST(... AS CHAR)` cho dấu cách, SQLite cũng vậy — nhưng nếu một
    //  ngày nào đó cột đi qua serializer khác thì chữ T không được làm hỏng trục.
    expect(formatHourLabel('2026-09-15T10:41:17')).toBe('10:00')
  })

  it('adds the day when the filter spans more than one day', () => {
    //  Lọc ba ngày mà trục X chỉ có giờ thì ba cột «10:00» đứng cạnh nhau, và
    //  "đỉnh lỗi lúc 10 giờ NGÀY NÀO" là thông tin duy nhất đang đi tìm.
    expect(formatHourLabel('2026-09-15 10', true)).toBe('15/09 10:00')
  })

  it('returns garbage input unchanged instead of printing NaN', () => {
    expect(formatHourLabel('')).toBe('')
    expect(formatHourLabel('không phải ngày')).toBe('không phải ngày')
  })
})

describe('spansMultipleDays', () => {
  it('is false when both ends are the same day', () => {
    expect(spansMultipleDays('2026-09-15', '2026-09-15')).toBe(false)
    expect(spansMultipleDays('2026-09-15T00:00', '2026-09-15T23:59')).toBe(false)
  })

  it('is true when a bound is missing — an open range can reach any day', () => {
    expect(spansMultipleDays('', '2026-09-15')).toBe(true)
    expect(spansMultipleDays('2026-09-15', '')).toBe(true)
  })
})

describe('defaultLogRange', () => {
  it('puts both ends on the same day, mirroring the backend default_range()', () => {
    //  Bẫy đã xảy ra ở backend: trả (hôm nay, ngày mai) rồi ô «Đến» được kéo tới
    //  23:59:59 của NGÀY MAI — khoảng mặc định lặng lẽ thành hai ngày.
    const range = defaultLogRange(new Date(2026, 8, 15, 14, 30))
    expect(range).toEqual({ from: '2026-09-15', to: '2026-09-15' })
  })

  it('pads month and day so the string stays sortable', () => {
    expect(defaultLogRange(new Date(2026, 0, 5))).toEqual({ from: '2026-01-05', to: '2026-01-05' })
  })
})

describe('tableLabel', () => {
  it('strips the tab_ prefix but keeps the real table name', () => {
    //  Cố ý không dịch sang tiếng Việt: người đi truy sự cố cần đúng cái tên gõ
    //  được vào câu SQL.
    expect(tableLabel('tab_purchase_order')).toBe('purchase_order')
    expect(tableLabel('purchase_order')).toBe('purchase_order')
  })

  it('removes only the leading prefix', () => {
    expect(tableLabel('tab_tab_x')).toBe('tab_x')
  })
})

describe('changeValueText', () => {
  it('tells "masked" apart from "empty"', () => {
    //  Hai thứ này mà in giống nhau thì người đọc kết luận sai về dữ liệu thật.
    expect(changeValueText('', false)).toBe('(trống)')
    expect(changeValueText('***', true)).toBe('(đã che)')
  })

  it('treats whitespace-only values as empty', () => {
    expect(changeValueText('   ', false)).toBe('(trống)')
  })

  it('never leaks the raw value of a masked field', () => {
    expect(changeValueText('0912345678', true)).toBe('(đã che)')
  })
})
