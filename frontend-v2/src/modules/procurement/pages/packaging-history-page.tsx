/**
 * duoc-CR-784 — LỊCH SỬ MUA HÀNG của cụm Giá bao bì (bản mẫu `histRows` + `renderLast5`): từng lần mua của mã VTBB, hoặc
 * của các thành phần trong định mức của một / nhiều sản phẩm; kèm dòng KPI và biểu đồ "Diễn biến đơn giá" khi chọn đúng một mã.
 *
 * Lịch sử là bản chụp BẤT BIẾN của sổ giá — không có ô sửa đơn giá (sai thì sửa ở ĐMH / nguồn nạp). Lọc + xếp + phân trang tại
 * MÁY CHỦ (luật §8). Lựa chọn mã nằm ở URL (`?codes=A,B` · `?hh=HH1,HH2` · `mode`) để các bảng khác dẫn thẳng vào được.
 */
import { FileDown, Loader2 } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { DataTable } from '@/shared/data-table'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'

import { exportPackagingHistory } from '../api/packaging-cost-api'
import { PackagingHistoryChart } from '../components/packaging-history-chart'
import { PackagingHistorySummary } from '../components/packaging-history-summary'
import { PackagingHistoryToolbar } from '../components/packaging-history-toolbar'
import { usePackagingCodeOptions } from '../hooks/use-packaging-impact'
import { usePackagingHhOptions, usePackagingHistory } from '../hooks/use-packaging-history'
import { usePackagingHistoryColumns } from '../hooks/use-packaging-history-columns'
import type { PackagingCodeOption } from '../types/packaging-cost-types'
import { sortPackagingCodeOptions } from '../utils/packaging-code-match'
import {
  buildHistoryParams,
  buildHistorySearch,
  EMPTY_HISTORY_FILTERS,
  parseHistorySearch,
  type PackagingHistoryFilters,
  type PackagingHistorySelection,
} from '../utils/packaging-history'

export function PackagingHistoryPage() {
  const { can } = usePermission()
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
  const hhOptionsQuery = usePackagingHhOptions(isProduct)
  const codeOptions = useMemo(
    () => sortPackagingCodeOptions(codeOptionsQuery.data ?? []),
    [codeOptionsQuery.data],
  )
  const productOptions = useMemo<PackagingCodeOption[]>(
    () => (hhOptionsQuery.data ?? []).map((item) => ({ ...item, group: '', usage: 0, new: null })),
    [hhOptionsQuery.data],
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
    <PageContainer fill>
      <PageHeader
        title="Lịch sử mua hàng"
        description="Từng lần mua của mã vật tư bao bì hoặc của thành phần trong định mức sản phẩm, mới nhất trước. Giá chưa VAT (VND), là bản chụp lúc mua: xanh = đắt hơn lần trước, đỏ = rẻ hơn."
        actions={
          can('packaging_cost', 'export') && (
            <Button
              type="button"
              variant="outline"
              disabled={exporting}
              onClick={() => void exportExcel()}
            >
              {exporting ? <Loader2 className="animate-spin" /> : <FileDown />}
              Xuất Excel
            </Button>
          )
        }
      />
      <Card className="flex min-h-0 flex-1 flex-col gap-3 p-4">
        <PackagingHistoryToolbar
          selection={selection}
          onSelectionChange={changeSelection}
          filters={filters}
          onFiltersChange={setFilters}
          codeOptions={codeOptions}
          productOptions={productOptions}
          optionsLoading={isProduct ? hhOptionsQuery.isLoading : codeOptionsQuery.isLoading}
          suppliers={list.data?.suppliers ?? []}
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
          //  Dòng khóa theo id dòng sổ giá nhưng không phải cột "ID" của bản ghi: tắt cột ID tự thêm.
          idColumn={false}
          fillHeight
          columns={columns}
          rows={list.data?.items}
          getRowId={(row) => String(row.id)}
          isLoading={list.isLoading}
          isError={list.isError}
          emptyMessage={
            filtersActive
              ? 'Không có lần mua nào khớp bộ lọc.'
              : 'Chưa có lần mua nào cho lựa chọn này.'
          }
          storageKey={`procurement.packaging-history.${isProduct ? 'product' : 'code'}`}
          filtersActive={filtersActive}
          onResetFilters={() => setFilters(EMPTY_HISTORY_FILTERS)}
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={(by, dir) => {
            setSortBy(by)
            setSortDir(dir)
          }}
          rowClassName={(row) => (row.price === 0 ? 'text-muted-foreground' : undefined)}
          toolbar={
            <PackagingHistorySummary
              stats={list.data?.stats}
              singleCode={series !== null}
              fetching={list.isFetching && !list.isLoading}
            />
          }
          pagination={{
            page,
            pageSize,
            total: list.data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'lần mua',
          }}
        />
      </Card>
    </PageContainer>
  )
}
