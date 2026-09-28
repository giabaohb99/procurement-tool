import { usePermission } from '@/core/authorization/use-permission'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'

import { ProcurementReportSection } from '../components/procurement-report-section'
import { ReportCatalogList } from '../components/report-catalog-list'
import { ReportPeriodFilters } from '../components/report-period-filters'
import { REPORT_CATALOG } from '../config/report-catalog'
import { useReportPeriod } from '../hooks/use-report-period'

/**
 * Tổng quan phân hệ Báo cáo — bố cục theo trang báo cáo của Haravan: bộ lọc kỳ
 * một hàng ở đầu, dải KPI so với kỳ trước, biểu đồ, rồi danh sách báo cáo theo
 * phân hệ. Mỗi khối số liệu tự gác bằng quyền của nguồn dữ liệu của nó.
 */
export function ReportOverviewPage() {
  const { can } = usePermission()
  const period = useReportPeriod()
  const canProcurement = can('report', 'read')
  const reports = REPORT_CATALOG.filter((r) => can(r.entity, 'read'))

  return (
    <PageContainer>
      <PageHeader
        title="Báo cáo"
        description={<span className="max-md:hidden">Số liệu các phân hệ, so với cùng kỳ năm trước.</span>}
        actions={canProcurement ? <ReportPeriodFilters period={period} /> : undefined}
      />
      <div className="flex flex-col gap-6">
        {canProcurement && (
          <ProcurementReportSection year={period.year} companyId={period.company} />
        )}
        <ReportCatalogList reports={reports} />
      </div>
    </PageContainer>
  )
}
