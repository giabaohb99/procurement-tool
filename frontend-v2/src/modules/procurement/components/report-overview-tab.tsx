import { AlertTriangle, Boxes, Info, ShoppingCart, Wallet, WalletCards } from 'lucide-react'
import { useMemo, useState } from 'react'

import { ChartCard } from '@/shared/ui/chart'
import { ColumnChart } from '@/shared/ui/column-chart'
import { StatCard } from '@/shared/ui/stat-card'
import { formatMoney } from '@/shared/utils/format-money'
import { StatusBadge } from './document-status-badge'
import { ReportDailyDialog } from './report-daily-dialog'
import { PO_STATUS_LABELS } from '../types/purchase-document'
import {
  ALL_PERIOD,
  shortMoney,
  spendSeries,
  type ProcurementReport,
  type ReportMonth,
} from '../types/purchase-report'

interface ReportOverviewTabProps {
  data: ProcurementReport | undefined
  months: ReportMonth[]
  /** `'all'` hoặc `'YYYY-MM'` — chỉ dùng để nhắc người đọc đang lọc theo tháng nào. */
  period: string
  periodLabel: string
  companyId?: string
  isLoading?: boolean
}

/**
 * Tab Tổng quan: năm thẻ số, phân bố trạng thái đơn, tiến độ giao hàng và biểu
 * đồ chi phí theo tháng (bấm cột để xem chi tiết theo ngày).
 *
 * Hai con số dễ bị hiểu là phải bằng nhau nhưng KHÔNG: "Giá trị đặt hàng" tính
 * theo ngày ĐẶT, còn biểu đồ chi phí tính công nợ phát sinh theo ngày NHẬN. Ghi
 * chú đầu tab nói rõ điều đó — đừng bỏ.
 */
