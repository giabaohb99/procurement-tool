import { describe, expect, it } from 'vitest'

import { formatVehicleCapacity } from './format-vehicle-capacity'

describe('formatVehicleCapacity', () => {
  it('xe chở người đếm bằng CHỖ, xe tải đếm bằng TẤN', () => {
    expect(formatVehicleCapacity('Xe con', 7)).toBe('7 chỗ')
    expect(formatVehicleCapacity('Xe tải', 6.8)).toBe('6,8 tấn')
  })

  it('xe bán tải đếm bằng CHỖ — 5 chỗ, không phải 5 tấn', () => {
    expect(formatVehicleCapacity('Xe bán tải', 5)).toBe('5 chỗ')
  })

  it('dùng dấu phẩy thập phân kiểu Việt, không phải dấu chấm', () => {
    expect(formatVehicleCapacity('Xe tải', 2.4)).toBe('2,4 tấn')
  })

  it('coi 0 / số âm là CHƯA KHAI chứ không phải "0 chỗ"', () => {
    //  Ô để trống thì backend trả 0 — bày "0 chỗ" là khẳng định một điều sai.
    expect(formatVehicleCapacity('Xe con', 0)).toBe('—')
    expect(formatVehicleCapacity('Xe tải', -3)).toBe('—')
  })

  it('không vỡ khi dữ liệu hỏng (NaN, Infinity)', () => {
    expect(formatVehicleCapacity('Xe con', Number.NaN)).toBe('—')
    expect(formatVehicleCapacity('Xe tải', Number.POSITIVE_INFINITY)).toBe('—')
  })

  it('cắt phần lẻ vô nghĩa thay vì kéo dài ô bảng', () => {
    //  Backend lưu DECIMAL nên 2.4 có thể về dạng 2.400000001 — cột chỉ rộng
    //  120px, in hết phần lẻ là cụt đuôi bằng dấu "…".
    expect(formatVehicleCapacity('Xe tải', 2.400000001)).toBe('2,4 tấn')
  })

  it('loại xe bỏ trống thì mặc định đếm bằng chỗ', () => {
    expect(formatVehicleCapacity('', 4)).toBe('4 chỗ')
  })
})
