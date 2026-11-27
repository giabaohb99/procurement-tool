/**
 * duoc-CR-784 — BẢNG GIÁ VTBB (bám `renderPrices` của bản mẫu): mỗi mã một dòng với số lần mua, hai lần mua
 * gần nhất, báo giá mới nhất, giá cũ / mới theo luật của kế hoạch, min–max theo khoảng ngày
 * và số sản phẩm đang dùng. Phân trang + xếp tại MÁY CHỦ (luật §8) — tham số xếp đi kèm bộ lọc
 * nên Xuất Excel ra đúng thứ tự đang xem. Nút từng dòng: Báo giá mới.
 */
import { Plus } from 'lucide-react'
import { useCallback, useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { DataTable } from '@/shared/data-table'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'

import { PackagingExportExcelButton } from '../components/packaging-header-buttons'
import { exportPackagingPriceList } from '../api/packaging-cost-api'
import {
  PackagingPriceListToolbar,
  type PriceListFilters,
} from '../components/packaging-price-list-toolbar'
import { PackagingExcelImportButton } from '../components/packaging-excel-import-button'
import { PackagingPriceRowCard } from '../components/packaging-price-row-card'
import { PackagingQuoteDialog } from '../components/packaging-quote-dialog'
import { PACKAGING_QUOTE_IMPORT } from '../config/packaging-excel-imports'
import { usePackagingCodeOptions } from '../hooks/use-packaging-impact'
import { usePackagingPriceList } from '../hooks/use-packaging-price-list'
import { usePackagingPriceListColumns } from '../hooks/use-packaging-price-list-columns'
import type { PackagingPriceListParams, PackagingPriceRow } from '../types/packaging-cost-types'
import { collectPackagingGroups, sortPackagingCodeOptions } from '../utils/packaging-code-match'
import { buildPriceListUrlSearch, parsePriceListUrlState } from '../utils/packaging-list-url-state'

const EMPTY_FILTERS: PriceListFilters = { codes: [], group: '', scope: 'bom' }

export function PackagingPriceListPage() {
  const { can } = usePermission()
  const isMobile = useIsMobile()
  const [searchParams, setSearchParams] = useSearchParams()
  //  Bộ lọc / cột xếp / trang sống trên URL (F5 / gửi link mở lại đúng chỗ): đọc MỘT lần lúc mở màn, sau đó state là nguồn
  //  và URL đi theo (effect bên dưới, `replace` — gõ ô tìm không đẻ ra cả chục mục lịch sử của nút Quay lại).
  const [initial] = useState(() => parsePriceListUrlState(searchParams))
  const [filters, setFilters] = useState<PriceListFilters>(initial.filters)
  const [range, setRange] = useState({ from: initial.from, to: initial.to })
  const [sortBy, setSortBy] = useState(initial.sortBy)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(initial.sortDir)
  const [pageSize, setPageSize] = useState(initial.pageSize)
  const [quoteCode, setQuoteCode] = useState<string | null>(null)
  const [exporting, setExporting] = useState(false)
  const once = useSingleFlight()

  /** Bộ lọc + thứ tự gửi máy chủ — dùng chung cho danh sách và Xuất Excel. */
  const filterParams = useMemo<PackagingPriceListParams>(
    () => ({
      code: filters.codes.length ? filters.codes : undefined,
      group: filters.group || undefined,
      scope: filters.scope,
      date_from: range.from || undefined,
      date_to: range.to || undefined,
      //  Nhịp thứ ba của tiêu đề cột trả khóa rỗng = thôi xếp → KHÔNG gửi, để máy chủ xếp mặc định.
      ...(sortBy ? { sort_by: sortBy, sort_dir: sortDir } : {}),
    }),
    [filters.codes, filters.group, filters.scope, range, sortBy, sortDir],
  )
  const [page, setPage] = usePageResetOnFilterChange([filterParams, pageSize], initial.page)
  const list = usePackagingPriceList({ ...filterParams, page, page_size: pageSize })

  const urlSearch = buildPriceListUrlSearch({
    filters,
    from: range.from,
    to: range.to,
    sortBy,
    sortDir,
    page,
    pageSize,
  })
  useEffect(() => {
    if (urlSearch !== searchParams.toString()) {
      setSearchParams(new URLSearchParams(urlSearch), { replace: true })
    }
  }, [urlSearch, searchParams, setSearchParams])

  //  Danh sách mã của ô chọn mã = mọi mã có trong sổ giá (27/11/2026); nhóm cho chip lấy từ chính danh sách đó.
  const optionsQuery = usePackagingCodeOptions(true, 'all')
  const codeOptions = useMemo(() => sortPackagingCodeOptions(optionsQuery.data ?? []), [optionsQuery.data])
  const groups = useMemo(() => collectPackagingGroups(codeOptions), [codeOptions])

  const openQuote = useCallback((row: PackagingPriceRow) => setQuoteCode(row.code), [])
  const canQuote = can('packaging_price_list', 'create')
  const columns = usePackagingPriceListColumns({
    canQuote,
    onQuote: openQuote,
  })

  const filtersActive =
    filters.codes.length > 0 ||
    filters.group !== '' ||
    filters.scope !== 'bom' ||
    Boolean(range.from || range.to)

  const exportExcel = () =>
    once(async () => {
      setExporting(true)
      try {
        await exportPackagingPriceList(filterParams)
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Không xuất được tệp Excel')
      } finally {
        setExporting(false)
      }
    })

  return (
    //  `fill` chỉ từ `md`: ở khổ hẹp bảng thành danh sách thẻ dài, nhét vào khe cao cố định là cuộn LỒNG (xem crud-list-page).
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Bảng giá VTBB"
        //  Câu giới thiệu ẩn ở khổ điện thoại (cùng nếp các màn CRUD): đọc một lần rồi thôi mà ăn ba bốn dòng đầu màn.
        description={
          isMobile
            ? undefined
            : 'Giá cũ / mới từng mã vật tư bao bì: có báo giá thì giá mới là báo giá, không thì là lần mua gần nhất. Đơn vị VNĐ, chưa VAT.'
        }
        actions={
          <>
            <DateRangePicker
              from={range.from}
              to={range.to}
              placeholder="Khoảng ngày tính min – max"
              //  Màn này đầu hàng còn ba nút (Báo giá mới · Nhập báo giá · Xuất Excel): ô ngày chiếm trọn hàng riêng, chia
              //  hàng với chúng thì bị bóp còn mỗi biểu tượng lịch.
              className="max-md:basis-full"
              onChange={(from, to) => setRange({ from, to })}
            />
            {canQuote && (
              <Button type="button" onClick={() => setQuoteCode('')}>
                <Plus />
                Báo giá mới
              </Button>
            )}
            <PackagingExcelImportButton kind={PACKAGING_QUOTE_IMPORT} />
            {can('packaging_price_list', 'export') && (
              <PackagingExportExcelButton exporting={exporting} onClick={() => void exportExcel()} />
            )}
          </>
        }
      />
      <Card className="flex min-h-0 flex-1 flex-col gap-4 p-4 max-md:gap-2 max-md:p-3">
        <DataTable
          //  Dòng khóa theo mã, không có `id` số: để mặc định thì lúc đang tải bảng chèn cột ID rồi gỡ, làm tách nhóm cột.
          idColumn={false}
          fillHeight
          columns={columns}
          rows={list.data?.items}
          getRowId={(row) => row.code}
          isLoading={list.isLoading}
          isError={list.isError}
          emptyMessage={
            filtersActive
              ? 'Không có mã nào khớp bộ lọc.'
              : 'Chưa có mã vật tư bao bì nào trong định mức.'
          }
          storageKey="procurement.packaging-price-list"
          mobileCard={(row) => (
            <PackagingPriceRowCard row={row} onQuote={canQuote ? openQuote : undefined} />
          )}
          mobileSort
          filtersActive={filtersActive}
          onResetFilters={() => {
            setFilters(EMPTY_FILTERS)
            setRange({ from: '', to: '' })
          }}
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={(by, dir) => {
            setSortBy(by)
            setSortDir(dir)
          }}
          toolbar={
            <PackagingPriceListToolbar
              filters={filters}
              groups={groups}
              codeOptions={codeOptions}
              codeOptionsLoading={optionsQuery.isLoading}
              onChange={setFilters}
            />
          }
          pagination={{
            page,
            pageSize,
            total: list.data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'mã',
          }}
        />
      </Card>

      {quoteCode !== null && (
        <PackagingQuoteDialog
          open
          defaultCode={quoteCode || undefined}
          onOpenChange={(open) => !open && setQuoteCode(null)}
        />
      )}
    </PageContainer>
  )
}
