/**
 * duoc-CR-784 — LỊCH SỬ MUA HÀNG của cụm Giá bao bì (bản mẫu `histRows` + `renderLast5`): từng lần mua của mã VTBB, hoặc
 * của các thành phần trong định mức của một / nhiều sản phẩm; kèm dòng KPI và biểu đồ "Diễn biến đơn giá" khi chọn đúng một mã.
 *
 * Lịch sử là bản chụp BẤT BIẾN của sổ giá — không có ô sửa đơn giá (sai thì sửa ở ĐMH / nguồn nạp). Lọc + xếp + phân trang tại
 * MÁY CHỦ (luật §8). Lựa chọn mã nằm ở URL (`?codes=A,B` · `?fg=HH1,HH2` · `mode`) để các bảng khác dẫn thẳng vào được.
 */
import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { DataTable } from '@/shared/data-table'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'

import { PackagingExportExcelButton, PackagingPrintButton } from '../components/packaging-header-buttons'
import { exportPackagingHistory } from '../api/packaging-cost-api'
import { PackagingHistoryCard } from '../components/packaging-history-card'
import { PackagingHistoryChart } from '../components/packaging-history-chart'
import { PackagingHistorySummary } from '../components/packaging-history-summary'
import { PackagingExcelImportButton } from '../components/packaging-excel-import-button'
import { PackagingHistoryToolbar } from '../components/packaging-history-toolbar'
import { PACKAGING_MISA_IMPORT } from '../config/packaging-excel-imports'
import { usePackagingCodeOptions } from '../hooks/use-packaging-impact'
import { usePackagingFgOptions, usePackagingHistory } from '../hooks/use-packaging-history'
import { usePackagingHistoryColumns } from '../hooks/use-packaging-history-columns'
import type { PackagingCodeOption } from '../types/packaging-cost-types'
import { sortPackagingCodeOptions } from '../utils/packaging-code-match'
import {
  buildHistoryParams,
  buildHistorySearch,
  EMPTY_HISTORY_FILTERS,
  historyRowKey,
  parseHistorySearch,
  type PackagingHistoryFilters,
  type PackagingHistorySelection,
} from '../utils/packaging-history'
import { packagingHistoryPrintHref } from '../utils/packaging-history-print'

