import { shortMoney } from '@/modules/procurement/types/purchase-report'
import { appRoutes } from '@/shared/constants/app-routes'
import { ChartCard } from '@/shared/ui/chart'
import { HorizontalBarChart } from '@/shared/ui/horizontal-bar-chart'
import { PageContainer } from '@/shared/ui/page-container'
import { formatMoney } from '@/shared/utils/format-money'

import { KpiTrendCard } from '../components/kpi-trend-card'
import { ReportChartPageHeader } from '../components/report-chart-page-header'
import { StackedMonthColumnChart } from '../components/stacked-month-column-chart'
import { useReportPeriod } from '../hooks/use-report-period'
import { usePrLinesSummary } from '../hooks/use-report-summaries'
import { fillPrLinesMonths, labelAssignee, orderPrLineStatuses } from '../utils/pr-lines-chart-data'
import { ratePercent } from '../utils/report-period-comparison'

/** Số hạng mục trên biểu đồ theo bộ phận / nhóm hàng / NSTM. */
const TOP_N = 8

/**
 * Chi tiết YC mua hàng — bản BIỂU ĐỒ của phân hệ Báo cáo.
 *
 * Bảng theo từng dòng vẫn ở Thu mua (`/procurement/pr-lines-report`): người mua
 * hàng dùng nó để soi TỪNG mã chưa đặt, việc đó biểu đồ không thay được. Trang
 * này trả lời câu hỏi của người quản lý: còn bao nhiêu dòng chưa đặt, dồn ở
 * tháng nào, ai đang ôm — rồi bấm «Xem bảng chi tiết» để đi tiếp.
 *
 * Số liệu từ `/api/reports/pr-lines/summary`: cùng bộ lọc + scope phòng ban với
 * bảng, và mọi khối (trừ «Tiến độ») đã BỎ dòng hủy.
 */
export function PrLinesChartPage() {
  const period = useReportPeriod()
  const { data, isLoading } = usePrLinesSummary({
    year: String(period.year),
    company_id: period.company,
  })
  const total = data?.total ?? { lines: 0, idle_lines: 0, amount: 0, idle_amount: 0 }
  const handledRate = ratePercent(total.lines - total.idle_lines, total.lines)

  const months = fillPrLinesMonths(period.year, data?.by_month ?? [])
  const statuses = orderPrLineStatuses(data?.by_line_status ?? [])
  const backlog = (data?.by_assignee ?? [])
    .filter((a) => a.idle_lines > 0)
    .slice(0, TOP_N)
    .map((a) => ({ label: labelAssignee(a), value: a.idle_lines }))
  const byDepartment = (data?.by_department ?? [])
    .slice(0, TOP_N)
    .map((d) => ({ label: d.key, value: d.amount }))
  const byGroup = (data?.by_item_group ?? [])
    .slice(0, TOP_N)
    .map((d) => ({ label: d.key, value: d.amount }))

  return (
    <PageContainer>
      <ReportChartPageHeader
        title="Chi tiết YC mua hàng"
        description="Dòng hàng của yêu cầu mua hàng — soi phần chưa được đặt để không đặt sót đơn."
        period={period}
        tablePath={appRoutes.procurement.prLinesReport}
      />

      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
          <KpiTrendCard
            label="Dòng hàng yêu cầu"
            value={formatMoney(total.lines)}
            hint="Không tính dòng đã hủy"
            loading={isLoading}
          />
          <KpiTrendCard
            label="Giá trị yêu cầu"
            value={`${shortMoney(total.amount)} đ`}
            loading={isLoading}
          />
          <KpiTrendCard
            label="Chưa được đặt"
            value={formatMoney(total.idle_lines)}
            hint={
              total.idle_lines
                ? `Trị giá ${shortMoney(total.idle_amount)} đ`
                : 'Không còn dòng nào chờ đặt'
            }
            tone={total.idle_lines ? 'danger' : undefined}
            loading={isLoading}
          />
          <KpiTrendCard
            label="Tỷ lệ đã đặt"
            value={handledRate === null ? '—' : `${Math.round(handledRate)}%`}
            hint={`${formatMoney(total.lines - total.idle_lines)} / ${formatMoney(total.lines)} dòng`}
            loading={isLoading}
          />
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <ChartCard
            title="Dòng hàng theo tháng"
            description="Theo ngày tạo yêu cầu — phần cam là dòng chưa được đặt."
            loading={isLoading}
            isEmpty={months.every((m) => m.handled === 0 && m.idle === 0)}
            emptyLabel="Kỳ này chưa có yêu cầu mua hàng."
            className="lg:col-span-2"
          >
            <StackedMonthColumnChart
              data={months}
              unit="dòng"
              series={[
                { key: 'handled', label: 'Đã đặt', color: 'var(--chart-1)' },
                { key: 'idle', label: 'Chưa được đặt', color: 'var(--chart-2)' },
              ]}
            />
          </ChartCard>
          <ChartCard
            title="Tiến độ dòng hàng"
            description="Xếp theo quy trình, gồm cả dòng hủy."
            loading={isLoading}
            isEmpty={statuses.length === 0}
          >
            <HorizontalBarChart data={statuses} unit="dòng" />
          </ChartCard>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <ChartCard
            title="Dòng chưa đặt theo NSTM"
            description="Ai đang giữ nhiều dòng chờ đặt nhất."
            loading={isLoading}
            isEmpty={backlog.length === 0}
            emptyLabel="Không còn dòng nào chờ đặt."
          >
            <HorizontalBarChart data={backlog} unit="dòng" color="var(--chart-2)" />
          </ChartCard>
          <ChartCard
            title="Giá trị theo bộ phận"
            description="Bộ phận yêu cầu, giá trị gồm VAT."
            loading={isLoading}
            isEmpty={byDepartment.length === 0}
          >
            <HorizontalBarChart data={byDepartment} unit="đ" formatValue={shortMoney} />
          </ChartCard>
          <ChartCard
            title="Giá trị theo nhóm hàng"
            description="Phân loại vật tư bao bì / nguyên liệu."
            loading={isLoading}
            isEmpty={byGroup.length === 0}
          >
            <HorizontalBarChart data={byGroup} unit="đ" formatValue={shortMoney} />
          </ChartCard>
        </div>
      </div>
    </PageContainer>
  )
}
