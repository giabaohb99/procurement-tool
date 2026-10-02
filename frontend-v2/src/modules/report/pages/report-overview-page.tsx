import { useState } from 'react'

import { useNavContext, usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'

import { ReportCatalogList } from '../components/report-catalog-list'
import { ReportFiltersBar } from '../components/report-filters-bar'
import {
  ReportOverviewKpiStrip,
  type OverviewMetricSelection,
} from '../components/report-overview-kpi-strip'
import { ReportOverviewTopLists } from '../components/report-overview-top-lists'
import { ReportTrendChart } from '../components/report-trend-chart'
import { REPORT_CATALOG } from '../config/report-catalog'
import { useReportFilters } from '../hooks/use-report-filters'
import { useReportOverview, type ReportOverviewEntry } from '../hooks/use-report-overview'
import type { ReportMeta } from '../types/report-analytics'
import { filterVisibleReports } from '../utils/filter-visible-reports'

const EMPTY_META: ReportMeta = { metrics: [], dimensions: [], group_by: 'none' }

/**
 * Chỉ số mặc định khi mở trang / chưa bấm thẻ nào — chỉ số ĐẦU của báo cáo nạp
 * xong SỚM NHẤT mà thật sự vẽ được xu hướng: bỏ qua `helper` (không hiện) và
 * `snapshot` (không có `trend[]`, chọn nó làm mặc định thì biểu đồ mở trang ra
 * đã trống trơn).
 */
function defaultSelection(entry: ReportOverviewEntry | undefined): OverviewMetricSelection | null {
  if (!entry?.data) return null
  const metricKey = entry.report.overviewKpis.find((key) => {
    const m = entry.data?.meta.metrics.find((mm) => mm.key === key)
    return m && !m.helper && !m.snapshot
  })
  const metric = entry.data.meta.metrics.find((m) => m.key === metricKey)
  if (!metric) return null
  return {
    endpoint: entry.report.endpoint,
    metric: metric.key,
    label: metric.label,
    kind: metric.kind,
  }
}

/**
 * Tổng quan phân hệ Báo cáo — bố cục kiểu Haravan: thanh lọc kỳ + so sánh +
 * công ty ở đầu → dải "Chỉ số chính" gom theo phân hệ (bấm thẻ đổi biểu đồ xu
 * hướng) → biểu đồ xu hướng của chỉ số đang chọn → Top lists (NCC/NSPT/bộ
 * phận/nhóm hàng từ Báo cáo mua hàng) → danh sách báo cáo theo nhóm.
 *
 * Mỗi khối tự gác bằng quyền của NGUỒN dữ liệu của nó (`can(entity,'read')`
 * trong `useReportOverview`) — không có báo cáo nào đọc được thì dải KPI/biểu
 * đồ/Top lists tự ẩn, chỉ còn thanh lọc và danh sách báo cáo (khi đó cũng rỗng).
 */
export function ReportOverviewPage() {
  const { can } = usePermission()
  const { reportKeys } = useNavContext()
  const filters = useReportFilters({ defaultGroupBy: 'none' })
  const entries = useReportOverview(filters.queryParams)
  const [selected, setSelected] = useState<OverviewMetricSelection | null>(null)

  const firstReady = entries.find((e) => e.data)
  const active = selected ?? defaultSelection(firstReady)
  const activeEntry = active
    ? entries.find((e) => e.report.endpoint === active.endpoint)
    : undefined
  const procurementEntry = entries.find((e) => e.report.path === appRoutes.report.purchaseReport)

  const reports = filterVisibleReports(REPORT_CATALOG, can, reportKeys)

  return (
    <PageContainer>
      <PageHeader
        title="Báo cáo"
        description={
          <span className="max-md:hidden">Số liệu các phân hệ trong một kỳ, so với kỳ trước.</span>
        }
      />
      <div className="flex flex-col gap-6">
        <ReportFiltersBar filters={filters} period={firstReady?.data?.period} />

        {entries.length > 0 && (
          <>
            <ReportOverviewKpiStrip
              entries={entries}
              compareMode={filters.compare}
              selected={active}
              onSelect={setSelected}
            />

            {active && (
              <ReportTrendChart
                meta={activeEntry?.data?.meta ?? EMPTY_META}
                trend={activeEntry?.data?.trend ?? []}
                metric={active.metric}
                compareMode={filters.compare}
                isLoading={activeEntry?.isLoading ?? entries.some((e) => e.isLoading)}
              />
            )}

            {/*  Không đọc được Báo cáo mua hàng (`report.read`) — KHÔNG hiện
                khối "Top" rỗng, dù báo cáo khác trong `entries` đọc được
                (L6/item 4): rỗng-vì-thiếu-quyền và rỗng-vì-chưa-có-số-liệu
                trông giống hệt nhau, dễ đọc nhầm là lỗi tải. */}
            {procurementEntry && (
              <ReportOverviewTopLists
                data={procurementEntry.data}
                isLoading={procurementEntry.isLoading}
              />
            )}
          </>
        )}

        <ReportCatalogList reports={reports} />
      </div>
    </PageContainer>
  )
}
