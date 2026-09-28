import { ChevronRight } from 'lucide-react'
import { useMemo } from 'react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { useProcurementReport } from '@/modules/procurement/hooks/use-purchase-report'
import {
  shortMoney,
  type ProcurementBreakdownRow,
} from '@/modules/procurement/types/purchase-report'
import { appRoutes } from '@/shared/constants/app-routes'
import { CHART_SEVERITY, ChartCard } from '@/shared/ui/chart'
import { DonutChart } from '@/shared/ui/donut-chart'
import { HorizontalBarChart } from '@/shared/ui/horizontal-bar-chart'
import { formatMoney } from '@/shared/utils/format-money'

import {
  buildMonthComparison,
  comparableMonthCount,
  maskFutureMonths,
  percentChange,
  ratePercent,
  sumFirstMonths,
} from '../utils/report-period-comparison'
import { KpiTrendCard } from './kpi-trend-card'
import { PeriodComparisonChart } from './period-comparison-chart'

/** Số hạng mục trên mỗi biểu đồ «Top». Dài hơn thì vào báo cáo chi tiết mà xem. */
const TOP_N = 5

interface ProcurementReportSectionProps {
  year: number
  /** Bỏ trống = tất cả công ty. */
  companyId?: string
  /** Tiêu đề «Thu mua» — cần ở trang Tổng quan (nhiều phân hệ), thừa ở trang riêng. */
  showHeading?: boolean
}

/**
 * Khối báo cáo THU MUA của trang Tổng quan báo cáo: dải KPI so với kỳ trước,
 * đường chi phí hai năm, tỷ lệ giao đúng hạn và bốn biểu đồ Top.
 *
 * Gọi `/api/reports/procurement` HAI lần (năm đang xem + năm trước) — đường đó
 * đã lọc phạm vi dữ liệu và chỉ tính đơn thật, nên số ở đây khớp tab Tổng quan
 * của Báo cáo mua hàng.
 */
