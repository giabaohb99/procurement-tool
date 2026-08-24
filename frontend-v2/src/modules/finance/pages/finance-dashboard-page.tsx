import { AlertTriangle, CheckCircle2, Clock, FileText, Plus, Wallet } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { BarList } from '@/shared/ui/bar-list'
import { Button } from '@/shared/ui/button'
import { ChartCard, CHART_NEUTRAL, CHART_SEVERITY } from '@/shared/ui/chart'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { StatCard } from '@/shared/ui/stat-card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import { useProcurementDashboard } from '@/modules/procurement/hooks/use-procurement-dashboard'
import { usePayableSummary } from '../hooks/use-payables'
import { usePaymentRequests } from '../hooks/use-payment-requests'
import { PaymentRequestStatusBadge } from '../components/payment-request-status-badge'
import type { PaymentRequestStatus } from '../types/payment-request'

/**
 * Tổng quan Tài chính: KPI Công nợ, tuổi nợ, top nợ NCC và danh sách YCTT gần đây.
 * Kiểm tra phân quyền chặt chẽ: `payable.read` và `payment_request.read`.
 *
 * `/api/dashboard/overview` gom số liệu của nhiều phân hệ và tự gác từng khối
 * theo quyền, nên trang này chỉ được lấy các khóa nằm trong khối `payable`
 * (`ap_aging`, `top_debt_suppliers`, `kpi.due_soon`, `kpi.overdue`). Mượn khóa
 * của khối khác là số sẽ trống với người chỉ có quyền Công nợ.
 */
