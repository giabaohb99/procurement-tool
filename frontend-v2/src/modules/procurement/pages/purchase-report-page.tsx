import { FileSpreadsheet, Printer, RefreshCw } from 'lucide-react'
import { Fragment } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { purchaseReportApi, RANGE_ENDPOINTS } from '../api/purchase-report-api'
import { ReportMatrixTab } from '../components/report-matrix-tab'
import { ReportOverviewTab } from '../components/report-overview-tab'
import { ReportShippingTab } from '../components/report-shipping-tab'
import {
  useProcurementReport,
  useRefreshReportMatrix,
  useReportMatrix,
  useRequestMatrix,
} from '../hooks/use-purchase-report'
import {
  ALL_PERIOD,
  DEPARTMENT_METRICS,
  EXPORT_SHEETS,
  ITEM_GROUP_METRICS,
  NSPT_METRICS,
  PYC_METRICS,
  REPORT_TABS,
  SUPPLIER_METRICS,
  YCKS_METRICS,
} from '../types/purchase-report'

/** Giá trị "không lọc công ty". Dùng chuỗi vì `SelectItem` không nhận value rỗng. */
const ALL_COMPANY = 'all'
/** Năm "tất cả" — backend gộp mọi năm, lúc đó cột tháng là tháng của nhiều năm. */
const ALL_YEAR = 'all'

/**
 * BÁO CÁO MUA HÀNG — tám tab trên cùng một bộ lọc (công ty · năm).
 *
 * Một lần gọi `/matrix` trả đủ số liệu cho năm tab ma trận, nên đổi tab KHÔNG
 * gọi lại API; chỉ hai tab Yêu cầu mua hàng / Yêu cầu báo giá có đường riêng và
 * chỉ tải khi thật sự mở (`enabled`).
 *
 * Bỏ nút "Lọc" của bản v1: đổi năm / công ty là react-query tự tải lại. Nút
 * "Cập nhật" thì giữ — nó bắt backend TÍNH LẠI snapshot chứ không phải nạp lại
 * cùng một số liệu.
 */
