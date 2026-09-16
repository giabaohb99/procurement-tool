import { describe, expect, it } from 'vitest'

import { parseLocalDate } from '@/shared/utils/format-date'
import {
  CALENDAR_VIEWS,
  DEFAULT_CALENDAR_MODE,
  isTimeGridView,
  modeFromView,
  viewFromMode,
} from './calendar-views'

describe('viewFromMode', () => {
  it('đổi ba chữ trong URL sang đúng tên khám của FullCalendar', () => {
    expect(viewFromMode('day')).toBe('timeGridDay')
    expect(viewFromMode('week')).toBe('timeGridWeek')
    expect(viewFromMode('month')).toBe('dayGridMonth')
  })

  //  Người dùng sửa tay URL, hoặc link cũ từ bản trước. FC nhận một tên khám
  //  không có thật thì ném lỗi lúc dựng và CẢ TRANG TRẮNG — nên mọi rác đều
  //  phải rơi về khám mặc định, không được lọt xuống FC.
  it.each([
    ['chữ lạ', 'nam'],
    ['tên khám của FC, không phải chữ của URL', 'timeGridDay'],
    ['sai hoa thường', 'Day'],
    ['chuỗi rỗng', ''],
    ['khoảng trắng', ' day '],
    ['thiếu hẳn param', null],
    ['undefined', undefined],
    //  Khóa có sẵn trên mọi object JS — tra bảng bằng `[raw]` mà không chặn thì
    //  `?mode=constructor` trả về hàm khởi tạo chứ không phải tên khám.
    ['khóa kế thừa của Object', 'constructor'],
    ['khóa kế thừa của Object (2)', '__proto__'],
    ['khóa kế thừa của Object (3)', 'toString'],
  ])('rơi về khám mặc định khi %s', (_label, raw) => {
    expect(viewFromMode(raw)).toBe('dayGridMonth')
  })
})

describe('modeFromView', () => {
  it('đổi ngược tên khám FullCalendar về chữ ghi trong URL', () => {
    expect(modeFromView('timeGridDay')).toBe('day')
    expect(modeFromView('timeGridWeek')).toBe('week')
    expect(modeFromView('dayGridMonth')).toBe('month')
  })

  it('khám lạ (FC đổi tên, hoặc thêm khám mới mà quên khai) về mặc định', () => {
    expect(modeFromView('dayGridDay')).toBe(DEFAULT_CALENDAR_MODE)
    expect(modeFromView('')).toBe(DEFAULT_CALENDAR_MODE)
  })

  //  Hai chiều phải khớp nhau: lệch là bấm đổi khám xong F5 ra khám khác.
  it('đi vòng tròn mode -> view -> mode không đổi giá trị', () => {
    for (const mode of ['day', 'week', 'month'] as const) {
      expect(modeFromView(viewFromMode(mode))).toBe(mode)
    }
  })

  //  Ràng buộc với bộ chọn Ngày · Tuần · Tháng trên thanh công cụ: thêm một
  //  khám vào `CALENDAR_VIEWS` mà quên khai trong bảng URL thì khám đó im lặng
  //  không lưu được vào link, và test này đỏ lên ngay.
  it('mọi khám trong bộ chọn đều ghi được vào URL', () => {
    for (const { value } of CALENDAR_VIEWS) {
      expect(viewFromMode(modeFromView(value))).toBe(value)
    }
  })
})

describe('isTimeGridView', () => {
  it('chỉ Ngày và Tuần mới có trục giờ', () => {
    expect(isTimeGridView('timeGridDay')).toBe(true)
    expect(isTimeGridView('timeGridWeek')).toBe(true)
    expect(isTimeGridView('dayGridMonth')).toBe(false)
    expect(isTimeGridView('')).toBe(false)
  })
})

//  `?date=` đi qua `parseLocalDate` của tầng dùng chung. Test ở đây vì trang
//  lịch là nơi chuỗi đó tới TỪ NGƯỜI DÙNG (thanh địa chỉ), không phải từ API —
//  hỏng cái này là FullCalendar nhận `Invalid Date` và trắng trang.
describe('?date= của lịch đặt xe', () => {
  it('đọc đúng ngày theo giờ địa phương, không lùi một ngày vì UTC', () => {
    const d = parseLocalDate('2026-08-23')
    expect(d?.getFullYear()).toBe(2026)
    expect(d?.getMonth()).toBe(7) // tháng 8
    expect(d?.getDate()).toBe(23)
  })

  it.each([['rỗng', ''], ['chữ', 'hom-nay'], ['thiếu số 0', '2026-8-3'], ['null', null]])(
    'trả undefined khi %s — FC tự mở ở hôm nay',
    (_label, raw) => {
      expect(parseLocalDate(raw)).toBeUndefined()
    },
  )

  //  ⚠️ Hành vi ĐÃ BIẾT, không phải lỗi: ngày không có thật bị `Date` đẩy sang
  //  tháng sau thay vì bị loại. Lịch vẫn mở được (rơi vào 02/03), nên chấp
  //  nhận. Ghi ra đây để người sau sửa `parseLocalDate` biết có chỗ này trông vào.
  it('ngày không có thật thì trượt sang ngày kế, không làm vỡ lịch', () => {
    const d = parseLocalDate('2026-02-30')
    expect(d).toBeDefined()
    expect(Number.isNaN(d?.getTime())).toBe(false)
  })
})
