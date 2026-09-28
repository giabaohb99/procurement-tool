import { appRoutes } from '@/shared/constants/app-routes'
import { PO_PROGRESS_STATUS } from '@/shared/constants/statuses'
import { CHART_SEVERITY, ChartCard } from '@/shared/ui/chart'
import { DonutChart } from '@/shared/ui/donut-chart'
import { HorizontalBarChart } from '@/shared/ui/horizontal-bar-chart'
import { PageContainer } from '@/shared/ui/page-container'
import { formatMoney } from '@/shared/utils/format-money'

import { KpiTrendCard } from '../components/kpi-trend-card'
import { ReportChartPageHeader } from '../components/report-chart-page-header'
import { StackedMonthColumnChart } from '../components/stacked-month-column-chart'
import { useReportPeriod } from '../hooks/use-report-period'
import { usePurchaseProgressSummary } from '../hooks/use-report-summaries'
import { fillYearMonths, orderByLifecycle, topBars } from '../utils/chart-series'
import { ratePercent } from '../utils/report-period-comparison'

const TOP_N = 8

/**
 * Tiến độ mua hàng — bản BIỂU ĐỒ. Trả lời: giao đúng hẹn tới đâu, dòng nào chưa
 * nhận đủ, NCC nào trễ nhiều, bộ phận nào còn nhiều việc mở. Bảng theo từng lần
 * giao vẫn ở Thu mua (nút «Xem bảng chi tiết»).
 *
 * Kỳ theo NGÀY ĐẶT hàng; «Lần giao theo tháng» theo ngày NHẬN.
 */
export function PurchaseProgressChartPage() {
  const period = useReportPeriod()
  const { data, isLoading } = usePurchaseProgressSummary({
    year: String(period.year),
    company_id: period.company,
  })
  const t = data?.total ?? { items: 0, deliveries: 0, late: 0, unreceived: 0, under: 0, full: 0 }
  const onTime = ratePercent(t.deliveries - t.late, t.deliveries)
  const pending = t.unreceived + t.under

  const months = fillYearMonths(period.year, data?.by_month ?? [], ['received', 'late'] as const).map(
    (m) => ({ label: m.label, onTime: Math.max(0, m.received - m.late), late: m.late }),
  )
  const statuses = orderByLifecycle(
    PO_PROGRESS_STATUS,
    (data?.by_progress_status ?? []).map((s) => ({ code: s.code, value: s.items })),
  )
  const lateSuppliers = topBars(data?.by_supplier ?? [], TOP_N, (s) => s.key, (s) => s.late)
  const openByDept = topBars(data?.by_department ?? [], TOP_N, (d) => d.key, (d) => d.open)

  return (
    <PageContainer>
      <ReportChartPageHeader
        title="Tiến độ mua hàng"
        description="Giao hàng đúng hẹn, dòng chưa nhận đủ, NCC trễ — theo đơn đặt trong năm."
        period={period}
        tablePath={appRoutes.procurement.purchaseProgress}
      />

      <div className="flex flex-col gap-4">
        <div className="grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
          <KpiTrendCard label="Dòng hàng đã đặt" value={formatMoney(t.items)} loading={isLoading} />
          <KpiTrendCard
            label="Lần giao đã nhận"
            value={formatMoney(t.deliveries)}
            hint={`Trễ ${formatMoney(t.late)} lần`}
            tone={t.late ? 'danger' : undefined}
            loading={isLoading}
          />
          <KpiTrendCard
            label="Giao đúng hạn"
            value={onTime === null ? '—' : `${Math.round(onTime)}%`}
            hint="So với hẹn NCC và hạn quy định"
            loading={isLoading}
          />
          <KpiTrendCard
            label="Dòng chưa nhận đủ"
            value={formatMoney(pending)}
            hint={`Chưa nhận ${formatMoney(t.unreceived)} · Nhận thiếu ${formatMoney(t.under)}`}
            tone={pending ? 'danger' : undefined}
            loading={isLoading}
          />
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <ChartCard
            title="Lần giao theo tháng"
            description="Theo ngày nhận hàng — phần cam là lần giao trễ."
            loading={isLoading}
            isEmpty={months.every((m) => m.onTime === 0 && m.late === 0)}
            emptyLabel="Kỳ này chưa nhận lần giao nào."
            className="lg:col-span-2"
          >
            <StackedMonthColumnChart
              data={months}
              unit="lần"
              series={[
                { key: 'onTime', label: 'Đúng hạn', color: 'var(--chart-1)' },
                { key: 'late', label: 'Trễ hạn', color: 'var(--chart-2)' },
              ]}
            />
          </ChartCard>
          <ChartCard
            title="Tình trạng nhận hàng"
            description="Tổng đã nhận so với số lượng đặt của từng dòng."
            loading={isLoading}
            isEmpty={t.unreceived + t.under + t.full === 0}
          >
            {/*  Màu MANG NGHĨA (đủ = ổn, thiếu = chú ý, chưa nhận = gấp) nên lấy
                 thang mức độ, không lấy dải phân loại. */}
            <DonutChart
              centerLabel="dòng"
              data={[
                { label: 'Nhận đủ', value: t.full, color: CHART_SEVERITY[0] },
                { label: 'Nhận thiếu', value: t.under, color: CHART_SEVERITY[1] },
                { label: 'Chưa nhận', value: t.unreceived, color: CHART_SEVERITY[3] },
              ]}
            />
          </ChartCard>
        </div>

        <div className="grid gap-4 lg:grid-cols-3">
          <ChartCard
            title="Tiến độ dòng hàng"
            description="Xếp theo quy trình, tạm ngưng / hủy đứng cuối."
            loading={isLoading}
            isEmpty={statuses.length === 0}
          >
            <HorizontalBarChart data={statuses} unit="dòng" />
          </ChartCard>
          {/*  NCC là dữ liệu nhạy cảm — backend trả rỗng khi thiếu `supplier.read`,
               thì ẩn hẳn thẻ chứ không vẽ một thẻ «chưa có dữ liệu» gây hiểu lầm. */}
          {data?.show_supplier !== false && (
            <ChartCard
              title="NCC giao trễ nhiều nhất"
              description="Số lần giao trễ trong kỳ."
              loading={isLoading}
              isEmpty={lateSuppliers.length === 0}
              emptyLabel="Không có lần giao trễ nào."
            >
              <HorizontalBarChart data={lateSuppliers} unit="lần" color="var(--chart-2)" />
            </ChartCard>
          )}
          <ChartCard
            title="Dòng còn mở theo bộ phận"
            description="Chưa hoàn thành, chưa hủy."
            loading={isLoading}
            isEmpty={openByDept.length === 0}
            emptyLabel="Không còn dòng nào đang mở."
          >
            <HorizontalBarChart data={openByDept} unit="dòng" />
          </ChartCard>
        </div>
      </div>
    </PageContainer>
  )
}
