import { appRoutes } from '@/shared/constants/app-routes'
import { CHART_NEUTRAL, CHART_SEVERITY, ChartCard } from '@/shared/ui/chart'
import { DonutChart } from '@/shared/ui/donut-chart'
import { HorizontalBarChart } from '@/shared/ui/horizontal-bar-chart'
import { PageContainer } from '@/shared/ui/page-container'
import { formatMoney } from '@/shared/utils/format-money'

import { KpiTrendCard } from '../components/kpi-trend-card'
import { ReportChartPageHeader } from '../components/report-chart-page-header'
import { StackedMonthColumnChart } from '../components/stacked-month-column-chart'
import { useReportPeriod } from '../hooks/use-report-period'
import { useSurveyReportSummary } from '../hooks/use-report-summaries'
import { fillYearMonths, topBars } from '../utils/chart-series'
import { ratePercent } from '../utils/report-period-comparison'

const TOP_N = 8

/**
 * Màu của bốn nhãn duyệt — MANG NGHĨA nên đi theo thang mức độ, gán theo NHÃN
 * (không theo thứ hạng). Nhãn lạ backend trả thêm rơi về xám trung tính.
 */
const APPROVE_COLORS: Record<string, string> = {
  'Đã duyệt': CHART_SEVERITY[0],
  'Thiếu thông tin': CHART_SEVERITY[1],
  'Không duyệt': CHART_SEVERITY[3],
  'Chờ duyệt': CHART_NEUTRAL,
}

/**
 * Báo cáo khảo sát — bản BIỂU ĐỒ. Trả lời: khảo sát được bao nhiêu NCC / sản
 * phẩm, duyệt được bao nhiêu, NSPT nào làm nhiều. Bảng từng dòng vẫn ở Thu mua.
 *
 * ⚠️ Nguồn này KHÔNG lọc theo công ty ở backend nên trang ẩn ô Công ty; năm dịch
 * sang khoảng ngày liên hệ của dòng.
 */
export function SurveyReportChartPage() {
  const period = useReportPeriod()
  const { data, isLoading } = useSurveyReportSummary({ year: String(period.year) })
  const total = data?.total ?? 0
  const approved = data?.by_approve.find((a) => a.state === 'Đã duyệt')?.lines ?? 0
  const approveRate = ratePercent(approved, total)

  const months = fillYearMonths(period.year, data?.by_month ?? [], ['supplier', 'product'] as const)
  const approveSlices = (data?.by_approve ?? [])
    .filter((a) => a.lines > 0)
    .map((a) => ({ label: a.state, value: a.lines, color: APPROVE_COLORS[a.state] ?? CHART_NEUTRAL }))
  const byNspt = topBars(data?.by_nspt ?? [], TOP_N, (n) => n.key, (n) => n.lines)
  const byGroup = topBars(data?.by_item_group ?? [], TOP_N, (g) => g.key, (g) => g.lines)

  return (
    <PageContainer>
      <ReportChartPageHeader
        title="Báo cáo khảo sát"
        description="Dòng khảo sát NCC và sản phẩm, kết quả duyệt — theo ngày liên hệ trong năm."
        period={period}
        tablePath={appRoutes.procurement.surveyReport}
        hideCompany
      />

      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
          <KpiTrendCard label="Dòng khảo sát" value={formatMoney(total)} loading={isLoading} />
          <KpiTrendCard
            label="Khảo sát NCC"
            value={formatMoney(data?.by_kind.supplier ?? 0)}
            loading={isLoading}
          />
          <KpiTrendCard
            label="Khảo sát sản phẩm"
            value={formatMoney(data?.by_kind.product ?? 0)}
            loading={isLoading}
          />
          <KpiTrendCard
            label="Tỷ lệ được duyệt"
            value={approveRate === null ? '—' : `${Math.round(approveRate)}%`}
            hint={`${formatMoney(approved)} / ${formatMoney(total)} dòng`}
            loading={isLoading}
          />
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <ChartCard
            title="Dòng khảo sát theo tháng"
            description="Theo ngày liên hệ (lùi về ngày nhận phiếu)."
            loading={isLoading}
            isEmpty={months.every((m) => m.supplier === 0 && m.product === 0)}
            emptyLabel="Kỳ này chưa có dòng khảo sát."
            className="lg:col-span-2"
          >
            <StackedMonthColumnChart
              data={months}
              unit="dòng"
              //  Dải phân loại theo thứ tự cố định (chart-1, chart-2). KHÔNG dùng
              //  xanh lá: nó đứng cạnh lát «Đã duyệt» xanh lá của vòng bên phải và
              //  đọc ra nghĩa «đã duyệt».
              series={[
                { key: 'product', label: 'Khảo sát sản phẩm', color: 'var(--chart-1)' },
                { key: 'supplier', label: 'Khảo sát NCC', color: 'var(--chart-2)' },
              ]}
            />
          </ChartCard>
          <ChartCard
            title="Kết quả duyệt"
            description="Trạng thái duyệt của từng dòng."
            loading={isLoading}
            isEmpty={approveSlices.length === 0}
          >
            <DonutChart centerLabel="dòng" data={approveSlices} />
          </ChartCard>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <ChartCard
            title="Theo nhân sự phụ trách"
            description="Số dòng khảo sát mỗi NSPT thực hiện."
            loading={isLoading}
            isEmpty={byNspt.length === 0}
          >
            <HorizontalBarChart data={byNspt} unit="dòng" />
          </ChartCard>
          <ChartCard
            title="Theo nhóm hàng"
            description="Số dòng khảo sát của từng phân loại."
            loading={isLoading}
            isEmpty={byGroup.length === 0}
          >
            <HorizontalBarChart data={byGroup} unit="dòng" />
          </ChartCard>
        </div>
      </div>
    </PageContainer>
  )
}
