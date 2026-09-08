import { ClipboardList, FileText, Plus, ShoppingCart, SquarePen, TruckIcon, Wallet } from 'lucide-react'
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { BarList } from '@/shared/ui/bar-list'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { ChartCard, CHART_COLORS, CHART_NEUTRAL, CHART_SEVERITY } from '@/shared/ui/chart'
import { ColumnChart } from '@/shared/ui/column-chart'
import { DonutChart } from '@/shared/ui/donut-chart'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { StatCard } from '@/shared/ui/stat-card'
import { cn } from '@/shared/utils/cn'
import { formatMoney } from '@/shared/utils/format-money'
import { ProcurementAlertList } from '../components/procurement-alert-list'
import { RecentPurchaseRequests } from '../components/recent-purchase-requests'
import { useProcurementDashboard } from '../hooks/use-procurement-dashboard'

/**
 * Màu thanh theo TRẠNG THÁI đơn — gán cố định cho từng mã, không theo thứ hạng:
 * lọc bớt trạng thái mà màu đổi theo thì người đã quen "vàng = chờ duyệt" đọc
 * sai ngay. Dùng đúng bộ token của `status-tone.ts` để thanh và huy hiệu trạng
 * thái trên các màn khác không lệch màu nhau.
 */
const PO_STATUS_COLORS: Record<string, string> = {
  draft: CHART_NEUTRAL,
  submitted: 'var(--warning)',
  approved: 'var(--info)',
  partial: 'var(--chart-2)',
  received: 'var(--success)',
  completed: 'var(--chart-3)',
  cancelled: 'var(--destructive)',
}

/**
 * Tổng quan Thu mua: KPI + chi phí theo tháng + cơ cấu chi theo nhóm hàng +
 * việc cần xử lý + phiếu gần đây + 4 khối phân tích nâng cao (Top NCC, Chi tiêu bộ phận, PO status, AP aging).
 *
 * Kiểm tra phân quyền chặt chẽ (can): chỉ hiển thị khối dữ liệu mà người dùng có quyền Xem.
 */
/**
 * Số cột xl khớp ĐÚNG số thẻ KPI hiện ra: vai trò ít quyền (người yêu cầu) chỉ
 * có 2-3 thẻ, giữ cứng 5 cột thì hơn nửa hàng trống toang hoác. Tailwind cần
 * class tĩnh nên liệt kê đủ, không ghép chuỗi.
 */
const KPI_GRID_COLS: Record<number, string> = {
  1: 'xl:grid-cols-1',
  2: 'xl:grid-cols-2',
  3: 'xl:grid-cols-3',
  4: 'xl:grid-cols-4',
  5: 'xl:grid-cols-5',
}

