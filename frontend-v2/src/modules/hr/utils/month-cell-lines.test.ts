import { describe, expect, it } from 'vitest'

import { monthCellDayLabel, monthCellLinesFor, splitMonthCellLines } from './month-cell-lines'

describe('splitMonthCellLines', () => {
  it('vừa đủ chỗ thì bày hết, không sinh dòng "+0"', () => {
    expect(splitMonthCellLines(3, false)).toEqual({ visible: 3, hidden: 0 })
    expect(splitMonthCellLines(0, false)).toEqual({ visible: 0, hidden: 0 })
  })

  it('tràn thì dòng "+N" CHIẾM CHỖ của một chip, không cộng thêm dòng thứ năm', () => {
    //  Ô cao bốn dòng: số ngày + ba chip. Bày đủ ba chip rồi thêm "+1" là năm
    //  dòng, dòng cuối bị đường kẻ ô cắt ngang — mà nó là lối duy nhất để đọc
    //  tên những người bị giấu.
    expect(splitMonthCellLines(4, false)).toEqual({ visible: 2, hidden: 2 })
    expect(splitMonthCellLines(12, false)).toEqual({ visible: 2, hidden: 10 })
  })

  it('ngày lễ ăn một dòng nên chỗ cho chip hụt đi một', () => {
    expect(splitMonthCellLines(2, true)).toEqual({ visible: 2, hidden: 0 })
    expect(splitMonthCellLines(3, true)).toEqual({ visible: 1, hidden: 2 })
  })

  it('không bao giờ trả số âm — tổng visible + hidden luôn bằng tổng đầu vào', () => {
    for (const total of [0, 1, 2, 3, 7, 30, 1000]) {
      for (const holiday of [false, true]) {
        const { visible, hidden } = splitMonthCellLines(total, holiday)
        expect(visible).toBeGreaterThanOrEqual(0)
        expect(hidden).toBeGreaterThanOrEqual(0)
        expect(visible + hidden).toBe(total)
      }
    }
  })
})

describe('monthCellLinesFor', () => {
  it('ô cao thì bày được nhiều chip hơn — laptop 1280×800 KHÁC màn 1440×900', () => {
    //  Đúng hai cửa sổ đã đo trên bản chạy: ô ~105px cho ba dòng, ô ~79px chỉ
    //  hai. Đặt cứng ba dòng thì laptop thấp bày ra chip thứ ba bị cắt ngang.
    expect(monthCellLinesFor(96)).toBe(3)
    expect(monthCellLinesFor(79)).toBe(2)
  })

  it('sàn HAI dòng — mất dòng "+N" là mất lối đọc tên người bị giấu', () => {
    expect(monthCellLinesFor(40)).toBe(2)
    expect(monthCellLinesFor(0)).toBe(2)
    expect(monthCellLinesFor(-100)).toBe(2)
  })

  it('ô rất cao vẫn ra số dòng hữu hạn, không nhảy loạn', () => {
    expect(monthCellLinesFor(300)).toBe(11)
  })
})

describe('monthCellDayLabel', () => {
  it('ngày 1 kèm tên tháng — hàng cuối của lưới bày 1…11 của tháng SAU', () => {
    expect(monthCellDayLabel(new Date(2026, 9, 1), false)).toBe('1 thg 10')
    expect(monthCellDayLabel(new Date(2027, 0, 1), false)).toBe('1 thg 1')
  })

  it('ngày thường chỉ có con số', () => {
    expect(monthCellDayLabel(new Date(2026, 9, 15), false)).toBe('15')
  })

  it('HÔM NAY thì bỏ tên tháng — nhãn nằm trong vòng tròn 24px', () => {
    //  «1 thg 10» nhét vào vòng tròn thì nó méo thành viên thuốc.
    expect(monthCellDayLabel(new Date(2026, 9, 1), true)).toBe('1')
  })
})