export function ReportOverviewTab({
  data,
  months,
  period,
  periodLabel,
  companyId,
  isLoading = false,
}: ReportOverviewTabProps) {
  /** Tháng đang mở hộp thoại chi tiết theo ngày. Rỗng = đóng. */
  const [dailyMonth, setDailyMonth] = useState('')

  const series = useMemo(
    () => spendSeries(months, data?.spend_by_month ?? []),
    [months, data?.spend_by_month],
  )

  const delivery = data?.delivery ?? { on_time: 0, late: 0, total: 0 }
  const onTimePct = delivery.total ? Math.round((delivery.on_time / delivery.total) * 100) : 0
  const remaining = (data?.payable_goods.remaining ?? 0) + (data?.payable_shipping.remaining ?? 0)
  const statusEntries = Object.entries(data?.po_status ?? {}).filter(([, count]) => count > 0)

  return (
    <div className="flex flex-col gap-4">
      <div className="rounded-lg border bg-muted/40 px-4 py-3 text-xs leading-relaxed text-muted-foreground print:hidden">
        <p>
          <Info className="mr-1 inline size-3.5 align-[-2px] text-primary" />
          <b>Lưu ý cách đọc số:</b> "Giá trị đặt hàng" = tổng giá trị các đơn <b>ĐẶT</b> theo{' '}
          <b>ngày đặt</b>. Biểu đồ "Chi phí mua theo tháng" = <b>công nợ phát sinh</b> (tiền hàng +
          vận chuyển, gồm VAT, theo lượng thực nhận) theo <b>ngày nhận hàng</b>. Hai con số đo khác
          nhau nên <b>không bằng nhau</b>. Mọi số liệu chỉ tính <b>đơn thật</b> (đã duyệt trở đi) —
          đã loại trừ đơn nháp / chờ duyệt / hủy / từ chối.
        </p>
        {period !== ALL_PERIOD && (
          <p className="mt-1">
            Đang lọc theo <b>{periodLabel}</b>: các thẻ số và tình hình đơn / giao hàng tính theo
            tháng này; riêng biểu đồ "Chi phí mua theo tháng" vẫn hiển thị cả năm.
          </p>
        )}
      </div>

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard
          icon={ShoppingCart}
          label="Số đơn mua hàng"
          value={formatMoney(data?.po_count ?? 0)}
          loading={isLoading}
        />
        <StatCard
          icon={Wallet}
          label="Giá trị đặt hàng"
          value={`${formatMoney(data?.order_value ?? 0)} đ`}
          hint="Theo ngày đặt"
          loading={isLoading}
        />
        <StatCard
          icon={WalletCards}
          label="Công nợ còn phải trả"
          value={`${formatMoney(remaining)} đ`}
          hint={`Hàng ${formatMoney(data?.payable_goods.remaining ?? 0)} · Vận chuyển ${formatMoney(
            data?.payable_shipping.remaining ?? 0,
          )}`}
          loading={isLoading}
        />
        <StatCard
          icon={AlertTriangle}
          label="Công nợ quá hạn"
          value={`${formatMoney(data?.overdue ?? 0)} đ`}
          hint={data?.overdue ? 'Cần thanh toán gấp' : 'Không có khoản quá hạn'}
          tone={data?.overdue ? 'danger' : undefined}
          loading={isLoading}
        />
        <StatCard
          icon={Boxes}
          label="Giá trị tồn kho"
          value={`${formatMoney(data?.inventory_value ?? 0)} đ`}
          loading={isLoading}
        />
      </div>

      <div className="grid items-start gap-4 lg:grid-cols-2">
        <ChartCard
          title="Đơn theo trạng thái"
          description="Gồm cả đơn nháp / hủy để thấy phân bố."
          loading={isLoading}
        >
          <div className="flex flex-wrap gap-2">
            {statusEntries.map(([status, count]) => (
              <span
                key={status}
                className="inline-flex items-center gap-2 rounded-md border px-2.5 py-1.5"
              >
                <StatusBadge status={status} labels={PO_STATUS_LABELS} />
                <b className="tabular-nums">{count}</b>
              </span>
            ))}
            {statusEntries.length === 0 && (
              <span className="text-sm text-muted-foreground">Chưa có đơn.</span>
            )}
          </div>

          <h4 className="mt-6 mb-2 text-sm font-semibold text-navy dark:text-foreground">
            Tiến độ giao hàng
          </h4>
          <p className="mb-2 text-sm">
            Đúng hạn <b className="text-success">{delivery.on_time}</b> · Trễ{' '}
            <b className="text-destructive">{delivery.late}</b> / {delivery.total}
          </p>
          {/* Rãnh tô đỏ nhạt, phần đã chạy tô xanh: nhìn một cái là ra tỉ lệ
              đúng hạn / trễ mà không cần đọc số. */}
          <div className="h-3.5 overflow-hidden rounded-full bg-destructive/20">
            <div className="h-full bg-success" style={{ width: `${onTimePct}%` }} />
          </div>
          <p className="mt-1 text-xs text-muted-foreground">Đúng hạn {onTimePct}%</p>
        </ChartCard>

        <ChartCard
          title="Chi phí mua theo tháng"
          description="Công nợ phát sinh theo ngày nhận · bấm vào cột để xem theo ngày."
          loading={isLoading}
          isEmpty={series.every((bar) => bar.value === 0)}
          emptyLabel="Kỳ này chưa phát sinh nhận hàng."
        >
          <ColumnChart
            data={series}
            unit="đ"
            formatValue={shortMoney}
            onBarClick={(index) => {
              const bar = series[index]
              if (bar?.value) setDailyMonth(bar.key)
            }}
          />
        </ChartCard>
      </div>

      <ReportDailyDialog
        month={dailyMonth}
        monthLabel={months.find((month) => month.key === dailyMonth)?.label ?? dailyMonth}
        companyId={companyId}
        onClose={() => setDailyMonth('')}
      />
    </div>
  )
}
