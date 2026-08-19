import { describe, expect, it } from 'vitest'

import {
  isWarnRow,
  metricValue,
  nextSort,
  shortMoney,
  spendSeries,
  type MatrixRow,
} from './purchase-report'

const row: MatrixRow = {
  key: 'CÔNG TY TNHH ABC',
  trans: 12,
  late: 5,
  rate: 41.67,
  m: {
    '2026-07': { trans: 4, late: 0, rate: 0 },
    '2026-08': { trans: 8, late: 5, rate: 62.5 },
  },
}

describe('metricValue', () => {
  it('đọc tổng cả năm khi kỳ là "all"', () => {
    expect(metricValue(row, 'trans', 'all')).toBe(12)
    expect(metricValue(row, 'rate', 'all')).toBe(41.67)
  })

  it('đọc số của đúng tháng khi kỳ là YYYY-MM', () => {
    expect(metricValue(row, 'trans', '2026-08')).toBe(8)
    expect(metricValue(row, 'rate', '2026-07')).toBe(0)
  })

  it('trả 0 cho tháng không phát sinh thay vì để ô trống', () => {
    // Backend chỉ trả tháng CÓ số. Trước đây trả undefined thì ô hiện rỗng,
    // người đọc tưởng bảng chưa tải xong.
    expect(metricValue(row, 'trans', '2026-01')).toBe(0)
    expect(metricValue({ key: 'X' }, 'trans', 'all')).toBe(0)
  })
})

describe('isWarnRow', () => {
  it('chỉ tô cảnh báo khi tỷ lệ vượt 30%', () => {
    expect(isWarnRow(row, 'all', 'rate')).toBe(true)
    expect(isWarnRow(row, '2026-07', 'rate')).toBe(false)
  })

  it('không tô gì khi bảng không khai cột cảnh báo', () => {
    expect(isWarnRow(row, 'all')).toBe(false)
  })
})

describe('nextSort', () => {
  it('bấm cột mới thì sắp giảm dần trước — báo cáo hay đọc từ cái lớn nhất', () => {
    expect(nextSort(null, 'trans')).toEqual({ key: 'trans', dir: 'desc' })
    expect(nextSort({ key: 'late', dir: 'asc' }, 'trans')).toEqual({ key: 'trans', dir: 'desc' })
  })

  it('bấm lại cùng cột: giảm -> tăng -> bỏ sắp xếp', () => {
    expect(nextSort({ key: 'trans', dir: 'desc' }, 'trans')).toEqual({
      key: 'trans',
      dir: 'asc',
    })
    expect(nextSort({ key: 'trans', dir: 'asc' }, 'trans')).toBeNull()
  })
})

describe('shortMoney', () => {
  it('rút gọn theo tỷ / triệu / nghìn', () => {
    expect(shortMoney(1_500_000_000)).toBe('1.5 tỷ')
    expect(shortMoney(2_000_000_000)).toBe('2 tỷ')
    expect(shortMoney(286_000_000)).toBe('286 tr')
    expect(shortMoney(12_000)).toBe('12k')
  })

  it('giữ nguyên số nhỏ hơn nghìn', () => {
    expect(shortMoney(999)).toBe('999')
    expect(shortMoney(0)).toBe('0')
  })
})

describe('spendSeries', () => {
  const months = [
    { key: '2026-01', label: '01/2026' },
    { key: '2026-02', label: '02/2026' },
    { key: '2026-03', label: '03/2026' },
  ]

  it('giữ đủ mọi tháng của kỳ, tháng chưa phát sinh để 0', () => {
    const series = spendSeries(months, [{ month: '2026-02', amount: 5_000_000 }])

    expect(series.map((bar) => bar.value)).toEqual([0, 5_000_000, 0])
    expect(series.map((bar) => bar.key)).toEqual(['2026-01', '2026-02', '2026-03'])
  })

  it('rút nhãn cột còn hai chữ số tháng cho khỏi chồng chữ', () => {
    expect(spendSeries(months, []).map((bar) => bar.label)).toEqual(['01', '02', '03'])
  })

  it('không sắp lại thứ tự thời gian theo độ lớn', () => {
    const series = spendSeries(months, [
      { month: '2026-03', amount: 9 },
      { month: '2026-01', amount: 1 },
    ])

    expect(series.map((bar) => bar.key)).toEqual(['2026-01', '2026-02', '2026-03'])
  })
})
