import type { AxiosError } from 'axios'
import { useState } from 'react'

import { extractErrorMessage } from '@/core/api'
import { PageContainer } from '@/shared/ui/page-container'
import { toDateInputValue } from '@/shared/utils/format-date'

import { useReportAnalytics } from '../hooks/use-report-analytics'
import { useReportFilters } from '../hooks/use-report-filters'
import type { ReportMetricValues, ReportPageConfig, ReportPeriod } from '../types/report-analytics'
import { ReportBreakdownCharts } from '../components/report-breakdown-charts'
import { ReportErrorCard } from '../components/report-error-card'
import { ReportExportButton } from '../components/report-export-button'
import { ReportFiltersBar } from '../components/report-filters-bar'
import { ReportGroupedTable } from '../components/report-grouped-table'
import { ReportNotes } from '../components/report-notes'
import { ReportKpiRow } from '../components/report-kpi-row'
import { ReportPageHeader } from '../components/report-page-header'
import { ReportPeriodEmptyState } from '../components/report-period-empty-state'
import { ReportTrendChart } from '../components/report-trend-chart'

interface ReportAnalyticsPageProps {
  config: ReportPageConfig
}

const EMPTY_METRICS: ReportMetricValues = {}

function buildExportFilename(slug: string, period?: ReportPeriod): string {
  const from = period?.date_from ?? toDateInputValue(new Date())
  const to = period?.date_to ?? toDateInputValue(new Date())
  return `bao-cao-${slug}-${from}-${to}.xlsx`
}

/**
 * "Xem bảng chi tiết" phải mở ĐÚNG kỳ đang xem trên bảng gốc. Bảng gốc chỉ hiểu
 * `year` (bộ lọc năm cũ, xem `purchase-report-page.tsx`/`pr-lines-report-page.tsx`)
 * hoặc `date_from`/`date_to` (`survey-progress-page.tsx`/`purchase-progress-page.tsx`/
 * `survey-report-page.tsx`) — gửi cả ba, trang nào hiểu tham số nào thì tự đọc,
 * tham số lạ bị bỏ qua chứ không lỗi. Chưa có lượt gọi nào về thì giữ nguyên
 * đường trơn (không tham số).
 */
function buildSourceHref(
  sourcePath: string | undefined,
  period?: ReportPeriod,
): string | undefined {
  if (!sourcePath) return undefined
  if (!period) return sourcePath
  const year = period.date_to.slice(0, 4)
  const params = new URLSearchParams({ year, date_from: period.date_from, date_to: period.date_to })
  return `${sourcePath}?${params.toString()}`
}

/**
 * Trang báo cáo Haravan CHUNG — mỗi báo cáo mới chỉ cần khai một
 * `ReportPageConfig` (~30 dòng) + một dòng danh mục, không viết thêm trang
 * riêng. Bố cục cố định: thanh lọc kỳ → thẻ KPI → biểu đồ xu hướng → breakdown
 * phụ (tùy chọn) → bảng "Xem theo".
 *
 * Toàn bộ số liệu/nhãn đọc từ `meta` + response của `config.endpoint` — trang
 * này không tự tính hay tự dịch mã trạng thái nào (backend là nguồn duy nhất).
 */
