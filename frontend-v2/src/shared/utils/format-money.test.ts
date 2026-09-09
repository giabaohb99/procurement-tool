import { describe, expect, it } from 'vitest'

import {
  formatMoney,
  formatMoneyWithCurrency,
  formatPercent,
  formatQuantity,
  formatUnitPrice,
} from './format-money'

describe('formatMoneyWithCurrency', () => {
  it('rounds VND to the dong and appends the dong sign', () => {
    expect(formatMoneyWithCurrency(4_760_000.08, 'VND')).toBe('4.760.000 đ')
    expect(formatMoneyWithCurrency(4_760_000.08, 'vnd')).toBe('4.760.000 đ')
  })

  it('treats a blank currency as VND', () => {
    expect(formatMoneyWithCurrency(1_000, '')).toBe('1.000 đ')
    expect(formatMoneyWithCurrency(1_000, null)).toBe('1.000 đ')
    expect(formatMoneyWithCurrency(1_000)).toBe('1.000 đ')
  })

  // Lỗi bao-CR-319: đơn USD từng hiện "5.230 đ" — mất số lẻ và sai đơn vị.
  it('keeps decimals and shows the code for a foreign currency instead of the dong sign', () => {
    expect(formatMoneyWithCurrency(5_230.5, 'USD')).toBe('5.230,5 USD')
    expect(formatMoneyWithCurrency(12, 'cny')).toBe('12 CNY')
  })

  it('leaves only the unit for an empty amount', () => {
    expect(formatMoneyWithCurrency(null, 'USD')).toBe(' USD')
    expect(formatMoneyWithCurrency('abc', 'VND')).toBe(' đ')
  })
})

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

describe('formatPercent', () => {
  it('nhận số phần trăm sẵn, không nhân thêm 100', () => {
    expect(formatPercent(41.67)).toBe('41,67%')
    expect(formatPercent(0.5)).toBe('0,5%')
  })

  it('không ép đủ 2 số thập phân khi tỷ lệ tròn', () => {
    expect(formatPercent(30)).toBe('30%')
    expect(formatPercent(0)).toBe('0%')
  })

  it('trả chuỗi rỗng khi không có số để hiện', () => {
    expect(formatPercent(null)).toBe('')
    expect(formatPercent(undefined)).toBe('')
  })
})