export function ProcurementDashboardPage() {
  const { can } = usePermission()
  const { data, isLoading } = useProcurementDashboard()

  const canPO = can('purchase_order', 'read')
  const canPR = can('purchase_request', 'read')
  const canSR = can('survey_request', 'read')
  const canPayable = can('payable', 'read')
  const canApprovePR = can('purchase_request', 'approve')
  const canApproveSR = can('survey_request', 'approve')

  // Người KHÔNG thuộc phòng thu mua (không quyền ĐMH) vào tổng quan chủ yếu để
  // tạo phiếu mới — thêm thẻ lối tắt cho họ; dân thu mua đã đủ 5 thẻ, không chen.
  const showQuickCreate = !canPO && (can('purchase_request', 'create') || can('survey_request', 'create'))
  const kpiCount =
    (canPO ? 3 : 0) + (canPR ? 1 : 0) + (canSR ? 1 : 0) + (showQuickCreate ? 1 : 0)

  const kpi = data?.kpi
  const spentThisYear = (data?.cost_12m ?? []).reduce((sum, item) => sum + item.value, 0)

  return (
    <PageContainer>
      <PageHeader
        title="Thu mua"
        description="Tổng quan yêu cầu mua hàng, báo giá, tiến độ giao hàng và phân tích chi tiêu."
      />

      {/* KPI Cards */}
      <div className={cn('mb-4 grid gap-4 sm:grid-cols-2', KPI_GRID_COLS[kpiCount] ?? 'xl:grid-cols-5')}>
        {canPO && (
          <StatCard
            icon={Wallet}
            label="Tổng chi tiêu"
            value={`${formatMoney(spentThisYear)} đ`}
            hint={`Giá trị nhận hàng năm ${data?.year ?? ''}`}
            loading={isLoading}
          />
        )}
        {canPR && (
          <StatCard
            icon={FileText}
            label="YCMH chờ duyệt"
            value={kpi?.pr_pending ?? 0}
            // "Cần phê duyệt" chỉ đúng với người CÓ quyền duyệt; người yêu cầu /
            // vai chỉ-đọc thấy câu đó là tưởng mình phải làm gì — đổi câu theo vai.
            hint={
              kpi?.pr_pending
                ? canApprovePR
                  ? 'Cần phê duyệt'
                  : 'Đang chờ duyệt'
                : 'Không tồn đọng'
            }
            tone={kpi?.pr_pending ? 'warning' : undefined}
            loading={isLoading}
          />
        )}
        {canSR && (
          <StatCard
            icon={ClipboardList}
            label="YC báo giá chờ duyệt"
            value={kpi?.sr_pending ?? 0}
            hint={
              kpi?.sr_pending
                ? canApproveSR
                  ? 'Cần phê duyệt'
                  : 'Đang chờ duyệt'
                : 'Không tồn đọng'
            }
            tone={kpi?.sr_pending ? 'warning' : undefined}
            loading={isLoading}
          />
        )}
        {showQuickCreate && (
          <Card className="gap-2">
            <CardHeader className="flex flex-row items-center gap-2 pb-0">
              <span className="grid size-8 shrink-0 place-items-center rounded-lg bg-accent text-accent-foreground">
                <SquarePen className="size-4" />
              </span>
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Tạo phiếu mới
              </CardTitle>
            </CardHeader>
            <CardContent className="flex flex-wrap items-center gap-2">
              {can('purchase_request', 'create') && (
                <Button asChild size="sm" variant="outline">
                  <Link to={appRoutes.procurement.purchaseRequestNew}>
                    <Plus />
                    Yêu cầu mua hàng
                  </Link>
                </Button>
              )}
              {can('survey_request', 'create') && (
                <Button asChild size="sm" variant="outline">
                  <Link to={appRoutes.procurement.surveyRequestNew}>
                    <Plus />
                    Yêu cầu báo giá
                  </Link>
                </Button>
              )}
            </CardContent>
          </Card>
        )}
        {canPO && (
          <StatCard
            icon={ShoppingCart}
            label="Đơn hàng hoạt động"
            value={kpi?.po_ordered ?? 0}
            hint="Đang theo dõi tiến độ"
            loading={isLoading}
          />
        )}
        {canPO && (
          <StatCard
            icon={TruckIcon}
            label="Giao hàng trễ"
            value={kpi?.late_deliveries ?? 0}
            hint={kpi?.late_deliveries ? 'Cần đốc thúc NCC' : 'Đúng hẹn'}
            tone={kpi?.late_deliveries ? 'danger' : undefined}
            loading={isLoading}
          />
        )}
      </div>

      {/* Main Grid: Biểu đồ & Việc cần xử lý */}
      <div className="grid items-start gap-4 lg:grid-cols-3">
        {canPO && (
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
        )}

        {/* Không có khối biểu đồ (vai trò ngoài thu mua) thì thẻ này đứng CẠNH
            "Yêu cầu mua gần đây" cho tròn hàng — trước đây nó một mình chiếm
            nguyên hàng ngang với cái ruột rỗng. */}
        <ChartCard
          title="Việc cần xử lý"
          description={`${data?.alert_total ?? 0} việc đang chờ`}
          loading={isLoading}
        >
          <div className="max-h-[320px] overflow-y-auto pr-1">
            <ProcurementAlertList alerts={data?.alerts ?? []} />
          </div>
        </ChartCard>

        {canPR && (
          <ChartCard
            // Vai trò ngoài thu mua: bảng phiếu là nội dung chính -> dồn sang
            // TRÁI, nhường cột phải cho "Việc cần xử lý" (thường rỗng).
            className={cn('lg:col-span-2', !canPO && 'lg:-order-1')}
            title="Yêu cầu mua gần đây"
            description={
              canApprovePR
                ? '8 phiếu mới nhất trong phạm vi bạn xem được. Có thể duyệt nhanh tại chỗ.'
                : '8 phiếu mới nhất trong phạm vi bạn xem được.'
            }
            loading={isLoading}
          >
            <RecentPurchaseRequests rows={data?.recent_prs ?? []} />
          </ChartCard>
        )}

        {canPO && (
          <ChartCard
            title="Chi phí theo nhóm hàng"
            description="Tỉ trọng chi mua trong năm."
            loading={isLoading}
            isEmpty={(data?.categories ?? []).length === 0}
          >
            <DonutChart
              centerLabel="tổng chi"
              unit="đ"
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
        )}
      </div>

      {/* 4 Khối bổ sung phân tích chi tiết (Top NCC, Bộ phận, Trạng thái PO, Tuổi nợ) */}
      <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {canPO && (
          <ChartCard
            title="Top nhà cung cấp"
            description="Theo tổng chi tiêu năm nay"
            loading={isLoading}
          >
            {/* MỘT màu cho cả danh sách: độ dài thanh đã nói lên thứ hạng rồi,
                tô mỗi hạng một màu là mã hóa hai lần cùng một thông tin. */}
            <BarList
              items={(data?.top_suppliers ?? []).map((s) => ({ label: s.name, value: s.value }))}
              formatValue={compactMoney}
            />
          </ChartCard>
        )}

        {canPO && (
          <ChartCard
            title="Chi tiêu theo bộ phận"
            description="Giá trị đơn mua theo phòng ban"
            loading={isLoading}
          >
            <BarList
              items={(data?.dept_spend ?? []).map((d) => ({ label: d.name, value: d.value }))}
              formatValue={compactMoney}
            />
          </ChartCard>
        )}

        {canPO && (
          <ChartCard
            title="Trạng thái đơn hàng"
            description="Số lượng đơn mua theo trạng thái"
            loading={isLoading}
          >
            <BarList
              items={(data?.po_status ?? []).map((s) => ({
                label: s.label,
                value: s.value,
                color: PO_STATUS_COLORS[s.key] ?? CHART_NEUTRAL,
              }))}
            />
          </ChartCard>
        )}

        {canPayable && (
          <ChartCard
            title="Tuổi nợ (Công nợ)"
            description="Phân tích công nợ còn phải trả"
            loading={isLoading}
          >
            <BarList
              items={(data?.ap_aging ?? []).map((a, index) => ({
                label: a.label,
                value: a.value,
                color: CHART_SEVERITY[index] ?? CHART_NEUTRAL,
              }))}
              formatValue={compactMoney}
            />
          </ChartCard>
        )}
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