export function ReportAnalyticsPage({ config }: ReportAnalyticsPageProps) {
  const filters = useReportFilters({
    defaultGroupBy: config.defaultGroupBy,
    defaultPreset: config.defaultPreset,
  })
  const [chartMetric, setChartMetric] = useState(config.chartMetric)
  const { data, isLoading, isError, error } = useReportAnalytics(
    config.endpoint,
    filters.queryParams,
  )

  const meta = data?.meta ?? { metrics: [], dimensions: [], group_by: config.defaultGroupBy }
  const totals = data?.totals ?? { current: EMPTY_METRICS, compare: null }
  const trend = data?.trend ?? []
  const groups = data?.groups ?? []
  const notes = data?.notes ?? []
  //  Kỳ không phát sinh gì: mọi chỉ số THEO KỲ ở dòng Tổng bằng 0/`null`. Bỏ qua
  //  chỉ số `snapshot` (công nợ còn lại…) — số dư vẫn còn dù kỳ này chẳng mua gì.
  const isPeriodEmpty =
    !!data && meta.metrics.filter((m) => !m.snapshot).every((m) => !totals.current[m.key])

  //  M6 — một đường `/summary` hỏng (403 `group_by` không có quyền, vd link
  //  chia sẻ `?group_by=supplier`; 422 tham số kỳ gõ tay sai) KHÔNG được để
  //  trang kẹt cứng. `Đặt lại bộ lọc` luôn đưa "Xem theo" về mặc định của
  //  trang; 422 (kỳ sai) đưa CẢ kỳ về mặc định — 403 do quyền thì kỳ không có
  //  lỗi gì, giữ nguyên để không mất ngữ cảnh người dùng đang xem.
  const errorStatus = isError ? (error as AxiosError | null)?.response?.status : undefined
  const handleResetFilters = () =>
    filters.resetFilters({ groupBy: true, period: errorStatus === 422 })

  return (
    <PageContainer>
      <ReportPageHeader
        title={config.title}
        description={config.description}
        sourcePath={buildSourceHref(config.sourcePath, data?.period)}
        exportButton={
          config.exportEndpoint && (
            <ReportExportButton
              endpoint={config.exportEndpoint}
              entity={config.entity}
              params={filters.queryParams}
              filename={buildExportFilename(config.slug, data?.period)}
            />
          )
        }
      />

      <div className="flex flex-col gap-4">
        <ReportFiltersBar
          filters={filters}
          period={data?.period}
          hideCompany={config.hideCompany}
          ExtraFilters={config.extraFilters}
        />

        {/*  M6 — lỗi thay HẲN khối KPI/biểu đồ/bảng thay vì đứng cạnh chúng:
             mấy khối đó rỗng lúc `isError` (không có `data`) nên để chúng đứng
             cạnh câu lỗi chỉ tổ trông như "đã tải xong nhưng chưa có số liệu",
             chưa kể vẫn giữ nguyên `group_by` hỏng trên URL cho lần tải lại kế
             tiếp (đúng cái kẹt cứng cần sửa). */}
        {isError ? (
          <ReportErrorCard
            message={extractErrorMessage(error) || 'Không tải được số liệu báo cáo.'}
            onReset={handleResetFilters}
          />
        ) : (
          <>
            {/*  `notes` mang các lưu ý tính toán quan trọng (nguồn dữ liệu gộp
                 hai cột ngày khác nhau, số công nợ là XẤP XỈ…) — backend là
                 nguồn DUY NHẤT, tầng này hiện nguyên văn (gấp sẵn, bấm để mở). */}
            <ReportNotes notes={notes} />

            <ReportKpiRow
              meta={meta}
              kpis={config.kpis}
              totals={totals}
              trend={trend}
              compareMode={filters.compare}
              selectedMetric={chartMetric}
              onSelectMetric={setChartMetric}
              isLoading={isLoading}
            />

            {isPeriodEmpty ? (
              <ReportPeriodEmptyState
                period={data?.period}
                onViewFullYear={() =>
                  filters.applyPeriod({
                    preset: 'this_year',
                    from: '',
                    to: '',
                    compare: filters.compare,
                  })
                }
              />
            ) : (
              <>
                <ReportTrendChart
                  meta={meta}
                  trend={trend}
                  metric={chartMetric}
                  compareMode={filters.compare}
                  isLoading={isLoading}
                />

                {config.breakdowns && config.breakdowns.length > 0 && (
                  <ReportBreakdownCharts
                    breakdowns={data?.breakdowns}
                    meta={data?.meta}
                    config={config.breakdowns}
                    isLoading={isLoading}
                  />
                )}

                <ReportGroupedTable
                  meta={meta}
                  kpis={config.kpis}
                  totals={totals}
                  groups={groups}
                  compare={filters.compare}
                  groupBy={filters.groupBy}
                  onGroupByChange={filters.setGroupBy}
                  isLoading={isLoading}
                  isError={isError}
                  //  `.v4` — mặc định chỉ hiện cột `kpis`, còn lại `defaultHidden`
                  //  (`docs/ui/table.md` §4: đổi mặc định cột thì phải đổi khóa mới,
                  //  không thì bố cục CŨ trong localStorage thắng, không ai thấy gì đổi).
                  storageKey={`report.${config.slug}.v4`}
                />
              </>
            )}
          </>
        )}
      </div>
    </PageContainer>
  )
}