export function PackagingHistoryPage() {
  const { can } = usePermission()
  const isMobile = useIsMobile()
  const [searchParams, setSearchParams] = useSearchParams()
  const selection = useMemo(() => parseHistorySearch(searchParams), [searchParams])
  const [filters, setFilters] = useState<PackagingHistoryFilters>(EMPTY_HISTORY_FILTERS)
  const [sortBy, setSortBy] = useState('date')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [pageSize, setPageSize] = useState(50)
  const [exporting, setExporting] = useState(false)
  const debouncedQ = useDebouncedValue(filters.q, 350)
  const once = useSingleFlight()
  const isProduct = selection.mode === 'product'

  const codeOptionsQuery = usePackagingCodeOptions()
  const fgOptionsQuery = usePackagingFgOptions(isProduct)
  const codeOptions = useMemo(
    () => sortPackagingCodeOptions(codeOptionsQuery.data ?? []),
    [codeOptionsQuery.data],
  )
  const productOptions = useMemo<PackagingCodeOption[]>(
    () => (fgOptionsQuery.data ?? []).map((item) => ({ ...item, group: '', usage: 0, new: null })),
    [fgOptionsQuery.data],
  )

  /** Bộ lọc + thứ tự gửi máy chủ — dùng chung cho danh sách và Xuất Excel. */
  const filterParams = useMemo(
    () => buildHistoryParams(selection, filters, debouncedQ, { by: sortBy, dir: sortDir }),
    [selection, filters, debouncedQ, sortBy, sortDir],
  )
  const [page, setPage] = usePageResetOnFilterChange([filterParams, pageSize])
  const list = usePackagingHistory({ ...filterParams, page, page_size: pageSize })
  const series = list.data?.series ?? null
  const columns = usePackagingHistoryColumns(isProduct, series !== null)

  const changeSelection = (next: PackagingHistorySelection) =>
    setSearchParams(buildHistorySearch(next), { replace: true })

  const filtersActive = JSON.stringify(filters) !== JSON.stringify(EMPTY_HISTORY_FILTERS)

  const exportExcel = () =>
    once(async () => {
      setExporting(true)
      try {
        await exportPackagingHistory(filterParams)
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
        title="Lịch sử mua hàng"
        //  Câu giới thiệu ẩn ở khổ điện thoại (cùng nếp các màn CRUD): đọc một lần rồi thôi mà ăn ba bốn dòng đầu màn.
        description={
          isMobile
            ? undefined
            : 'Từng lần mua của mã vật tư bao bì hoặc của thành phần trong định mức sản phẩm, mới nhất trước. Giá VNĐ, chưa VAT, là bản chụp lúc mua: xanh = đắt hơn lần trước, đỏ = rẻ hơn.'
        }
        actions={
          <>
            {/* In = xem, nên gác theo quyền đọc (không đòi quyền xuất). Mở tab mới với ĐÚNG bộ lọc đang áp; trang in tự nạp đủ mọi dòng. */}
            {can('packaging_cost', 'read') && (
              <PackagingPrintButton href={packagingHistoryPrintHref(filterParams)} />
            )}
            <PackagingExcelImportButton kind={PACKAGING_MISA_IMPORT} />
            {can('packaging_cost', 'export') && (
              <PackagingExportExcelButton exporting={exporting} onClick={() => void exportExcel()} />
            )}
          </>
        }
      />
      <Card className="flex min-h-0 flex-1 flex-col gap-3 p-4 max-md:gap-2 max-md:p-3">
        <PackagingHistoryToolbar
          selection={selection}
          onSelectionChange={changeSelection}
          filters={filters}
          onFiltersChange={setFilters}
          codeOptions={codeOptions}
          productOptions={productOptions}
          optionsLoading={isProduct ? fgOptionsQuery.isLoading : codeOptionsQuery.isLoading}
          suppliers={list.data?.suppliers ?? []}
        />
        {/* Thẻ số liệu đặt TRÊN biểu đồ (người chủ chốt 21/11/2026), không còn nằm trong thanh công cụ của bảng. */}
        <PackagingHistorySummary
          stats={list.data?.stats}
          singleCode={series !== null}
          mode={selection.mode}
          selectedCount={isProduct ? selection.fg.length : selection.codes.length}
        />
        {series && series.length > 0 && (
          <PackagingHistoryChart
            series={series}
            subject={[list.data?.items[0]?.code, list.data?.items[0]?.name]
              .filter(Boolean)
              .join(' · ')}
          />
        )}
        <DataTable
          //  Dòng khóa theo (sản phẩm, id dòng sổ giá) nhưng không phải cột "ID" của bản ghi: tắt cột ID tự thêm.
          idColumn={false}
          fillHeight
          columns={columns}
          rows={list.data?.items}
          getRowId={historyRowKey}
          isLoading={list.isLoading}
          isError={list.isError}
          emptyMessage={
            filtersActive
              ? 'Không có lần mua nào khớp bộ lọc.'
              : 'Chưa có lần mua nào cho lựa chọn này.'
          }
          storageKey={`procurement.packaging-history.${isProduct ? 'product' : 'code'}`}
          mobileCard={(row) => <PackagingHistoryCard row={row} productMode={isProduct} />}
          mobileSort
          filtersActive={filtersActive}
          onResetFilters={() => setFilters(EMPTY_HISTORY_FILTERS)}
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={(by, dir) => {
            setSortBy(by)
            setSortDir(dir)
          }}
          rowClassName={(row) => (row.price === 0 ? 'text-muted-foreground' : undefined)}
          pagination={{
            page,
            pageSize,
            total: list.data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: isProduct ? 'dòng' : 'lần mua',
          }}
        />
      </Card>
    </PageContainer>
  )
}
