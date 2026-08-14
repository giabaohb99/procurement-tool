import { describe, expect, it } from 'vitest'

import { formatMoney, formatQuantity, formatUnitPrice } from './format-money'

describe('formatMoney', () => {
  it('làm tròn tới đồng, không để lẻ rò ra cột danh sách', () => {
    // Chính lỗi đã sinh ra hàm này: `toLocaleString('vi-VN')` trần cho ra
    // "4.760.000,08".
    expect(formatMoney(4_760_000.08)).toBe('4.760.000')
    expect(formatMoney(4_760_000.5)).toBe('4.760.001')
  })

  it('phân cách nghìn theo kiểu Việt Nam (dấu chấm)', () => {
    expect(formatMoney(1_234_567)).toBe('1.234.567')
  })

  it('nhận chuỗi số vì backend trả Decimal dưới dạng chuỗi', () => {
    expect(formatMoney('1000000')).toBe('1.000.000')
    expect(formatMoney('1000000.4')).toBe('1.000.000')
  })

  it('số 0 vẫn hiện "0", không bị nuốt thành rỗng', () => {
    expect(formatMoney(0)).toBe('0')
    expect(formatMoney('0')).toBe('0')
  })

  it('trả chuỗi rỗng khi không có số để hiện', () => {
    expect(formatMoney(null)).toBe('')
    expect(formatMoney(undefined)).toBe('')
    expect(formatMoney('')).toBe('')
    expect(formatMoney('abc')).toBe('')
    expect(formatMoney(Number.NaN)).toBe('')
    expect(formatMoney(Number.POSITIVE_INFINITY)).toBe('')
  })

  it('giữ dấu âm (điều chỉnh giảm, công nợ âm)', () => {
    expect(formatMoney(-1_500_000)).toBe('-1.500.000')
  })
})

describe('formatUnitPrice', () => {
  it('giữ tối đa 4 số thập phân', () => {
    expect(formatUnitPrice(1234.56789)).toBe('1.234,5679')
  })

  it('không ép đủ 4 số khi đơn giá tròn', () => {
    expect(formatUnitPrice(1234)).toBe('1.234')
    expect(formatUnitPrice(1234.5)).toBe('1.234,5')
  })
})

describe('formatQuantity', () => {
  it('giữ tối đa 3 số thập phân', () => {
    expect(formatQuantity(10.12345)).toBe('10,123')
    expect(formatQuantity(10)).toBe('10')
  })
})
