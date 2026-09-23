// bao-CR-470 — Tra cứu giá hải quan (bản v2). Thiết kế: doc/erp/hai-quan/04-giao-dien.md.
//
// MỘT màn hình, năm thẻ: Danh sách · Biểu đồ · Nhà nhập khẩu · So sánh · Pháp lý & thuế.
// Đại ca chốt 23/09/2026: biểu đồ nằm chung màn với danh sách, CHỈ hiện khi đã có bộ lọc
// (từ khóa hoặc mã HS); không có trang tổng quan riêng, không tính sẵn, không tác vụ định kỳ.
// Quyền: `customs_price` (đọc / ghi = nạp tệp / xóa = hoàn tác / xuất = Excel).
//
// Bộ lọc và thẻ đang mở nằm TRÊN ĐƯỜNG DẪN — gửi link cho người khác là họ thấy đúng kết
// quả đang xem. Thanh lọc dùng chung cho cả năm thẻ, đổi thẻ không mất bộ lọc.
import {
  BookOpen,
  ChartLine,
  Download,
  Factory,
  FilterX,
  GitCompareArrows,
  History,
  Landmark,
  List,
  TriangleAlert,
  Upload,
  X,
} from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { DataTable } from '@/shared/data-table'
import { appRoutes } from '@/shared/constants/app-routes'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { useSetUrlParams, useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlRangeParam } from '@/shared/hooks/use-url-range-param'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { ScrollableTabsList } from '@/shared/ui/scrollable-tabs-list'
import { SearchField } from '@/shared/ui/search-field'
import { SearchSelect } from '@/shared/ui/search-select'
import { TAB_TRIGGER_UNDERLINE } from '@/shared/ui/tab-underline'
import { Tabs, TabsContent, TabsTrigger } from '@/shared/ui/tabs'

import { exportCustomsLines } from '../api/customs-api'
import { CustomsCompareTab } from '../components/customs/customs-compare-tab'
import { CustomsNeedFilterState, CustomsNotice } from '../components/customs/customs-controls'
import { CustomsCoverageStrip } from '../components/customs/customs-coverage-strip'
import { CustomsHistoryDialog } from '../components/customs/customs-history-dialog'
import { CustomsImportDialog } from '../components/customs/customs-import-dialog'
import { CustomsImportersTab } from '../components/customs/customs-importers-tab'
import { CustomsLegalTab } from '../components/customs/customs-legal-tab'
import { CustomsLineDetailSheet } from '../components/customs/customs-line-detail-sheet'
import { CustomsPriceChart } from '../components/customs/customs-price-chart'
import { CUSTOMS_LINE_COLUMNS } from '../config/customs-line-columns'
import {
  useCustomsAlerts,
  useCustomsCoverage,
  useCustomsLines,
  useCustomsOptions,
  useCustomsPermissions,
} from '../hooks/use-customs'
import type { CustomsFilters, CustomsOptionItem } from '../types/customs'
import {
  buildCustomsParams,
  hasChartFilter,
  resolveLinesEmptyMessage,
} from '../utils/customs'

const TABS = [
  { key: 'list', label: 'Danh sách', icon: List },
  { key: 'chart', label: 'Biểu đồ', icon: ChartLine },
  { key: 'importers', label: 'Nhà nhập khẩu', icon: Factory },
  { key: 'compare', label: 'So sánh', icon: GitCompareArrows },
  { key: 'legal', label: 'Pháp lý & thuế', icon: Landmark },
] as const

type TabKey = (typeof TABS)[number]['key']

/** Hậu tố `-v2`: bố cục cũ (ẩn 22 cột) đã lưu trong máy người dùng không được thắng bố cục mới. */
const STORAGE_KEY = 'procurement.customs-lines-v2'
const DEFAULT_PAGE_SIZE = 50
/** Tham số lọc trên URL — "Xóa lọc" dọn đúng bộ này, giữ nguyên thẻ đang mở. */
const FILTER_PARAMS = [
  'q',
  'hs_code',
  'origin',
  'unit',
  'formulation',
  'importer_id',
  'importer_name',
  'partner_id',
  'partner_name',
  'date_from',
  'date_to',
] as const

