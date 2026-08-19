import { describe, expect, it } from 'vitest'

import { QTY_STATUS_OPTIONS, moveAmount, moveKindLabel } from './inventory'

describe('moveKindLabel', () => {
  it('dịch hai loại phát sinh thật của sổ kho', () => {
    expect(moveKindLabel('gr')).toBe('Nhập kho (nhận hàng)')
    expect(moveKindLabel('adjust')).toBe('Điều chỉnh tay')
  })

  it('loại lạ vẫn ra chữ, không để lộ mã kỹ thuật ra màn hình', () => {
    expect(moveKindLabel('transfer')).toBe('Khác')
    expect(moveKindLabel('')).toBe('Khác')
  })
})

describe('moveAmount', () => {
  it('dòng nhập ra số dương', () => {
    expect(moveAmount({ qty: 10, unit_price: 25000 })).toBe(250000)
  })

  // Lỗi của bản v1: nó hiện `Math.abs(qty × unit_price)`, nên dòng điều chỉnh
  // GIẢM hiện thành tiền dương — cột "Thay đổi" ghi -5 mà cột "Thành tiền" ghi
  // số dương, hai cột cùng dòng nói ngược nhau. Đừng bọc lại abs.
  it('dòng giảm giữ dấu âm, không bọc trị tuyệt đối', () => {
    expect(moveAmount({ qty: -5, unit_price: 25000 })).toBe(-125000)
  })

  it('chưa có đơn giá thì thành tiền bằng 0', () => {
    expect(moveAmount({ qty: 12, unit_price: 0 })).toBe(0)
  })
})

describe('QTY_STATUS_OPTIONS', () => {
  // Ba chuỗi này backend so sánh bằng `==` trong `list_inventory`; đổi chữ ở đây
  // là bộ lọc im lặng trả về toàn bộ danh sách chứ không báo lỗi.
  it('giữ đúng ba mã trạng thái backend đang so khớp', () => {
    expect(QTY_STATUS_OPTIONS.map((option) => option.value)).toEqual([
      'in_stock',
      'out_of_stock',
      'negative_stock',
    ])
  })

  it('mã nào cũng có nhãn tiếng Việt', () => {
    for (const option of QTY_STATUS_OPTIONS) {
      expect(option.label, option.value).toBeTruthy()
    }
  })
})
