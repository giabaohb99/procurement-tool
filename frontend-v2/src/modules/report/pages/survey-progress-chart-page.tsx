import { appRoutes } from '@/shared/constants/app-routes'
import { ChartCard } from '@/shared/ui/chart'
import { HorizontalBarChart } from '@/shared/ui/horizontal-bar-chart'
import { PageContainer } from '@/shared/ui/page-container'
import { formatMoney } from '@/shared/utils/format-money'

import { KpiTrendCard } from '../components/kpi-trend-card'
import { ReportChartPageHeader } from '../components/report-chart-page-header'
import { StackedMonthColumnChart } from '../components/stacked-month-column-chart'
import { useReportPeriod } from '../hooks/use-report-period'
import { useSurveyProgressSummary } from '../hooks/use-report-summaries'
import { fillYearMonths, topBars } from '../utils/chart-series'

const TOP_N = 8

/**
 * Tiến độ báo giá — bản BIỂU ĐỒ. Trả lời: còn bao nhiêu dòng yêu cầu báo giá
 * đang mở, trễ hạn ở đâu, NSTM nào đang ôm nhiều. Bảng từng dòng vẫn ở Thu mua.
 *
 * «Tiến độ dòng» là cột TÍNH do backend dựng (không lưu DB), đã xếp sẵn theo
 * chuỗi tiến độ — giữ nguyên thứ tự đó, đừng sắp lại theo độ lớn.
 */
export function SurveyProgressChartPage() {
  const period = useReportPeriod()
  const { data, isLoading } = useSurveyProgressSummary({
    year: String(period.year),
    company_id: period.company,
  })
  const t = data?.total ?? { lines: 0, late: 0, answered: 0, open: 0, avg_handling_days: null }

  const months = fillYearMonths(period.year, data?.by_month ?? [], ['lines', 'late'] as const).map(
    (m) => ({ label: m.label, onTime: Math.max(0, m.lines - m.late), late: m.late }),
  )
  const states = (data?.by_state ?? []).map((s) => ({ label: s.state, value: s.lines }))
  const openByAssignee = topBars(
    data?.by_assignee ?? [],
    TOP_N,
    (a) => a.name || '(Chưa giao NSTM)',
    (a) => a.open,
  )
  const byGroup = topBars(data?.by_item_group ?? [], TOP_N, (g) => g.key, (g) => g.lines)

  return (
    <PageContainer>
      <ReportChartPageHeader
        title="Tiến độ báo giá"
        description="Dòng yêu cầu báo giá đang mở, trễ hạn, NSTM đang xử lý — theo phiếu lập trong năm."
        period={period}
        tablePath={appRoutes.procurement.surveyProgress}
      />

      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
          <KpiTrendCard
            label="Dòng yêu cầu báo giá"
            value={formatMoney(t.lines)}
            hint={`Đã trả kết quả ${formatMoney(t.answered)}`}
            loading={isLoading}
          />
          <KpiTrendCard
            label="Đang mở"
            value={formatMoney(t.open)}
            hint="Chưa tạo YCMH, chưa hoàn thành"
            loading={isLoading}
          />
          <KpiTrendCard
            label="Trễ hạn"
            value={formatMoney(t.late)}
            hint={t.late ? 'Trả sau hạn hoặc đã quá hạn' : 'Không có dòng trễ'}
            tone={t.late ? 'danger' : undefined}
            loading={isLoading}
          />
          <KpiTrendCard
            label="Số ngày xử lý TB"
            value={
              t.avg_handling_days === null
                ? '—'
                : `${t.avg_handling_days.toLocaleString('vi-VN')} ngày`
            }
            hint="Từ tiếp nhận tới trả kết quả"
            loading={isLoading}
          />
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <ChartCard
            title="Dòng yêu cầu theo tháng"
            description="Theo ngày lập phiếu — phần cam là dòng trễ hạn."
            loading={isLoading}
            isEmpty={months.every((m) => m.onTime === 0 && m.late === 0)}
            emptyLabel="Kỳ này chưa có yêu cầu báo giá."
            className="lg:col-span-2"
          >
            <StackedMonthColumnChart
              data={months}
              unit="dòng"
              series={[
                { key: 'onTime', label: 'Không trễ', color: 'var(--chart-1)' },
                { key: 'late', label: 'Trễ hạn', color: 'var(--chart-2)' },
              ]}
            />
          </ChartCard>
          <ChartCard
            title="Tiến độ dòng"
            description="Xếp theo chuỗi xử lý."
            loading={isLoading}
            isEmpty={states.length === 0}
          >
            <HorizontalBarChart data={states} unit="dòng" />
          </ChartCard>
        </div>

        <div className="grid gap-4 lg:grid-cols-2">
          <ChartCard
            title="Dòng đang mở theo NSTM"
            description="Ai đang giữ nhiều việc báo giá nhất."
            loading={isLoading}
            isEmpty={openByAssignee.length === 0}
            emptyLabel="Không còn dòng nào đang mở."
          >
            <HorizontalBarChart data={openByAssignee} unit="dòng" color="var(--chart-2)" />
          </ChartCard>
          <ChartCard
            title="Theo nhóm hàng"
            description="Số dòng yêu cầu của từng phân loại."
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
