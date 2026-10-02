import { BarChart3, FileText } from 'lucide-react'
import { describe, expect, it } from 'vitest'

import type { ReportCatalogEntry } from '../config/report-catalog'
import { filterVisibleReports } from './filter-visible-reports'

function buildReport(overrides: Partial<ReportCatalogEntry> = {}): ReportCatalogEntry {
  return {
    label: 'Báo cáo thử',
    description: '',
    path: '/report/test',
    sourcePath: '/procurement/test',
    icon: BarChart3,
    key: 1,
    entity: 'report',
    group: 'Thu mua',
    endpoint: '/api/reports/test/summary',
    overviewKpis: ['spend'],
    load: async () => () => null,
    ...overrides,
  }
}

describe('filterVisibleReports — gác KÉP entity + reportKeys', () => {
  it('ẩn khi reportKeys là undefined, dù entity đọc được — hồ sơ cũ trước khi trường này ra đời', () => {
    const r = buildReport()
    expect(filterVisibleReports([r], () => true, undefined)).toEqual([])
  })

  it('ẩn khi reportKeys là mảng rỗng — chưa được gán báo cáo nào', () => {
    const r = buildReport()
    expect(filterVisibleReports([r], () => true, [])).toEqual([])
  })

  it('ẩn khi reportKeys có khóa khác (khóa lạ 999), không khớp key của báo cáo', () => {
    const r = buildReport({ key: 1 })
    expect(filterVisibleReports([r], () => true, [999])).toEqual([])
  })

  it('ẩn khi được gán đúng key nhưng KHÔNG đọc được entity — gác kép, thiếu một là đóng', () => {
    const r = buildReport({ key: 1 })
    expect(filterVisibleReports([r], () => false, [1])).toEqual([])
  })

  it('hiện khi CẢ HAI điều kiện đạt: đọc được entity VÀ được gán đúng key', () => {
    const r = buildReport({ key: 1 })
    expect(filterVisibleReports([r], () => true, [1])).toEqual([r])
  })

  it('key trùng lặp trong reportKeys không làm báo cáo xuất hiện nhiều lần', () => {
    const r = buildReport({ key: 1 })
    expect(filterVisibleReports([r], () => true, [1, 1, 1])).toEqual([r])
  })

  it('mỗi báo cáo tự xét theo ĐÚNG key của nó — gán báo cáo A không mở báo cáo B', () => {
    const a = buildReport({ key: 1, path: '/report/a', entity: 'report' })
    const b = buildReport({ key: 2, path: '/report/b', entity: 'report' })
    expect(filterVisibleReports([a, b], () => true, [1])).toEqual([a])
  })

  it('danh mục rỗng trả về rỗng, không ném lỗi', () => {
    expect(filterVisibleReports([], () => true, [1, 2, 3])).toEqual([])
  })

  it('entity khác nhau trên hai báo cáo cùng key: chỉ báo cáo đọc được entity mới qua', () => {
    const a = buildReport({ key: 5, path: '/report/a', entity: 'report' })
    const b = buildReport({ key: 5, path: '/report/b', entity: 'survey' })
    const can = (entity: string) => entity === 'survey'
    expect(filterVisibleReports([a, b], can, [5])).toEqual([b])
  })

  it('không đụng danh mục thật khi lọc rỗng — dùng icon khác để tránh trùng lặp chi tiết', () => {
    const r = buildReport({ icon: FileText, key: 7 })
    expect(filterVisibleReports([r], () => true, [7])[0]?.icon).toBe(FileText)
  })
})
