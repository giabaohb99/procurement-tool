import { describe, expect, it } from 'vitest'

import { dayMonthOf, formatBookingRange, formatStamp, timeOf } from './booking-time-format'

describe('formatStamp', () => {
  it('turns an ISO-to-minute stamp into dd/mm/yyyy hh:mm', () => {
    expect(formatStamp('2026-09-10T05:00')).toBe('10/09/2026 05:00')
  })

  //  `created_at` của backend dùng dấu CÁCH thay chữ T — cùng một hàm phải nuốt
  //  được cả hai, nếu không thì mỗi màn lại nhớ một luật.
  it('accepts the space-separated shape that created_at uses', () => {
    expect(formatStamp('2026-09-10 05:00:31')).toBe('10/09/2026 05:00')
  })

  it('keeps just the date when there is no clock part', () => {
    expect(formatStamp('2026-09-10')).toBe('10/09/2026')
  })

  it('returns empty for every flavour of missing value', () => {
    expect(formatStamp('')).toBe('')
    expect(formatStamp(null)).toBe('')
    expect(formatStamp(undefined)).toBe('')
  })

  //  Dữ liệu bẩn thì trả NGUYÊN chuỗi chứ không ra "undefined/undefined/" —
  //  người dùng đọc được chuỗi gốc còn đoán ra nguồn sai, đọc "NaN" thì không.
  it('hands back the raw string when it is not a date at all', () => {
    expect(formatStamp('hôm qua')).toBe('hôm qua')
  })
})

describe('timeOf', () => {
  it('cuts the HH:mm out of an ISO-to-minute stamp', () => {
    expect(timeOf('2026-09-10T05:00')).toBe('05:00')
  })

  it('still reads the time when the backend sends seconds', () => {
    expect(timeOf('2026-09-10T05:00:33')).toBe('05:00')
  })

  it('returns empty for a date without a time part', () => {
    expect(timeOf('2026-09-10')).toBe('')
  })

  it('returns empty for an empty string', () => {
    expect(timeOf('')).toBe('')
  })
})

describe('dayMonthOf', () => {
  it('reorders to dd/MM for Vietnamese reading', () => {
    expect(dayMonthOf('2026-09-04T09:30')).toBe('04/09')
  })

  it('keeps the leading zero of a single-digit day', () => {
    expect(dayMonthOf('2026-01-02T00:00')).toBe('02/01')
  })

  it('returns empty for an empty string', () => {
    expect(dayMonthOf('')).toBe('')
  })
})

describe('formatBookingRange', () => {
  it('shows only the clock for a trip inside one day', () => {
    expect(formatBookingRange('2026-09-04T09:30', '2026-09-04T17:00')).toBe('09:30 – 17:00')
  })

  //  Lỗi đã từng xảy ra: bản đầu ghi ngày ở MỘT đầu ('09:30 → 05/09 07:00') nên
  //  không đọc ra giờ bắt đầu thuộc ngày nào. Đừng bỏ khẳng định này.
  it('dates BOTH ends when the trip crosses midnight', () => {
    expect(formatBookingRange('2026-09-04T09:30', '2026-09-05T07:00')).toBe(
      '04/09 09:30 → 05/09 07:00',
    )
  })

  it('dates both ends across a month boundary too', () => {
    expect(formatBookingRange('2026-08-31T22:00', '2026-09-01T06:15')).toBe(
      '31/08 22:00 → 01/09 06:15',
    )
  })

  it('collapses to a single clock when start and end are the same instant', () => {
    expect(formatBookingRange('2026-09-04T09:30', '2026-09-04T09:30')).toBe('09:30')
  })

  it('falls back to the start when the end time is missing', () => {
    expect(formatBookingRange('2026-09-04T09:30', '')).toBe('09:30')
  })

  it('renders a dash when neither end is known', () => {
    expect(formatBookingRange('', '')).toBe('—')
  })

  //  Phiếu chỉ có NGÀY (chưa ai nhập giờ khởi hành) vẫn phải đọc ra cái gì đó —
  //  không được trả về chuỗi rỗng, vì thẻ hover sẽ hiện một dòng trống vô nghĩa.
  it('uses the date when the start has no clock at all', () => {
    expect(formatBookingRange('2026-09-04', '')).toBe('04/09')
  })

  it('does not leave a stray arrow when a multi-day end has no clock', () => {
    expect(formatBookingRange('2026-09-04T09:30', '2026-09-06')).toBe('04/09 09:30 → 06/09')
  })

  it('handles an end BEFORE the start without crashing (dirty legacy rows)', () => {
    expect(formatBookingRange('2026-09-06T09:30', '2026-09-04T07:00')).toBe(
      '06/09 09:30 → 04/09 07:00',
    )
  })
})
