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
    {
      key: 'overdue_tasks',
      label: 'Quá hạn',
      kind: 'int',
      good: 'down',
      helper: false,
      snapshot: true,
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

  //  H3 (review 01/10/2026) — trang có nhiều khối "Top" xếp theo nhiều chỉ số
  //  khác nhau (vd work-report-page.tsx) không thể dùng chung một `meta.rank_by`.
  describe('rankMetric overrides meta.rank_by for one specific breakdown', () => {
    it('describes and formats using the overriding metric, not meta.rank_by', () => {
      const { description, formatValue } = describeBreakdownRank(META, 'overdue_tasks')
      expect(description).toBe('Theo quá hạn')
      expect(formatValue?.(7)).not.toMatch(/tỷ đ$/)   // "int", không phải "money"
    })

    it('falls back to meta.rank_by when rankMetric is undefined', () => {
      //  `formatValue` là một CLOSURE MỚI mỗi lần gọi — so `toEqual` cả object sẽ
      //  luôn trượt vì hai hàm không bao giờ cùng tham chiếu. So nội dung thật:
      //  mô tả + kết quả định dạng của cùng một giá trị.
      const withoutOverride = describeBreakdownRank(META, undefined)
      const baseline = describeBreakdownRank(META)
      expect(withoutOverride.description).toBe(baseline.description)
      expect(withoutOverride.formatValue?.(1_200_000_000)).toBe(baseline.formatValue?.(1_200_000_000))
    })

    it('an unknown rankMetric key yields no description, same as an unknown rank_by', () => {
      expect(describeBreakdownRank(META, 'khong_ton_tai')).toEqual({})
    })
  })
})