export function ProcurementReportSection({
  year,
  companyId,
  showHeading = true,
}: ProcurementReportSectionProps) {
  const { can } = usePermission()
  const current = useProcurementReport({ year: String(year), company_id: companyId })
  const previous = useProcurementReport({ year: String(year - 1), company_id: companyId })
  const loading = current.isLoading || previous.isLoading
  const cur = current.data
  const prev = previous.data

  const months = comparableMonthCount(year, new Date())
  const isFullYear = months === 12
  const points = useMemo(
    () => buildMonthComparison(year, cur?.spend_by_month ?? [], prev?.spend_by_month ?? []),
    [year, cur?.spend_by_month, prev?.spend_by_month],
  )
  const spend = sumFirstMonths(points, months)
  const compareCaption = isFullYear ? `so với năm ${year - 1}` : `so với cùng kỳ ${year - 1}`

  const onTime = ratePercent(cur?.delivery.on_time ?? 0, cur?.delivery.total ?? 0)
  const onTimePrev = ratePercent(prev?.delivery.on_time ?? 0, prev?.delivery.total ?? 0)
  const remaining = (cur?.payable_goods.remaining ?? 0) + (cur?.payable_shipping.remaining ?? 0)

  //  NCC và NSPT là dữ liệu nhạy cảm — backend của đường này KHÔNG tự chặn như
  //  các đường báo cáo khác, nên gác ở đây bằng đúng khóa tab Báo cáo mua hàng dùng.
  const canSeeSupplier = can('purchase_order', 'read')
  //  «Xem báo cáo» mở BẢNG ở đúng tab của Báo cáo mua hàng bên Thu mua — bản
  //  biểu đồ ở phân hệ Báo cáo không có tab để mà trỏ vào.
  const reportLink = (tab: string) => {
    const qs = new URLSearchParams({ tab, year: String(year) })
    if (companyId) qs.set('company_id', companyId)
    return `${appRoutes.procurement.purchaseReport}?${qs.toString()}`
  }
  const tops: { title: string; tab: string; rows?: ProcurementBreakdownRow[]; show: boolean }[] = [
    { title: 'Top nhà cung cấp', tab: 'supplier', rows: cur?.by_supplier, show: canSeeSupplier },
    { title: 'Top nhân sự phụ trách', tab: 'nspt', rows: cur?.by_nspt, show: canSeeSupplier },
    { title: 'Top bộ phận', tab: 'department', rows: cur?.by_department, show: true },
    { title: 'Top nhóm hàng', tab: 'item_group', rows: cur?.by_item_group, show: true },
  ]

  return (
    <section className="flex flex-col gap-4">
      {showHeading && (
        <h2 className="text-lg font-semibold text-navy dark:text-foreground">Thu mua</h2>
      )}
      <div className="grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-3 xl:grid-cols-5">
        <KpiTrendCard
          label="Chi phí mua hàng"
          value={`${shortMoney(spend.current)} đ`}
          change={percentChange(spend.current, spend.previous)}
          changeCaption={compareCaption}
          hint={isFullYear ? undefined : `Lũy kế T1–T${months}`}
          sparkline={points.slice(0, months).map((p) => p.current)}
          loading={loading}
        />
        {/*  Giá trị đặt / số đơn chỉ có số CẢ NĂM — năm đang chạy dở thì không so
             được với năm trước trọn vẹn, nên hiện số năm trước làm mốc thay cho %. */}
        <KpiTrendCard
          label="Giá trị đặt hàng"
          value={`${shortMoney(cur?.order_value ?? 0)} đ`}
          change={isFullYear ? percentChange(cur?.order_value ?? 0, prev?.order_value ?? 0) : null}
          changeCaption={compareCaption}
          hint={isFullYear ? undefined : `Cả năm ${year - 1}: ${shortMoney(prev?.order_value ?? 0)} đ`}
          loading={loading}
        />
        <KpiTrendCard
          label="Số đơn mua hàng"
          value={formatMoney(cur?.po_count ?? 0)}
          change={isFullYear ? percentChange(cur?.po_count ?? 0, prev?.po_count ?? 0) : null}
          changeCaption={compareCaption}
          hint={isFullYear ? undefined : `Cả năm ${year - 1}: ${formatMoney(prev?.po_count ?? 0)} đơn`}
          loading={loading}
        />
        <KpiTrendCard
          label="Giao hàng đúng hạn"
          value={onTime === null ? '—' : `${Math.round(onTime)}%`}
          change={onTime !== null && onTimePrev !== null ? onTime - onTimePrev : null}
          changeUnit="điểm"
          changeCaption={`so với ${year - 1}`}
          goodDirection="up"
          hint={`Trễ ${cur?.delivery.late ?? 0} / ${cur?.delivery.total ?? 0} lần giao`}
          loading={loading}
        />
        <KpiTrendCard
          label="Công nợ còn phải trả"
          value={`${shortMoney(remaining)} đ`}
          hint={cur?.overdue ? `Quá hạn ${shortMoney(cur.overdue)} đ` : 'Không có khoản quá hạn'}
          tone={cur?.overdue ? 'danger' : undefined}
          loading={loading}
          // Thẻ thứ năm lẻ hàng ở lưới 2 cột — trải hết bề ngang cho khỏi trơ trọi.
          className="max-lg:col-span-2"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <ChartCard
          title="Chi phí mua hàng theo tháng"
          description={`Công nợ phát sinh theo ngày nhận hàng · ${year} so với ${year - 1}.`}
          loading={loading}
          isEmpty={points.every((p) => p.current === 0 && p.previous === 0)}
          emptyLabel="Hai năm này chưa phát sinh nhận hàng."
          className="lg:col-span-2"
        >
          <PeriodComparisonChart
            data={maskFutureMonths(points, months)}
            currentLabel={`Năm ${year}`}
            previousLabel={`Năm ${year - 1}`}
            formatValue={shortMoney}
          />
        </ChartCard>
        <ChartCard
          title="Tiến độ giao hàng"
          description={`Các lần nhận hàng của đơn năm ${year}.`}
          loading={loading}
          isEmpty={!cur?.delivery.total}
          emptyLabel="Chưa có lần nhận hàng nào."
        >
          <DonutChart
            centerLabel="lần giao"
            data={[
              { label: 'Đúng hạn', value: cur?.delivery.on_time ?? 0, color: CHART_SEVERITY[0] },
              { label: 'Trễ hạn', value: cur?.delivery.late ?? 0, color: CHART_SEVERITY[3] },
            ]}
          />
        </ChartCard>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        {tops
          .filter((t) => t.show)
          .map((t) => {
            const data = (t.rows ?? [])
              .slice(0, TOP_N)
              .map((r) => ({ label: r.key, value: r.order_value }))
            return (
              <ChartCard
                key={t.tab}
                title={t.title}
                description="Theo giá trị đặt hàng của đơn thật."
                loading={loading}
                isEmpty={data.length === 0}
              >
                <HorizontalBarChart data={data} unit="đ" formatValue={shortMoney} />
                <Link
                  to={reportLink(t.tab)}
                  className="mt-2 inline-flex items-center gap-1 self-end text-sm text-primary hover:underline"
                >
                  Xem báo cáo
                  <ChevronRight className="size-4" />
                </Link>
              </ChartCard>
            )
          })}
      </div>
    </section>
  )
}
