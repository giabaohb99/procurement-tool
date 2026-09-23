import { describe, expect, it } from 'vitest'

import { isCargoVehicle } from './is-cargo-vehicle'

describe('isCargoVehicle', () => {
  it('nhận ra xe tải dù người dùng gõ hoa thường lẫn lộn', () => {
    expect(isCargoVehicle('Xe tải')).toBe(true)
    expect(isCargoVehicle('XE TẢI 2T5')).toBe(true)
    expect(isCargoVehicle('xe tải thùng')).toBe(true)
  })

  it('XE BÁN TẢI đếm theo CHỖ chứ không theo tấn', () => {
    //  Lỗi thật 22/09/2026: bốn chiếc Hilux/BT50 khai `capacity = 5` (số chỗ)
    //  hiện ra "5 tấn" chỉ vì tên loại có chữ "tải".
    expect(isCargoVehicle('Xe bán tải')).toBe(false)
    expect(isCargoVehicle('XE BÁN TẢI')).toBe(false)
  })

  it('xe chở người không phải xe tải', () => {
    expect(isCargoVehicle('Xe con')).toBe(false)
    expect(isCargoVehicle('Xe 16 chỗ')).toBe(false)
    expect(isCargoVehicle('')).toBe(false)
  })

  it('không nhầm chữ "tai" không dấu thành "tải"', () => {
    //  Loại xe là chữ tự do; bỏ dấu là một cụm khác hẳn nên đừng đoán rộng ra.
    expect(isCargoVehicle('Xe tai nan')).toBe(false)
  })
})
