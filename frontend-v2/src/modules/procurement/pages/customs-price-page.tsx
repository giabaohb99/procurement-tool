// bao-CR-470 — Tra cứu giá hải quan (bản v2). Thiết kế: doc/erp/hai-quan/04-giao-dien.md.
//
// MỘT màn hình, năm thẻ: Danh sách · Biểu đồ · Nhà nhập khẩu · So sánh · Pháp lý & thuế.
// Đại ca chốt 23/09/2026: biểu đồ nằm chung màn với danh sách, CHỈ hiện khi đã có bộ lọc
// (từ khóa hoặc mã HS); không có trang tổng quan riêng, không tính sẵn, không tác vụ định kỳ.
// Quyền: `customs_price` (đọc / ghi = nạp tệp / xóa = hoàn tác / xuất = Excel).
//
// Bộ lọc và thẻ đang mở nằm TRÊN ĐƯỜNG DẪN — gửi link cho người khác là họ thấy đúng kết
// quả đang xem. Thanh lọc dùng chung cho cả năm thẻ, đổi thẻ không mất bộ lọc.
//
// bao-CR-493 (yêu cầu phòng Thu mua 25/09): thẻ thứ sáu «Lịch sử nạp» thay hộp thoại; hàng
// «Lọc thêm» với sáu ô theo sheet 4 (nguyên tệ, giao hàng, lô nguồn, ba khoảng số); doanh
// nghiệp / đối tác chọn được NHIỀU (chip cộng dồn, id nối dấu phẩy trên URL).
import {
  BookOpen,
  ChartLine,
  ChevronDown,
  ChevronUp,
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
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { ScrollableTabsList } from '@/shared/ui/scrollable-tabs-list'
import { SearchField } from '@/shared/ui/search-field'
import { SearchSelect } from '@/shared/ui/search-select'
import { TAB_TRIGGER_UNDERLINE } from '@/shared/ui/tab-underline'
import { Tabs, TabsContent, TabsTrigger } from '@/shared/ui/tabs'

import { exportCustomsLines } from '../api/customs-api'
import { CustomsSearchHint } from '../components/customs/customs-search-hint'
import { CustomsCompareTab } from '../components/customs/customs-compare-tab'
import { CustomsNeedFilterState, CustomsNotice } from '../components/customs/customs-controls'
import { CustomsCoverageStrip } from '../components/customs/customs-coverage-strip'
import { CustomsHistoryPanel } from '../components/customs/customs-history-panel'
import { CustomsImportDialog } from '../components/customs/customs-import-dialog'
import { CustomsImportersTab } from '../components/customs/customs-importers-tab'
import { CustomsLegalTab } from '../components/customs/customs-legal-tab'
import { CustomsLineDetailDialog } from '../components/customs/customs-line-detail-dialog'
import { CustomsPriceChart } from '../components/customs/customs-price-chart'
import { CustomsSavedFilterBar } from '../components/customs/customs-saved-filter-bar'
import { CUSTOMS_LINE_COLUMNS } from '../config/customs-line-columns'
import { useCustomsSearchExplain } from '../hooks/use-customs-search-explain'
import {
  useCustomsAlerts,
  useCustomsCoverage,
  useCustomsLines,
  useCustomsOptions,
  useCustomsPermissions,
} from '../hooks/use-customs'
import type { CustomsFilters, CustomsOptionItem } from '../types/customs'
import { collectFilterParams } from '../utils/customs-saved-filter'
import {
  addNamedId,
  buildCustomsParams,
  formatBannedLabel,
  formatThresholdKg,
  hasChartFilter,
  removeNamedId,
  resolveLinesEmptyMessage,
  sortRegulationsBySeverity,
  splitNamedIds,
} from '../utils/customs'

const TABS = [
  { key: 'list', label: 'Danh sách', icon: List },
  { key: 'chart', label: 'Biểu đồ', icon: ChartLine },
  { key: 'importers', label: 'Nhà nhập khẩu', icon: Factory },
  { key: 'compare', label: 'So sánh', icon: GitCompareArrows },
  { key: 'legal', label: 'Pháp lý & thuế', icon: Landmark },
  { key: 'history', label: 'Lịch sử nạp', icon: History },
] as const

type TabKey = (typeof TABS)[number]['key']

/**
 * Hậu tố `-v2`: bố cục cũ (ẩn 22 cột) đã lưu trong máy người dùng không được thắng bố cục mới.
 * `-v3` (bao-CR-493): bề rộng cột mới đủ cho tiêu đề + hai cột VND — bản lưu cũ giữ bề rộng cũ
 * nên tiêu đề vẫn cụt, phải đổi khóa để bố cục mới thắng.
 */
//  v4: bao-CR-494 thêm cột «Phân loại» — đổi khóa để bố cục cột đã lưu không che mất cột mới.
/** bao-CR-494 — khớp `ProductKind` backend (1 Thành phẩm · 2 Nguyên liệu). */
const PRODUCT_KIND_OPTIONS = [
  { value: '1', label: 'Thành phẩm' },
  { value: '2', label: 'Nguyên liệu' },
]

const STORAGE_KEY = 'procurement.customs-lines-v4'
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
  'currency',
  'incoterm',
  'batch_id',
  'price_min',
  'price_max',
  'qty_min',
  'qty_max',
  'rate_min',
  'rate_max',
  'product_kind',
] as const
/** Sáu ô của hàng «Lọc thêm» — có giá trị thì hàng tự mở khi vào trang bằng link. */
const EXTRA_FILTER_PARAMS = [
  'currency',
  'incoterm',
  'batch_id',
  'price_min',
  'price_max',
  'qty_min',
  'qty_max',
  'rate_min',
  'rate_max',
] as const

