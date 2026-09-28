import { describe, expect, it } from 'vitest'

import { PROCUREMENT_REPORT_CATALOG } from './report-catalog-procurement'

//  Ràng buộc RIÊNG của nhóm Thu mua (P03) — `report-catalog.test.ts` đã canh
//  luật entity/route chung cho MỌI nhóm; ở đây chỉ kiểm phần dữ liệu chỉ có ý
//  nghĩa với nhóm này (đường `/summary` + KPI Tổng quan).
describe('PROCUREMENT_REPORT_CATALOG', () => {
  it('has exactly the five reports migrated in P03', () => {
    expect(PROCUREMENT_REPORT_CATALOG).toHaveLength(5)
  })

  it('every report keeps a distinct /summary endpoint under /api/', () => {
    const endpoints = PROCUREMENT_REPORT_CATALOG.map((r) => r.endpoint)
    expect(new Set(endpoints).size).toBe(endpoints.length)
    for (const endpoint of endpoints) {
      expect(endpoint.startsWith('/api/')).toBe(true)
      expect(endpoint.endsWith('/summary')).toBe(true)
    }
  })

  //  Trang Tổng quan gọi THẲNG `endpoint` (không nạp `load()`) — quên khai là
  //  báo cáo đó âm thầm biến mất khỏi dải KPI, không lỗi nào bắn ra để biết.
  it('every overviewKpis entry has 1-2 metric keys, no duplicates', () => {
    for (const report of PROCUREMENT_REPORT_CATALOG) {
      expect(report.overviewKpis.length).toBeGreaterThanOrEqual(1)
      expect(report.overviewKpis.length).toBeLessThanOrEqual(2)
      expect(new Set(report.overviewKpis).size).toBe(report.overviewKpis.length)
    }
  })

  it('all five reports belong to the Thu mua group for now', () => {
    expect(PROCUREMENT_REPORT_CATALOG.every((r) => r.group === 'Thu mua')).toBe(true)
  })
})