function toSelectOptions(items: CustomsOptionItem[] | undefined) {
  return (items ?? []).map((item) => ({ value: item.value, label: `${item.value} (${item.count})` }))
}

export function CustomsPricePage() {
  const { canImport, canExport, canReadRegulations } = useCustomsPermissions()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam('q')
  const [hsCode, setHsCode] = useUrlParamState('hs_code', '')
  const [origin, setOrigin] = useUrlParamState('origin', '')
  const [unit, setUnit] = useUrlParamState('unit', '')
  const [formulation, setFormulation] = useUrlParamState('formulation', '')
  const [dateFrom, dateTo, setDateRange] = useUrlRangeParam('date_from', 'date_to')
  const [rawTab, setTab] = useUrlParamState('tab', 'list')
  const [searchParams] = useSearchParams()
  const setUrlParams = useSetUrlParams()

  const importerId = searchParams.get('importer_id') ?? ''
  const importerName = searchParams.get('importer_name') ?? ''
  const partnerId = searchParams.get('partner_id') ?? ''
  const partnerName = searchParams.get('partner_name') ?? ''
  const tab: TabKey = TABS.some((item) => item.key === rawTab) ? (rawTab as TabKey) : 'list'

  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [detailId, setDetailId] = useState<number | null>(null)
  const [dialog, setDialog] = useState<'' | 'import' | 'history'>('')
  const [exporting, setExporting] = useState(false)
  const singleFlight = useSingleFlight()

  //  Từ khóa lấy bản ĐÃ HOÃN — mỗi phím gõ không bắn một lượt gọi API.
  const filters = useMemo<CustomsFilters>(
    () => ({
      q: debouncedValue,
      hs_code: hsCode,
      origin,
      unit,
      formulation,
      importer_id: importerId,
      partner_id: partnerId,
      date_from: dateFrom,
      date_to: dateTo,
    }),
    [debouncedValue, hsCode, origin, unit, formulation, importerId, partnerId, dateFrom, dateTo],
  )
  const filterParams = useMemo(() => buildCustomsParams(filters), [filters])
  const [page, setPage] = usePageResetOnFilterChange([JSON.stringify(filterParams)])

  const coverage = useCustomsCoverage()
  const options = useCustomsOptions()
  const lines = useCustomsLines({ ...filterParams, page, page_size: pageSize }, tab === 'list')
  //  Cảnh báo pháp lý chỉ so khi từ khóa từ 3 ký tự — khớp `match_alerts` của backend.
  const alerts = useCustomsAlerts(filterParams, filters.q.trim().length >= 3)
  const alertItems = alerts.data ?? []

  const chartReady = hasChartFilter(filters)
  const filtersActive = FILTER_PARAMS.some((name) => Boolean(searchParams.get(name)))

  function clearFilters() {
    setKeyword('')
    setUrlParams(Object.fromEntries(FILTER_PARAMS.map((name) => [name, null])))
  }

  function filterByImporter(id: number, name: string) {
    setDetailId(null)
    setUrlParams({ importer_id: String(id), importer_name: name || null, tab: null })
  }

  function filterByPartner(id: number, name: string) {
    setDetailId(null)
    setUrlParams({ partner_id: String(id), partner_name: name || null, tab: null })
  }

  function exportExcel() {
    void singleFlight(async () => {
      setExporting(true)
      try {
        await exportCustomsLines(filterParams)
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Không xuất được tệp Excel')
      } finally {
        setExporting(false)
      }
    })
  }

  return (
    <PageContainer className="flex flex-col gap-3">
      <PageHeader
        title="Tra cứu giá hải quan"
        description="Giá nhập khẩu theo dữ liệu hải quan (tệp GTT02) — tra theo tên hàng, hoạt chất hoặc mã HS."
        actions={
          <>
            {canReadRegulations && (
              <Button asChild variant="outline">
                <Link to={appRoutes.procurement.customsRegulations}>
                  <BookOpen className="size-4" />
                  Danh mục hóa chất
                </Link>
              </Button>
            )}
            <Button type="button" variant="outline" onClick={() => setDialog('history')}>
              <History className="size-4" />
              Lịch sử nạp
            </Button>
            {canImport && (
              <Button type="button" onClick={() => setDialog('import')}>
                <Upload className="size-4" />
                Nạp dữ liệu
              </Button>
            )}
          </>
        }
      />

      <CustomsCoverageStrip
        coverage={coverage.data}
        ingredientCoverage={options.data?.ingredient_coverage}
        isLoading={coverage.isLoading}
      />

      <Card className="gap-3 p-4">
        <div className="flex flex-wrap items-center gap-2">
          <SearchField
            value={keyword}
            onChange={setKeyword}
            placeholder="Tên hàng / hoạt chất — vd ATRAZINE, mancozeb, glyphosate…"
            placeholderShort="Tên hàng, hoạt chất…"
            aria-label="Tìm theo tên hàng hoặc hoạt chất"
            className="min-w-56 flex-1 md:max-w-md"
          />
          <div className="w-44 max-md:w-full">
            <SearchSelect
              value={hsCode}
              onChange={setHsCode}
              options={toSelectOptions(options.data?.hs_codes)}
              placeholder="Tất cả mã HS"
              searchPlaceholder="Tìm mã HS…"
              clearable
            />
          </div>
          <div className="w-44 max-md:w-full">
            <SearchSelect
              value={origin}
              onChange={setOrigin}
              options={toSelectOptions(options.data?.origins)}
              placeholder="Tất cả xuất xứ"
              searchPlaceholder="Tìm xuất xứ…"
              clearable
            />
          </div>
          <div className="w-40 max-md:w-full">
            <SearchSelect
              value={unit}
              onChange={setUnit}
              options={toSelectOptions(options.data?.units)}
              placeholder="Tất cả đơn vị"
              searchPlaceholder="Tìm đơn vị…"
              clearable
            />
          </div>
          <div className="w-44 max-md:w-full">
            <SearchSelect
              value={formulation}
              onChange={setFormulation}
              options={toSelectOptions(options.data?.formulations)}
              placeholder="Tất cả hàm lượng / dạng"
              searchPlaceholder="Tìm hàm lượng / dạng…"
              clearable
            />
          </div>
          <DateRangePicker
            from={dateFrom}
            to={dateTo}
            onChange={setDateRange}
            placeholder="Ngày đăng ký từ – tới"
            className="max-md:w-full"
          />
          {filtersActive && (
            <Button type="button" variant="ghost" onClick={clearFilters}>
              <FilterX className="size-4" />
              Xóa lọc
            </Button>
          )}
        </div>

        {(importerId || partnerId) && (
          <div className="flex flex-wrap gap-2">
            {importerId && (
              <FilterChip
                label={`Doanh nghiệp: ${importerName || `#${importerId}`}`}
                onRemove={() => setUrlParams({ importer_id: null, importer_name: null })}
                removeLabel="Bỏ lọc doanh nghiệp"
              />
            )}
            {partnerId && (
              <FilterChip
                label={`Đối tác: ${partnerName || `#${partnerId}`}`}
                onRemove={() => setUrlParams({ partner_id: null, partner_name: null })}
                removeLabel="Bỏ lọc đối tác"
              />
            )}
          </div>
        )}
      </Card>

      {alertItems.length > 0 && (
        <CustomsNotice tone="danger" icon={<TriangleAlert className="size-4" />}>
          <p className="font-semibold">Lưu ý pháp lý cho «{filters.q}»:</p>
          <ul className="mt-1 list-disc space-y-0.5 pl-5">
            {alertItems.slice(0, 5).map((alert) => (
              <li key={alert.id}>
                {alert.name}
                {alert.cas_no ? ` (CAS ${alert.cas_no})` : ''} — {alert.obligation}
              </li>
            ))}
          </ul>
          {alertItems.length > 5 && (
            <p className="mt-1">
              … và {alertItems.length - 5} mục khác — xem thẻ Pháp lý &amp; thuế.
            </p>
          )}
        </CustomsNotice>
      )}

      <Tabs value={tab} onValueChange={(next) => setTab(next)}>
        <ScrollableTabsList
          value={tab}
          className="max-md:w-full max-md:min-w-0 md:max-w-full md:min-w-0 md:overflow-x-auto"
        >
          {TABS.map((item) => (
            <TabsTrigger key={item.key} value={item.key} className={TAB_TRIGGER_UNDERLINE}>
              <item.icon className="size-4" />
              {item.label}
            </TabsTrigger>
          ))}
        </ScrollableTabsList>

        <TabsContent value="list" className="mt-2">
          <Card className="p-4">
            <DataTable
              columns={CUSTOMS_LINE_COLUMNS}
              rows={lines.data?.items}
              getRowId={(line) => line.id}
              isLoading={lines.isLoading}
              isError={lines.isError}
              emptyMessage={resolveLinesEmptyMessage(coverage.data?.total, canImport)}
              storageKey={STORAGE_KEY}
              onRowClick={(line) => setDetailId(line.id)}
              //  Bộ lọc đứng NGOÀI bảng (dùng chung cho năm thẻ) và đã có nút "Xóa lọc"
              //  riêng ở thanh lọc — tắt nút của bảng cho khỏi hai nút làm cùng một việc.
              filtersActive={false}
              pagination={{
                page,
                pageSize,
                total: lines.data?.total ?? 0,
                onPageChange: setPage,
                onPageSizeChange: (size) => {
                  setPageSize(size)
                  setPage(1)
                },
                unitLabel: 'dòng hàng',
              }}
              toolbar={
                canExport ? (
                  <Button
                    type="button"
                    variant="outline"
                    disabled={exporting || !lines.data?.total}
                    onClick={exportExcel}
                    title="Xuất đúng các dòng đang lọc (tối đa 50.000 dòng)"
                  >
                    <Download className="size-4" />
                    {exporting ? 'Đang xuất…' : 'Xuất Excel'}
                  </Button>
                ) : undefined
              }
            />
          </Card>
        </TabsContent>

        <TabsContent value="chart" className="mt-2">
          {chartReady ? <CustomsPriceChart filters={filters} /> : <CustomsNeedFilterState />}
        </TabsContent>

        <TabsContent value="importers" className="mt-2">
          {chartReady ? (
            <CustomsImportersTab filters={filters} onPickImporter={filterByImporter} />
          ) : (
            <CustomsNeedFilterState />
          )}
        </TabsContent>

        <TabsContent value="compare" className="mt-2">
          <CustomsCompareTab filters={filters} />
        </TabsContent>

        <TabsContent value="legal" className="mt-2">
          <CustomsLegalTab filters={filters} alerts={alertItems} />
        </TabsContent>
      </Tabs>

      <CustomsLineDetailSheet
        lineId={detailId}
        onClose={() => setDetailId(null)}
        onFilterImporter={filterByImporter}
        onFilterPartner={filterByPartner}
      />
      {dialog === 'import' && <CustomsImportDialog onClose={() => setDialog('')} />}
      {dialog === 'history' && <CustomsHistoryDialog onClose={() => setDialog('')} />}
    </PageContainer>
  )
}

function FilterChip({
  label,
  onRemove,
  removeLabel,
}: {
  label: string
  onRemove: () => void
  removeLabel: string
}) {
  return (
    <Badge variant="secondary" className="gap-1.5 py-1 pr-1 text-sm font-normal">
      {label}
      <button
        type="button"
        aria-label={removeLabel}
        className="rounded-full p-0.5 hover:bg-muted-foreground/15"
        onClick={onRemove}
      >
        <X className="size-3.5" />
      </button>
    </Badge>
  )
}
