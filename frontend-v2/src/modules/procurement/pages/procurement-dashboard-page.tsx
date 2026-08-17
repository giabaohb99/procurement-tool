import { ClipboardList, FileText, ShoppingCart, TruckIcon, Wallet } from 'lucide-react'

import { ChartCard, CHART_COLORS, CHART_NEUTRAL } from '@/shared/ui/chart'
import { ColumnChart } from '@/shared/ui/column-chart'
import { DonutChart } from '@/shared/ui/donut-chart'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { StatCard } from '@/shared/ui/stat-card'
import { formatMoney } from '@/shared/utils/format-money'
import { ProcurementAlertList } from '../components/procurement-alert-list'
import { RecentPurchaseRequests } from '../components/recent-purchase-requests'
import { useProcurementDashboard } from '../hooks/use-procurement-dashboard'

/**
 * Tổng quan Thu mua: KPI + chi phí theo tháng + cơ cấu chi theo nhóm hàng +
 * việc cần xử lý + phiếu gần đây.
 *
 * Toàn bộ lấy từ MỘT lần gọi `/api/dashboard/overview` (backend đã lọc theo
 * phạm vi dữ liệu của người đăng nhập), nên trang này không tự đếm gì thêm.
 */
export function ProcurementDashboardPage() {
  const { data, isLoading } = useProcurementDashboard()

  const kpi = data?.kpi
  const spentThisYear = (data?.cost_12m ?? []).reduce((sum, item) => sum + item.value, 0)

  return (
    <PageContainer>
      <PageHeader
        title="Thu mua"
        description="Yêu cầu báo giá, khảo sát, yêu cầu và đơn mua hàng."
      />

      <div className="mb-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        <StatCard
          icon={Wallet}
          label="Tổng chi tiêu"
          value={`${formatMoney(spentThisYear)} đ`}
          hint={`Giá trị nhận hàng năm ${data?.year ?? ''}`}
          loading={isLoading}
        />
        <StatCard
          icon={FileText}
          label="YCMH chờ duyệt"
          value={kpi?.pr_pending ?? 0}
          hint={kpi?.pr_pending ? 'Cần phê duyệt' : 'Không tồn đọng'}
          tone={kpi?.pr_pending ? 'warning' : undefined}
          loading={isLoading}
        />
        <StatCard
          icon={ClipboardList}
          label="YC báo giá chờ duyệt"
          value={kpi?.sr_pending ?? 0}
          hint={kpi?.sr_pending ? 'Cần phê duyệt' : 'Không tồn đọng'}
          tone={kpi?.sr_pending ? 'warning' : undefined}
          loading={isLoading}
        />
        <StatCard
          icon={ShoppingCart}
          label="Đơn hàng hoạt động"
          value={kpi?.po_ordered ?? 0}
          hint="Đang theo dõi tiến độ"
          loading={isLoading}
        />
        <StatCard
          icon={TruckIcon}
          label="Giao hàng trễ"
          value={kpi?.late_deliveries ?? 0}
          hint={kpi?.late_deliveries ? 'Cần đốc thúc NCC' : 'Đúng hẹn'}
          tone={kpi?.late_deliveries ? 'danger' : undefined}
          loading={isLoading}
        />
      </div>

      <div className="grid items-start gap-4 lg:grid-cols-3">
        <ChartCard
          className="lg:col-span-2"
          title="Chi phí mua hàng theo tháng"
          description={`Giá trị nhận hàng · năm ${data?.year ?? ''}`}
          loading={isLoading}
          isEmpty={spentThisYear === 0}
          emptyLabel="Năm nay chưa phát sinh nhận hàng."
        >
          <ColumnChart
            data={data?.cost_12m ?? []}
            unit="đ"
            // Trục tiền tính bằng trăm triệu -> rút gọn, để nguyên thì nhãn dài
            // hơn cả cột và trục Y chiếm mất nửa biểu đồ.
            formatValue={compactMoney}
          />
        </ChartCard>

        <ChartCard
          title="Việc cần xử lý"
          description={`${data?.alert_total ?? 0} việc đang chờ`}
          loading={isLoading}
        >
          <div className="max-h-[320px] overflow-y-auto pr-1">
            <ProcurementAlertList alerts={data?.alerts ?? []} />
          </div>
        </ChartCard>

        <ChartCard
          className="lg:col-span-2"
          title="Yêu cầu mua gần đây"
          description="8 phiếu mới nhất trong phạm vi bạn xem được."
          loading={isLoading}
        >
          <RecentPurchaseRequests rows={data?.recent_prs ?? []} />
        </ChartCard>

        <ChartCard
          title="Chi phí theo nhóm hàng"
          description="Tỉ trọng chi mua trong năm."
          loading={isLoading}
          isEmpty={(data?.categories ?? []).length === 0}
        >
          <DonutChart
            centerLabel="tổng chi"
            unit="đ"
            // Tổng cỡ tỉ đồng -> rút gọn cho vừa lỗ vòng; chú giải vẫn số đầy đủ.
            formatTotal={compactMoney}
            formatValue={formatMoney}
            data={(data?.categories ?? []).map((item, index) => ({
              label: item.name,
              value: item.cost,
              // Quá 4 nhóm thì phần đuôi dùng xám trung tính — bảng phân loại
              // chỉ có 4 tông đã kiểm cho người mù màu.
              color: CHART_COLORS[index] ?? CHART_NEUTRAL,
            }))}
          />
        </ChartCard>
      </div>
    </PageContainer>
  )
}

/** 286.000.000 -> "286 tr"; 1.675.469.039 -> "1,7 tỷ". */
function compactMoney(value: number): string {
  if (Math.abs(value) >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toLocaleString('vi-VN', { maximumFractionDigits: 1 })} tỷ`
  }
  if (Math.abs(value) >= 1_000_000) {
    return `${Math.round(value / 1_000_000).toLocaleString('vi-VN')} tr`
  }
  return formatMoney(value)
}