export function PurchaseReportPage() {
  const { can } = usePermission()
  const thisYear = new Date().getFullYear()

  const [tab, setTab] = useUrlParamState('tab', 'overview')
  const [year, setYear] = useUrlParamState('year', String(thisYear))
  const [companyId, setCompanyId] = useUrlParamState('company_id', ALL_COMPANY)
  const [period, setPeriod] = useUrlParamState('period', ALL_PERIOD)

  const company = companyId === ALL_COMPANY ? undefined : companyId
  const scope = { year, company_id: company }

  const { data: companies } = useCompanies({ page_size: 500, is_active: true })
  const matrix = useReportMatrix(scope)
  const refresh = useRefreshReportMatrix(scope)
  const overview = useProcurementReport({
    ...scope,
    month: period === ALL_PERIOD ? undefined : period,
  })

  // Tab nào không có quyền đọc thì ẩn hẳn; nếu URL trỏ vào tab đã bị ẩn thì rơi
  // về tab đầu tiên còn lại thay vì hiện khung trống.
  const tabs = REPORT_TABS.filter((item) => !item.need || can(item.need, 'read'))
  const activeTab = tabs.some((item) => item.key === tab) ? tab : (tabs[0]?.key ?? 'overview')

  const requestKind = activeTab === 'pyc_req' ? 'pyc' : activeTab === 'ycks_req' ? 'ycks' : ''
  const requestMatrix = useRequestMatrix({ ...scope, kind: requestKind }, !!requestKind)

  const months = matrix.data?.months ?? []
  const periodLabel =
    period === ALL_PERIOD ? 'Cả năm' : (months.find((item) => item.key === period)?.label ?? period)
  const yearLabel = year === ALL_YEAR ? 'Tất cả' : `Năm ${year}`
  const companyLabel =
    companies?.items.find((item) => String(item.id) === companyId)?.name ?? 'Tất cả công ty'

  // Workbook xuất ra có sẵn cột 12 tháng nên "Tất cả các năm" không có chỗ đổ số
  // -> quy về năm hiện tại.
  function exportExcel(sheet: string) {
    void purchaseReportApi.exportExcel(sheet, {
      year: year === ALL_YEAR ? String(thisYear) : year,
      company_id: company,
    })
  }

  return (
    <PageContainer>
      <PageHeader
        title="Báo cáo mua hàng"
        description={
          <span>
            Kỳ: {yearLabel} · {companyLabel}
            {matrix.data?.computed_at ? ` · Tính lúc: ${matrix.data.computed_at}` : ''}
          </span>
        }
        actions={
          <div className="flex flex-wrap items-center gap-2 print:hidden">
            <Select value={companyId} onValueChange={setCompanyId}>
              <SelectTrigger className="w-52">
                <SelectValue placeholder="Công ty" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_COMPANY}>Tất cả công ty</SelectItem>
                {(companies?.items ?? []).map((item) => (
                  <SelectItem key={item.id} value={String(item.id)}>
                    {item.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Select value={year} onValueChange={setYear}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="Năm" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_YEAR}>Tất cả</SelectItem>
                {[thisYear, thisYear - 1, thisYear - 2].map((item) => (
                  <SelectItem key={item} value={String(item)}>
                    {item}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>

            <Button
              variant="outline"
              disabled={refresh.isPending}
              onClick={() => refresh.mutate()}
              title="Tính lại số liệu báo cáo"
            >
              <RefreshCw className={refresh.isPending ? 'animate-spin' : undefined} />
              Cập nhật
            </Button>

            <Button variant="ghost" onClick={() => window.print()}>
              <Printer />
              In
            </Button>

            {can('report', 'export') && (
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost">
                    <FileSpreadsheet />
                    Xuất Excel
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-60">
                  {EXPORT_SHEETS.map((item, index) => (
                    <Fragment key={item.sheet}>
                      {/* Vạch ngăn sau mục "Tất cả": nó xuất cả 5 báo cáo, khác hẳn
                          các mục còn lại (mỗi mục một báo cáo). */}
                      {index === 1 && <DropdownMenuSeparator />}
                      <DropdownMenuItem onSelect={() => exportExcel(item.sheet)}>
                        {item.label}
                      </DropdownMenuItem>
                    </Fragment>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            )}
          </div>
        }
      />

      <Tabs value={activeTab} onValueChange={setTab}>
        <div className="flex flex-wrap items-center justify-between gap-2 print:hidden">
          {/* Tám tab, nhãn dài -> cho cuộn ngang thay vì ép xuống dòng. */}
          <TabsList className="max-w-full justify-start overflow-x-auto">
            {tabs.map((item) => (
              <TabsTrigger key={item.key} value={item.key}>
                {item.label}
              </TabsTrigger>
            ))}
          </TabsList>

          {/* "Xem theo" chỉ có nghĩa ở hai tab đọc số theo kỳ; các tab ma trận đã
              hiện đủ 12 tháng nên lọc thêm một tháng là thừa. */}
          {(activeTab === 'overview' || activeTab === 'shipping') && (
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              Xem theo:
              <Select value={period} onValueChange={setPeriod}>
                <SelectTrigger className="w-36">
                  <SelectValue placeholder="Cả năm" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL_PERIOD}>Cả năm</SelectItem>
                  {months.map((item) => (
                    <SelectItem key={item.key} value={item.key}>
                      {item.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        </div>

        <TabsContent value="overview" className="mt-2">
          <ReportOverviewTab
            data={overview.data}
            months={months}
            period={period}
            periodLabel={periodLabel}
            companyId={company}
            isLoading={overview.isLoading}
          />
        </TabsContent>

        <TabsContent value="supplier" className="mt-2">
          <ReportMatrixTab
            rows={matrix.data?.supplier ?? []}
            months={months}
            metrics={SUPPLIER_METRICS}
            nameLabel="Nhà cung cấp"
            title="Giao dịch nhà cung cấp"
            warnHint="đỏ = tỷ lệ trễ > 30%"
            yearLabel={yearLabel}
            rangeEndpoint={RANGE_ENDPOINTS.supplier}
            companyId={company}
            nameWidth={260}
            isLoading={matrix.isLoading}
          />
        </TabsContent>

        <TabsContent value="item_group" className="mt-2">
          <ReportMatrixTab
            rows={matrix.data?.item_group ?? []}
            months={months}
            metrics={ITEM_GROUP_METRICS}
            nameLabel="Loại vật tư bao bì / nguyên liệu"
            title="Tần suất mua theo loại vật tư bao bì / nguyên liệu"
            yearLabel={yearLabel}
            rangeEndpoint={RANGE_ENDPOINTS.item_group}
            companyId={company}
            nameWidth={200}
            isLoading={matrix.isLoading}
          />
        </TabsContent>

        <TabsContent value="nspt" className="mt-2">
          <ReportMatrixTab
            rows={matrix.data?.nspt ?? []}
            months={months}
            metrics={NSPT_METRICS}
            nameLabel="Nhân sự phụ trách"
            title="Giao hàng theo nhân sự phụ trách"
            warnHint="đỏ = tỷ lệ trễ > 30%"
            yearLabel={yearLabel}
            rangeEndpoint={RANGE_ENDPOINTS.nspt}
            companyId={company}
            isLoading={matrix.isLoading}
          />
        </TabsContent>

        <TabsContent value="department" className="mt-2">
          <ReportMatrixTab
            rows={matrix.data?.department ?? []}
            months={months}
            metrics={DEPARTMENT_METRICS}
            nameLabel="Bộ phận"
            title="Đặt hàng và đơn gấp theo bộ phận"
            warnHint="đỏ = tỷ lệ gấp > 30%"
            yearLabel={yearLabel}
            rangeEndpoint={RANGE_ENDPOINTS.department}
            companyId={company}
            isLoading={matrix.isLoading}
          />
        </TabsContent>

        <TabsContent value="shipping" className="mt-2">
          <ReportShippingTab
            rows={matrix.data?.shipping ?? []}
            period={period}
            periodLabel={periodLabel}
            year={year}
            companyId={company}
            isLoading={matrix.isLoading}
          />
        </TabsContent>

        <TabsContent value="pyc_req" className="mt-2">
          <ReportMatrixTab
            rows={requestMatrix.data?.rows ?? []}
            months={requestMatrix.data?.months ?? []}
            metrics={PYC_METRICS}
            nameLabel="Phòng ban"
            title="Yêu cầu mua hàng theo phòng ban"
            yearLabel={yearLabel}
            rangeEndpoint={RANGE_ENDPOINTS.pyc_req}
            rangeKind="pyc"
            companyId={company}
            nameWidth={220}
            isLoading={requestMatrix.isLoading}
          />
        </TabsContent>

        <TabsContent value="ycks_req" className="mt-2">
          <ReportMatrixTab
            rows={requestMatrix.data?.rows ?? []}
            months={requestMatrix.data?.months ?? []}
            metrics={YCKS_METRICS}
            nameLabel="Phòng ban"
            title="Yêu cầu báo giá theo phòng ban"
            yearLabel={yearLabel}
            rangeEndpoint={RANGE_ENDPOINTS.ycks_req}
            rangeKind="ycks"
            companyId={company}
            nameWidth={220}
            isLoading={requestMatrix.isLoading}
          />
        </TabsContent>
      </Tabs>
    </PageContainer>
  )
}
