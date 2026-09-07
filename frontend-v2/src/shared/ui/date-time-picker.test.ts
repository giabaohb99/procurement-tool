import { describe, expect, it } from 'vitest'

import { buildTimeOptions, joinDateTime, splitDateTime } from './date-time-picker'

/**
 * Ô chọn NGÀY + GIỜ thay cho `<input type="datetime-local">`.
 *
 * Ba hàm thuần ở đây giữ đúng một hợp đồng: **giá trị vào/ra vẫn là chuỗi
 * `YYYY-MM-DDTHH:mm` theo giờ ĐỊA PHƯƠNG**. Lệch một ký tự là phiếu đặt phòng
 * mở ra với ô trống dù dữ liệu vẫn còn nguyên trong máy chủ.
 */

describe('splitDateTime', () => {
  it('tách đúng hai vế của một mốc đầy đủ', () => {
    expect(splitDateTime('2026-09-10T09:00')).toEqual(['2026-09-10', '09:00'])
  })

  it('CẮT phần giây mà API trả kèm', () => {
    //  `/api/room-bookings` trả `09:00:00`; không cắt thì không mục nào trong
    //  danh sách giờ khớp và ô hiện ra như chưa chọn.
    expect(splitDateTime('2026-09-10T09:00:00')).toEqual(['2026-09-10', '09:00'])
  })

  it('chuỗi rỗng ra hai vế rỗng, không nổ', () => {
    expect(splitDateTime('')).toEqual(['', ''])
  })

  it('chỉ có ngày, chưa có giờ', () => {
    expect(splitDateTime('2026-09-10')).toEqual(['2026-09-10', ''])
  })

  it('KHÔNG tự dịch múi giờ — giữ nguyên con số người dùng thấy', () => {
    //  Máy chạy ở UTC+7. Nếu chỗ nào đó lỡ đi qua `new Date()` thì 00:30 sẽ lùi
    //  về hôm trước; hàm này chỉ được cắt chuỗi.
    expect(splitDateTime('2026-01-01T00:30')).toEqual(['2026-01-01', '00:30'])
  })
})

describe('joinDateTime', () => {
  it('ghép lại đúng dạng cũ', () => {
    expect(joinDateTime('2026-09-10', '14:30')).toBe('2026-09-10T14:30')
  })

  it('thiếu một vế thì là CHƯA CHỌN, không phải nửa mốc', () => {
    //  Một cái giờ không có ngày vẫn trông như đã điền nhưng không nói được gì —
    //  gửi lên là backend 422, mà người dùng thì thấy ô có chữ.
    expect(joinDateTime('', '14:30')).toBe('')
    expect(joinDateTime('2026-09-10', '')).toBe('')
  })
})

describe('buildTimeOptions', () => {
  it('bước 15 phút phủ trọn một ngày, không lố sang 24:00', () => {
    const options = buildTimeOptions(15)
    expect(options).toHaveLength(96)
    expect(options[0]).toBe('00:00')
    expect(options.at(-1)).toBe('23:45')
  })

  it('luôn hai chữ số — 9 giờ là «09:00», không phải «9:0»', () => {
    expect(buildTimeOptions(60)[9]).toBe('09:00')
  })

  it('bước 30 và bước 60 vẫn ra đúng số mốc', () => {
    expect(buildTimeOptions(30)).toHaveLength(48)
    expect(buildTimeOptions(60)).toHaveLength(24)
  })
})
