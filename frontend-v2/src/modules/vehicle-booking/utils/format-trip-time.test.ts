import { describe, expect, it } from 'vitest'

import { formatTripTime } from './format-trip-time'

//  Múi giờ khi chạy test ghim `Asia/Ho_Chi_Minh` (xem `vitest.config.ts`), nên mọi
//  khẳng định dưới đây đọc theo giờ Việt Nam.
const NOW = new Date('2026-09-16T10:00:00')

describe('formatTripTime', () => {
  it('gộp ngày lại một lần khi chuyến đi về trong cùng ngày', () => {
    expect(formatTripTime('2026-09-21T10:00', '2026-09-21T15:00', NOW)).toBe(
      '21/09/2026 · 10:00 – 15:00',
    )
  })

  it('ghi đủ hai mốc ngày khi chuyến qua ngày khác', () => {
    expect(formatTripTime('2026-09-21T10:00', '2026-09-23T17:30', NOW)).toBe(
      '21/09/2026 10:00 → 23/09/2026 17:30',
    )
  })

  it('gọi tên hôm nay · ngày mai · hôm qua thay cho con số ngày', () => {
    expect(formatTripTime('2026-09-16T08:00', '2026-09-16T12:00', NOW)).toBe(
      'Hôm nay · 08:00 – 12:00',
    )
    expect(formatTripTime('2026-09-17T08:00', '2026-09-17T12:00', NOW)).toBe(
      'Ngày mai · 08:00 – 12:00',
    )
    expect(formatTripTime('2026-09-15T08:00', '2026-09-15T12:00', NOW)).toBe(
      'Hôm qua · 08:00 – 12:00',
    )
  })

  //  Lỗi kinh điển: lấy (b - a) / 86400000 để đếm ngày. 23:00 hôm nay và 01:00
  //  ngày mai cách nhau 2 tiếng → ra 0 ngày → chuyến NGÀY MAI bị dán nhãn "Hôm nay",
  //  tức tài xế đọc ra một chuyến sắp chạy trong hôm nay. Đừng xoá bài này.
  it('đếm theo NGÀY LỊCH, không theo khoảng 24 giờ', () => {
    const khuya = new Date('2026-09-16T23:30:00')
    expect(formatTripTime('2026-09-17T01:00', '2026-09-17T03:00', khuya)).toBe(
      'Ngày mai · 01:00 – 03:00',
    )
    //  Ngược lại: cách nhau 26 tiếng nhưng vẫn là ngày mai, không phải ngày kia.
    const sang = new Date('2026-09-16T01:00:00')
    expect(formatTripTime('2026-09-17T03:00', '2026-09-17T05:00', sang)).toBe(
      'Ngày mai · 03:00 – 05:00',
    )
  })

  //  Chuyến 22:00 → 23:59 cùng đêm giờ Việt Nam rơi vào HAI ngày UTC khác nhau.
  //  So ngày bằng mốc UTC thì nó bị coi là chuyến qua đêm và in ra hai lần ngày.
  it('so ngày theo giờ địa phương, không theo UTC', () => {
    expect(formatTripTime('2026-09-21T22:00', '2026-09-21T23:59', NOW)).toBe(
      '21/09/2026 · 22:00 – 23:59',
    )
  })

  it('bỏ mốc kết thúc khi chưa có giờ về', () => {
    expect(formatTripTime('2026-09-21T10:00', '', NOW)).toBe('21/09/2026 · 10:00')
    expect(formatTripTime('2026-09-21T10:00', null, NOW)).toBe('21/09/2026 · 10:00')
  })

  it('trả dấu gạch khi thiếu giờ đi hoặc chuỗi hỏng', () => {
    expect(formatTripTime('', '2026-09-21T15:00', NOW)).toBe('—')
    expect(formatTripTime(null, null, NOW)).toBe('—')
    expect(formatTripTime(undefined, undefined, NOW)).toBe('—')
    expect(formatTripTime('khong-phai-ngay', '2026-09-21T15:00', NOW)).toBe('—')
  })

  //  Giờ về hỏng KHÔNG được kéo cả dòng xuống '—': giờ đi vẫn là thông tin thật.
  it('giữ giờ đi khi riêng giờ về hỏng', () => {
    expect(formatTripTime('2026-09-21T10:00', 'khong-phai-ngay', NOW)).toBe('21/09/2026 · 10:00')
  })

  it('không vỡ ở mốc giao năm', () => {
    const giaothua = new Date('2026-12-31T20:00:00')
    expect(formatTripTime('2027-01-01T06:00', '2027-01-01T09:00', giaothua)).toBe(
      'Ngày mai · 06:00 – 09:00',
    )
    expect(formatTripTime('2026-12-31T22:00', '2027-01-01T02:00', giaothua)).toBe(
      '31/12/2026 22:00 → 01/01/2027 02:00',
    )
  })
})