export function FinanceDashboardPage() {
  const navigate = useNavigate()
  const { can } = usePermission()

  const canPayable = can('payable', 'read')
  const canPR = can('payment_request', 'read')

  const { data: overview, isLoading: isOverviewLoading } = useProcurementDashboard()
  const { data: payableSummary, isLoading: isSummaryLoading } = usePayableSummary({}, { enabled: canPayable })
  const { data: prsData, isLoading: isPrsLoading } = usePaymentRequests({ page_size: 8 }, { enabled: canPR })
  // Đếm YCTT đang chờ duyệt: hỏi thẳng danh sách YCTT và chỉ lấy `total`
  // (`page_size: 1` để khỏi kéo bản ghi). `/dashboard/overview` KHÔNG có số này
  // — `kpi.pr_pending` bên đó là Yêu cầu MUA HÀNG, thuộc phân hệ Thu mua.
  const { data: pendingPrs, isLoading: isPendingLoading } = usePaymentRequests(
    { page: 1, page_size: 1, status: 'submitted' },
    { enabled: canPR },
  )

  const kpi = overview?.kpi
  const apAging = overview?.ap_aging ?? []
  const topDebtSuppliers = overview?.top_debt_suppliers ?? []

  return (
    <PageContainer>
      <PageHeader
        title="Tài chính & Công nợ"
        description="Tổng quan công nợ phải trả, theo dõi tuổi nợ và quản lý phiếu đề nghị thanh toán."
        actions={
          canPR ? (
            <Button onClick={() => navigate(appRoutes.finance.paymentRequestNew)}>
              <Plus className="mr-1.5 size-4" />
              Tạo đề nghị thanh toán
            </Button>
          ) : undefined
        }
      />

      {/* KPI Cards */}
      <div className="mb-4 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">
        {canPayable && (
          <StatCard
            icon={Wallet}
            label="Tổng nợ còn lại"
            value={`${formatMoney(payableSummary?.remaining ?? 0)} đ`}
            hint={`Tổng phát sinh: ${formatMoney(payableSummary?.total ?? 0)} đ`}
            loading={isSummaryLoading}
          />
        )}

        {canPayable && (
          <StatCard
            icon={CheckCircle2}
            label="Đã thanh toán"
            value={`${formatMoney(payableSummary?.paid ?? 0)} đ`}
            hint="Đã chi trả"
            loading={isSummaryLoading}
          />
        )}

        {canPayable && (
          <StatCard
            icon={AlertTriangle}
            label="Nợ quá hạn"
            value={`${formatMoney(payableSummary?.overdue ?? kpi?.overdue ?? 0)} đ`}
            hint={payableSummary?.overdue ? 'Cần thanh toán gấp' : 'Không có nợ quá hạn'}
            tone={payableSummary?.overdue ? 'danger' : undefined}
            loading={isSummaryLoading || isOverviewLoading}
          />
        )}

        {canPayable && (
          <StatCard
            icon={Clock}
            label="Sắp đến hạn (7 ngày)"
            value={`${formatMoney(kpi?.due_soon ?? 0)} đ`}
            hint="Hạn trả trong 7 ngày tới"
            tone={kpi?.due_soon ? 'warning' : undefined}
            loading={isOverviewLoading}
          />
        )}

        {canPR && (
          <StatCard
            icon={FileText}
            label="YCTT chờ duyệt"
            value={pendingPrs?.total ?? 0}
            hint={pendingPrs?.total ? 'Cần kế toán/sếp duyệt' : 'Không tồn đọng'}
            tone={pendingPrs?.total ? 'warning' : undefined}
            loading={isPendingLoading}
          />
        )}
      </div>

      {/* Main Grid: Tuổi nợ + Top nợ NCC */}
      <div className="grid gap-4 lg:grid-cols-2 mb-4">
        {canPayable && (
          <ChartCard
            title="Phân tích Tuổi nợ (AP Aging)"
            description="Cơ cấu công nợ theo thời gian quá hạn"
            loading={isOverviewLoading}
          >
            <BarList
              emptyLabel="Chưa có dữ liệu tuổi nợ"
              formatValue={(value) => `${formatMoney(value)} đ`}
              items={apAging.map((item, index) => ({
                label: item.label,
                value: item.value,
                // Bốn nhóm xếp từ "Chưa đến hạn" tới "> 60 ngày" nên màu đi theo
                // MỨC ĐỘ, không phải theo thứ hạng.
                color: CHART_SEVERITY[index] ?? CHART_NEUTRAL,
              }))}
            />
          </ChartCard>
        )}

        {canPayable && (
          <ChartCard
            title="Top Nhà cung cấp công nợ lớn"
            description="Các đơn vị có số nợ còn lại cao nhất"
            loading={isOverviewLoading}
          >
            <BarList
              emptyLabel="Chưa có dữ liệu công nợ nhà cung cấp"
              formatValue={(value) => `${formatMoney(value)} đ`}
              items={topDebtSuppliers.map((item) => ({ label: item.name, value: item.value }))}
            />
          </ChartCard>
        )}
      </div>

      {/* Yêu cầu thanh toán gần đây */}
      {canPR && (
        <ChartCard
          title="Đề nghị thanh toán gần đây"
          description="Các phiếu đề nghị thanh toán mới nhất"
          loading={isPrsLoading}
        >
          <div className="overflow-x-auto">
            <Table className="min-w-[700px]">
              <TableHeader>
                <TableRow>
                  <TableHead className="w-36">Mã phiếu</TableHead>
                  <TableHead className="min-w-48">Nhà cung cấp</TableHead>
                  <TableHead className="w-28">Loại nợ</TableHead>
                  <TableHead className="w-28">Ngày lập</TableHead>
                  <TableHead className="w-36 text-right">Tổng tiền</TableHead>
                  <TableHead className="w-32">Trạng thái</TableHead>
                </TableRow>
              </TableHeader>

              <TableBody>
                {(prsData?.items ?? []).length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={6} className="py-8 text-center text-xs text-muted-foreground">
                      Chưa có phiếu đề nghị thanh toán nào.
                    </TableCell>
                  </TableRow>
                ) : (
                  (prsData?.items ?? []).map((row) => (
                    <TableRow
                      key={row.id}
                      className="cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800/50"
                      onClick={() => navigate(`/finance/payment-requests/${row.id}`)}
                    >
                      <TableCell className="font-semibold text-sky-600 dark:text-sky-400">
                        {row.code}
                      </TableCell>
                      <TableCell className="font-medium">{row.supplier_name || row.supplier_code}</TableCell>
                      <TableCell>{row.source_type === 'shipping' ? 'Vận chuyển' : 'Hàng hóa'}</TableCell>
                      <TableCell>{formatDate(row.request_date) || '—'}</TableCell>
                      <TableCell className="text-right font-medium tabular-nums">
                        {formatMoney(row.total)} đ
                      </TableCell>
                      <TableCell>
                        <PaymentRequestStatusBadge status={row.status as PaymentRequestStatus} />
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </div>
        </ChartCard>
      )}
    </PageContainer>
  )
}
