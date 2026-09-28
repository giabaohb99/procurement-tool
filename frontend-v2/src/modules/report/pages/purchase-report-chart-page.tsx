import { usePermission } from '@/core/authorization/use-permission'
import { useProcurementReport } from '@/modules/procurement/hooks/use-purchase-report'
import { shortMoney } from '@/modules/procurement/types/purchase-report'
import { appRoutes } from '@/shared/constants/app-routes'
import { ChartCard } from '@/shared/ui/chart'
import { HorizontalBarChart } from '@/shared/ui/horizontal-bar-chart'
import { PageContainer } from '@/shared/ui/page-container'

import { ProcurementReportSection } from '../components/procurement-report-section'
import { ReportChartPageHeader } from '../components/report-chart-page-header'
import { useReportPeriod } from '../hooks/use-report-period'
import { topBars } from '../utils/chart-series'

const TOP_N = 8

/**
 * Báo cáo mua hàng — bản BIỂU ĐỒ: toàn bộ khối Thu mua của trang Tổng quan
 * (KPI so năm trước, chi phí hai năm, giao hàng, bốn Top) cộng thêm chi phí vận
 * chuyển theo đơn vị VC và tồn kho theo kho. Bảng ma trận 10 tab vẫn ở Thu mua.
 *
 * Gọi lại `useProcurementReport` với ĐÚNG tham số của khối Thu mua nên react-query
 * trả từ bộ nhớ đệm, không phát thêm request.
 */
export function PurchaseReportChartPage() {
  const { can } = usePermission()
  const period = useReportPeriod()
  const { data, isLoading } = useProcurementReport({
    year: String(period.year),
    company_id: period.company,
  })
  const carriers = topBars(data?.shipping.by_carrier ?? [], TOP_N, (c) => c.carrier, (c) => c.amount)
  const warehouses = topBars(
    data?.inventory.by_warehouse ?? [],
    TOP_N,
    (w) => w.warehouse || '(Không rõ)',
    (w) => w.value,
  )
  //  Đơn vị vận chuyển là NCC — cùng khóa gác với tab «Chi phí vận chuyển».
  const canSeeShipping = can('purchase_order', 'read')
  const canSeeInventory = can('inventory', 'read')

  return (
    <PageContainer>
      <ReportChartPageHeader
        title="Báo cáo mua hàng"
        description="Chi phí, đơn hàng, giao hàng và công nợ mua hàng — so với năm trước."
        period={period}
        tablePath={appRoutes.procurement.purchaseReport}
      />

      <div className="flex flex-col gap-4">
        <ProcurementReportSection
          year={period.year}
          companyId={period.company}
          showHeading={false}
        />

        {(canSeeShipping || canSeeInventory) && (
          <div className="grid gap-4 lg:grid-cols-2">
            {canSeeShipping && (
              <ChartCard
                title="Chi phí vận chuyển theo đơn vị"
                description={`Tổng ${shortMoney(data?.shipping.total ?? 0)} đ trong năm.`}
                loading={isLoading}
                isEmpty={carriers.length === 0}
                emptyLabel="Kỳ này chưa phát sinh chi phí vận chuyển."
              >
                <HorizontalBarChart data={carriers} unit="đ" formatValue={shortMoney} />
              </ChartCard>
            )}
            {canSeeInventory && (
              <ChartCard
                title="Giá trị tồn kho theo kho"
                description="Số hiện tại, không theo năm đang xem."
                loading={isLoading}
                isEmpty={warehouses.length === 0}
                emptyLabel="Chưa có tồn kho."
              >
                <HorizontalBarChart data={warehouses} unit="đ" formatValue={shortMoney} />
              </ChartCard>
            )}
          </div>
        )}
      </div>
    </PageContainer>
  )
}
