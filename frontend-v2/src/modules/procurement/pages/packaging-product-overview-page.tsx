/**
 * duoc-CR-784 — TỔNG HỢP THEO SẢN PHẨM (bám tab "Tổng hợp" của bản mẫu): mọi sản phẩm có định mức bao bì với chi phí bao
 * bì / chai cũ so với mới và xu hướng — Tăng (cần xem lại giá bán) · Giảm · Không đổi · Chưa có giá (thiếu giá chai).
 * Cùng công thức và luật giá cũ / mới với Tác động giá, nhưng không có giá giả định. Lọc + xếp + phân trang tại MÁY CHỦ
 * (luật §8); tham số đi kèm Xuất Excel để ra đúng thứ tự.
 */
import { useEffect, useMemo, useState } from 'react'
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

import { PackagingExportExcelButton } from '../components/packaging-header-buttons'
import { exportPackagingProductOverview } from '../api/packaging-cost-api'
import { PercentText, TrendText } from '../components/packaging-price-cells'
import { PackagingProductCard } from '../components/packaging-product-card'
import { PackagingProductOverviewToolbar } from '../components/packaging-product-overview-toolbar'
import {
  buildPackagingProductColumns,
  type PackagingProductColumn,
} from '../config/packaging-product-columns'
import { usePackagingProductOverview } from '../hooks/use-packaging-product-overview'
import type { PackagingOverviewTrend } from '../types/packaging-cost-types'
import {
  EMPTY_IMPACT_FILTERS,
  countAdvancedFilters,
  type ImpactAdvancedFilters,
} from '../utils/packaging-impact-filters'
import {
  buildOverviewParams,
  buildOverviewUrlSearch,
  parseOverviewUrlState,
} from '../utils/packaging-product-overview'

const DEFAULT_PAGE_SIZE = 100

/** "% chênh" và "Xu hướng" đứng ngay sau các cột chi phí — Tác động giá không có. */
const EXTRA_COLUMNS: PackagingProductColumn[] = [
  {
    key: 'pct',
    header: '% chênh',
    width: 104,
    align: 'right',
    sortable: true,
    sortDescFirst: true,
    cell: (row) => <PercentText value={row.pct} />,
  },
  {
    key: 'trend',
    header: 'Xu hướng',
    width: 100,
    cell: (row) => <TrendText trend={row.trend} />,
  },
]

/** Cột của bảng — không phụ thuộc gì của màn nên dựng một lần. */
const OVERVIEW_COLUMNS = buildPackagingProductColumns({
  newCostKey: 'cost_new_bottle',
  compact: true,
  extraAfterCosts: EXTRA_COLUMNS,
})
/** Khóa các cột xếp được — để kiểm `sort_by` đọc từ URL (luật §8: máy chủ chỉ nhận khóa của cột). */
const OVERVIEW_SORT_KEYS = OVERVIEW_COLUMNS.filter((column) => column.sortable).map(
  (column) => column.sortKey ?? column.key,
)

