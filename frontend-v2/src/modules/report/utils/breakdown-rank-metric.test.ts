import { describe, expect, it } from 'vitest'

import type { ReportMeta } from '../types/report-analytics'
import { describeBreakdownRank } from './breakdown-rank-metric'

const META: ReportMeta = {
  metrics: [
    { key: 'po_count', label: 'Số ĐMH', kind: 'int', good: null, helper: false, snapshot: false },
    {
      key: 'order_value',
      label: 'Giá trị đặt hàng',
      kind: 'money',
      good: null,
      helper: false,
      snapshot: false,
    },
  ],
  dimensions: [],
  group_by: 'department',
  rank_by: 'order_value',
}

describe('describeBreakdownRank', () => {
  it('ghi rõ khối Top xếp theo chỉ số nào và định dạng tiền rút gọn', () => {
    const { description, formatValue } = describeBreakdownRank(META)
    expect(description).toBe('Theo giá trị đặt hàng')
    expect(formatValue?.(1_200_000_000)).toMatch(/tỷ đ$/)
  })

  it('chưa có meta hoặc rank_by lạ thì không bịa mô tả', () => {
    expect(describeBreakdownRank(undefined)).toEqual({})
    expect(describeBreakdownRank({ ...META, rank_by: 'khong_co' })).toEqual({})
  })
})