function toSelectOptions(items: CustomsOptionItem[] | undefined) {
  return (items ?? []).map((item) => ({
    value: item.value,
    label: `${item.label ?? item.value} (${item.count})`,
  }))
}

export function CustomsPricePage() {
  const { canImport, canExport, canReadRegulations } = useCustomsPermissions()
  const { value: keyword, setValue: setKeyword, debouncedValue } = useUrlSearchParam('q')
  const [hsCode, setHsCode] = useUrlParamState('hs_code', '')
  const [origin, setOrigin] = useUrlParamState('origin', '')
  const [unit, setUnit] = useUrlParamState('unit', '')
  const [formulation, setFormulation] = useUrlParamState('formulation', '')
  const [dateFrom, dateTo, setDateRange] = useUrlRangeParam('date_from', 'date_to')
  const [currency, setCurrency] = useUrlParamState('currency', '')
  const [incoterm, setIncoterm] = useUrlParamState('incoterm', '')
  const [batchId, setBatchId] = useUrlParamState('batch_id', '')
  const [priceMin, setPriceMin] = useUrlParamState('price_min', '')
  const [priceMax, setPriceMax] = useUrlParamState('price_max', '')
  const [qtyMin, setQtyMin] = useUrlParamState('qty_min', '')
  const [qtyMax, setQtyMax] = useUrlParamState('qty_max', '')
  const [rateMin, setRateMin] = useUrlParamState('rate_min', '')
  const [rateMax, setRateMax] = useUrlParamState('rate_max', '')
  const [productKind, setProductKind] = useUrlParamState('product_kind', '')   // bao-CR-494
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
  const [importOpen, setImportOpen] = useState(false)
  const [exporting, setExporting] = useState(false)
  const [extraOpen, setExtraOpen] = useState(() =>
    EXTRA_FILTER_PARAMS.some((name) => Boolean(searchParams.get(name))),
  )
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
      currency,
      incoterm,
      batch_id: batchId,
      price_min: priceMin,
      price_max: priceMax,
      qty_min: qtyMin,
      qty_max: qtyMax,
      rate_min: rateMin,
      rate_max: rateMax,
      product_kind: productKind,
    }),
    [
      debouncedValue,
      hsCode,
      origin,
      unit,
      formulation,
      importerId,
      partnerId,
      dateFrom,
      dateTo,
      currency,
      incoterm,
      batchId,
      priceMin,
      priceMax,
      qtyMin,
      qtyMax,
      rateMin,
      rateMax,
      productKind,
    ],
  )
  const filterParams = useMemo(() => buildCustomsParams(filters), [filters])
  const searchExplain = useCustomsSearchExplain(debouncedValue)   // bao-CR-495
  const [page, setPage] = usePageResetOnFilterChange([JSON.stringify(filterParams)])

  const coverage = useCustomsCoverage()
  const options = useCustomsOptions()
  const lines = useCustomsLines({ ...filterParams, page, page_size: pageSize }, tab === 'list')
  //  Cảnh báo pháp lý chỉ so khi từ khóa từ 3 ký tự — khớp `match_alerts` của backend.
  const alerts = useCustomsAlerts(filterParams, filters.q.trim().length >= 3)
  //  bao-CR-477 — xếp nặng nhất lên đầu: dải cảnh báo chỉ bày 5 mục, nên thứ tự quyết định
  //  cái gì được nhìn thấy — hoạt chất cấm không được phép nằm ở mục thứ sáu bị cắt.
  const alertItems = useMemo(() => sortRegulationsBySeverity(alerts.data ?? []), [alerts.data])

  const chartReady = hasChartFilter(filters)
  const filtersActive = FILTER_PARAMS.some((name) => Boolean(searchParams.get(name)))
  //  bao-CR-496: chuỗi ô lọc đang áp, đúng bộ khóa `FILTER_PARAMS` — thứ được lưu thành bộ lọc.
  //  Thêm ô lọc mới vào `FILTER_PARAMS` là bộ lọc đã lưu tự mang theo, không cần sửa gì thêm.
  const savedFilterParams = collectFilterParams(searchParams, FILTER_PARAMS)
  //  bao-CR-493: nhiều doanh nghiệp / đối tác — mỗi người một chip, gỡ từng chip được.
  const importerChips = useMemo(() => splitNamedIds(importerId, importerName), [importerId, importerName])
  const partnerChips = useMemo(() => splitNamedIds(partnerId, partnerName), [partnerId, partnerName])

  function clearFilters() {
    setKeyword('')
    setUrlParams(Object.fromEntries(FILTER_PARAMS.map((name) => [name, null])))
  }

  //  bao-CR-496: nạp một bộ lọc đã lưu. Ô tìm `q` có state riêng (gõ xong mới hoãn ghi lên URL),
  //  nên phải đặt thẳng cả nó — cùng lý do `clearFilters` ngay trên gọi `setKeyword('')`. Chỉ
  //  đổi URL thì ô tìm vẫn hiện chữ cũ trong khi bảng đã lọc theo chữ mới.
  function applySavedFilter(next: Record<string, string | null>) {
    setKeyword(next.q ?? '')
    setUrlParams(next)
  }

  //  Chọn thêm từ thẻ Nhà nhập khẩu / hộp chi tiết dòng: CỘNG DỒN vào bộ lọc, không thay thế.
  function filterByImporter(id: number, name: string) {
    setDetailId(null)
    const next = addNamedId(importerId, importerName, id, name)
    setUrlParams({ importer_id: next.ids, importer_name: next.names || null, tab: null })
  }

  function filterByPartner(id: number, name: string) {
    setDetailId(null)
    const next = addNamedId(partnerId, partnerName, id, name)
    setUrlParams({ partner_id: next.ids, partner_name: next.names || null, tab: null })
  }

  function dropImporter(id: string) {
    const next = removeNamedId(importerId, importerName, id)
    setUrlParams({ importer_id: next.ids || null, importer_name: next.names || null })
  }

  function dropPartner(id: string) {
    const next = removeNamedId(partnerId, partnerName, id)
    setUrlParams({ partner_id: next.ids || null, partner_name: next.names || null })
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
        title="Tra cứu thị trường"
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
            <Button type="button" variant="outline" onClick={() => setTab('history')}>
              <History className="size-4" />
              Lịch sử nạp
            </Button>
            {canImport && (
              <Button type="button" onClick={() => setImportOpen(true)}>
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
          {/* bao-CR-494 — nhãn tự gắn Thành phẩm / Nguyên liệu. */}
          <div className="w-44 max-md:w-full">
            <SearchSelect
              value={productKind}
              onChange={setProductKind}
              options={PRODUCT_KIND_OPTIONS}
              placeholder="Thành phẩm + Nguyên liệu"
              searchPlaceholder="Tìm phân loại…"
              clearable
            />
          </div>
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
          <Button
            type="button"
            variant="ghost"
            aria-expanded={extraOpen}
            onClick={() => setExtraOpen((open) => !open)}
          >
            {extraOpen ? <ChevronUp className="size-4" /> : <ChevronDown className="size-4" />}
            Lọc thêm
          </Button>
          {filtersActive && (
            <Button type="button" variant="ghost" onClick={clearFilters}>
              <FilterX className="size-4" />
              Xóa lọc
            </Button>
          )}
        </div>

        {/* bao-CR-495 — ô tìm hiểu từ CÓ / KHÔNG CÓ, nồng độ, đồng nghĩa: nói cho người dùng biết. */}
        <CustomsSearchHint query={debouncedValue} explain={searchExplain.data} />

        {/* bao-CR-496 — bộ lọc đặt tên, RIÊNG từng tài khoản, lưu ở máy chủ (đổi máy không mất).
             Hàng riêng chứ không chen vào hàng trên: thanh có tới bốn nút, hàng trên đã bảy ô. */}
        <CustomsSavedFilterBar
          currentParams={savedFilterParams}
          filterNames={FILTER_PARAMS}
          onApply={applySavedFilter}
        />

        {extraOpen && (
          /* bao-CR-493 — sáu ô theo sheet 4 của yêu cầu phòng Thu mua. Khoảng số nhập chữ, backend
             bỏ qua ô rác; giá so trên GIÁ HIỆU LỰC (điều chỉnh nếu có). */
          <div className="flex flex-wrap items-center gap-2" aria-label="Lọc thêm">
            <div className="w-36 max-md:w-full">
              <SearchSelect
                value={currency}
                onChange={setCurrency}
                options={toSelectOptions(options.data?.currencies)}
                placeholder="Nguyên tệ"
                searchPlaceholder="Tìm nguyên tệ…"
                clearable
              />
            </div>
            <div className="w-40 max-md:w-full">
              <SearchSelect
                value={incoterm}
                onChange={setIncoterm}
                options={toSelectOptions(options.data?.incoterms)}
                placeholder="Điều kiện giao hàng"
                searchPlaceholder="Tìm điều kiện…"
                clearable
              />
            </div>
            <div className="w-56 max-md:w-full">
              <SearchSelect
                value={batchId}
                onChange={setBatchId}
                options={toSelectOptions(options.data?.batches)}
                placeholder="Tệp nguồn (lô nạp)"
                searchPlaceholder="Tìm tệp…"
                clearable
              />
            </div>
            <RangeFilter label="Đơn giá USD" from={priceMin} to={priceMax} onFrom={setPriceMin} onTo={setPriceMax} />
            <RangeFilter label="Lượng" from={qtyMin} to={qtyMax} onFrom={setQtyMin} onTo={setQtyMax} />
            <RangeFilter label="Tỷ giá USD" from={rateMin} to={rateMax} onFrom={setRateMin} onTo={setRateMax} />
          </div>
        )}

        {(importerChips.length > 0 || partnerChips.length > 0) && (
          <div className="flex flex-wrap gap-2">
            {importerChips.map((chip) => (
              <FilterChip
                key={`importer-${chip.id}`}
                label={`Doanh nghiệp: ${chip.name || `#${chip.id}`}`}
                onRemove={() => dropImporter(chip.id)}
                removeLabel={`Bỏ lọc doanh nghiệp ${chip.name || chip.id}`}
              />
            ))}
            {partnerChips.map((chip) => (
              <FilterChip
                key={`partner-${chip.id}`}
                label={`Đối tác: ${chip.name || `#${chip.id}`}`}
                onRemove={() => dropPartner(chip.id)}
                removeLabel={`Bỏ lọc đối tác ${chip.name || chip.id}`}
              />
            ))}
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
                {alert.cas_no ? ` (CAS ${alert.cas_no})` : ''} —{' '}
                {alert.list_code === 10 && (
                  <b className="font-bold">{formatBannedLabel(alert.banned_year)}. </b>
                )}
                {alert.list_code !== 10 && formatThresholdKg(alert.threshold_kg) && (
                  <b className="font-bold">
                    Ngưỡng {formatThresholdKg(alert.threshold_kg)}.{' '}
                  </b>
                )}
                {alert.obligation}
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

        <TabsContent value="history" className="mt-2">
          <CustomsHistoryPanel />
        </TabsContent>
      </Tabs>

      <CustomsLineDetailDialog
        lineId={detailId}
        onClose={() => setDetailId(null)}
        onFilterImporter={filterByImporter}
        onFilterPartner={filterByPartner}
      />
      {importOpen && <CustomsImportDialog onClose={() => setImportOpen(false)} />}
    </PageContainer>
  )
}

/** Cặp ô «từ – tới» cho một khoảng số; để trống một đầu là chỉ chặn đầu kia. */
function RangeFilter({
  label,
  from,
  to,
  onFrom,
  onTo,
}: {
  label: string
  from: string
  to: string
  onFrom: (value: string) => void
  onTo: (value: string) => void
}) {
  return (
    <div className="flex items-center gap-1 text-sm" role="group" aria-label={label}>
      <span className="text-muted-foreground">{label}</span>
      <Input
        inputMode="decimal"
        className="h-9 w-24"
        value={from}
        placeholder="từ"
        aria-label={`${label} từ`}
        onChange={(event) => onFrom(event.target.value)}
      />
      <span className="text-muted-foreground">–</span>
      <Input
        inputMode="decimal"
        className="h-9 w-24"
        value={to}
        placeholder="tới"
        aria-label={`${label} tới`}
        onChange={(event) => onTo(event.target.value)}
      />
    </div>
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