export function PackagingProductOverviewPage() {
  const { can } = usePermission()
  const isMobile = useIsMobile()
  const [searchParams, setSearchParams] = useSearchParams()
  //  Bộ lọc sống trên URL (F5 / gửi link mở lại đúng bộ lọc, duoc-CR-784): đọc một lần lúc mở, sau đó URL đi theo state.
  const [initial] = useState(() => parseOverviewUrlState(searchParams, OVERVIEW_SORT_KEYS))
  const [keyword, setKeyword] = useState(initial.q)
  const [trend, setTrend] = useState<PackagingOverviewTrend>(initial.trend)
  const [advanced, setAdvanced] = useState<ImpactAdvancedFilters>(initial.advanced)
  const [sortBy, setSortBy] = useState(initial.sortBy)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(initial.sortDir)
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [exporting, setExporting] = useState(false)
  const debouncedKeyword = useDebouncedValue(keyword, 350)
  const once = useSingleFlight()

  /** Bộ lọc + thứ tự gửi máy chủ — dùng chung cho danh sách và Xuất Excel. */
  const filterParams = useMemo(
    () => buildOverviewParams(trend, debouncedKeyword, { by: sortBy, dir: sortDir }, advanced),
    [trend, debouncedKeyword, sortBy, sortDir, advanced],
  )
  const [page, setPage] = usePageResetOnFilterChange([filterParams, pageSize], initial.page)
  const overview = usePackagingProductOverview({ ...filterParams, page, page_size: pageSize })
  const rows = overview.data?.items

  const urlSearch = buildOverviewUrlSearch({ q: debouncedKeyword, trend, advanced, sortBy, sortDir, page })
  useEffect(() => {
    if (urlSearch !== searchParams.toString()) {
      setSearchParams(new URLSearchParams(urlSearch), { replace: true })
    }
  }, [urlSearch, searchParams, setSearchParams])

  const filtersActive =
    trend !== 'all' ||
    keyword.trim() !== '' ||
    countAdvancedFilters(advanced, 'overview') > 0
  const resetFilters = () => {
    setKeyword('')
    setTrend('all')
    setAdvanced(EMPTY_IMPACT_FILTERS)
  }

  const exportExcel = () =>
    once(async () => {
      setExporting(true)
      try {
        await exportPackagingProductOverview(filterParams)
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Không xuất được tệp Excel')
      } finally {
        setExporting(false)
      }
    })

  const exportButton = can('packaging_product_summary', 'export') && (
    <PackagingExportExcelButton exporting={exporting} onClick={() => void exportExcel()} />
  )

  return (
    //  `fill` chỉ từ `md`: ở khổ hẹp bảng thành danh sách thẻ dài, nhét vào khe cao cố định là cuộn LỒNG (xem crud-list-page).
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Tổng hợp theo sản phẩm"
        //  Câu giới thiệu ẩn ở khổ điện thoại (cùng nếp các màn CRUD): đọc một lần rồi thôi mà ăn ba bốn dòng đầu màn.
        description={
          isMobile
            ? undefined
            : 'Chi phí bao bì / chai của mọi sản phẩm có định mức, giá cũ so với giá mới (báo giá hoặc lần mua gần nhất). Sản phẩm tăng chi phí là sản phẩm cần xem lại giá bán; thiếu giá chai thì chưa tính được. Đơn vị VNĐ, chưa VAT.'
        }
        //  Khổ điện thoại: nút Xuất Excel dời xuống cụm nút của bảng (cạnh Tải lại) — một mình nó một hàng đầu màn là dải
        //  trống người chủ chê (26/11/2026).
        actions={!isMobile && exportButton}
      />
      <Card className="flex min-h-0 flex-1 flex-col gap-4 p-4 max-md:gap-2 max-md:p-3">
        <DataTable
          //  Dòng khóa theo mã, không có `id` số: để mặc định thì lúc đang tải bảng chèn cột ID rồi gỡ, làm tách nhóm cột.
          idColumn={false}
          fillHeight
          toolbarEnd={isMobile ? exportButton : undefined}
          columns={OVERVIEW_COLUMNS}
          rows={rows}
          getRowId={(row) => row.fg_code}
          isLoading={overview.isLoading}
          isError={overview.isError}
          emptyMessage={
            filtersActive
              ? 'Không có sản phẩm nào khớp bộ lọc.'
              : 'Chưa có sản phẩm nào có định mức bao bì.'
          }
          storageKey="procurement.packaging-product-overview"
          mobileCard={(row) => <PackagingProductCard row={row} variant="overview" />}
          mobileSort
          filtersActive={filtersActive}
          onResetFilters={resetFilters}
          toolbarActionsClassName="order-2"
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={(by, dir) => {
            setSortBy(by)
            setSortDir(dir)
          }}
          toolbar={
            <PackagingProductOverviewToolbar
              keyword={keyword}
              onKeywordChange={setKeyword}
              trend={trend}
              onTrendChange={setTrend}
              counts={overview.data?.counts}
              advanced={advanced}
              onAdvancedChange={setAdvanced}
            />
          }
          pagination={{
            page,
            pageSize,
            total: overview.data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'sản phẩm',
          }}
        />
      </Card>
    </PageContainer>
  )
}
