/**
 * duoc-CR-784 — TỔNG HỢP THEO SẢN PHẨM (bám tab "Tổng hợp" của bản mẫu): mọi sản phẩm có định mức bao bì với chi phí bao
 * bì / chai cũ so với mới và xu hướng — Tăng (cần xem lại giá bán) · Giảm · Không đổi · Chưa có giá (thiếu giá chai).
 * Cùng công thức và luật giá cũ / mới với Tác động giá, nhưng không có giá giả định. Lọc + xếp + phân trang tại MÁY CHỦ
 * (luật §8); tham số đi kèm Xuất Excel để ra đúng thứ tự.
 */
import { FileDown, Loader2 } from 'lucide-react'
import { useMemo, useState } from 'react'
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

import { exportPackagingProductOverview } from '../api/packaging-cost-api'
import { PercentText, TrendText } from '../components/packaging-price-cells'
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
import { buildOverviewParams } from '../utils/packaging-product-overview'

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

export function PackagingProductOverviewPage() {
  const { can } = usePermission()
  const [keyword, setKeyword] = useState('')
  const [trend, setTrend] = useState<PackagingOverviewTrend>('all')
  const [advanced, setAdvanced] = useState<ImpactAdvancedFilters>(EMPTY_IMPACT_FILTERS)
  const [sortBy, setSortBy] = useState('')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [pageSize, setPageSize] = useState(DEFAULT_PAGE_SIZE)
  const [exporting, setExporting] = useState(false)
  const debouncedKeyword = useDebouncedValue(keyword, 350)
  const once = useSingleFlight()

  /** Bộ lọc + thứ tự gửi máy chủ — dùng chung cho danh sách và Xuất Excel. */
  const filterParams = useMemo(
    () => buildOverviewParams(trend, debouncedKeyword, { by: sortBy, dir: sortDir }, advanced),
    [trend, debouncedKeyword, sortBy, sortDir, advanced],
  )
  const [page, setPage] = usePageResetOnFilterChange([filterParams, pageSize])
  const overview = usePackagingProductOverview({ ...filterParams, page, page_size: pageSize })
  const rows = overview.data?.items

  const columns = useMemo(
    () =>
      buildPackagingProductColumns({
        newCostKey: 'cost_new_bottle',
        compact: true,
        extraAfterCosts: EXTRA_COLUMNS,
      }),
    [],
  )

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

  return (
    <PageContainer fill>
      <PageHeader
        title="Tổng hợp theo sản phẩm"
        description="Chi phí bao bì / chai của mọi sản phẩm có định mức, giá cũ so với giá mới (báo giá hoặc lần mua gần nhất). Sản phẩm tăng chi phí là sản phẩm cần xem lại giá bán; thiếu giá chai thì chưa tính được."
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
      <Card className="flex min-h-0 flex-1 flex-col gap-4 p-4">
        <DataTable
          //  Dòng khóa theo mã, không có `id` số: để mặc định thì lúc đang tải bảng chèn cột ID rồi gỡ, làm tách nhóm cột.
          idColumn={false}
          fillHeight
          columns={columns}
          rows={rows}
          getRowId={(row) => row.hh_code}
          isLoading={overview.isLoading}
          isError={overview.isError}
          emptyMessage={
            filtersActive
              ? 'Không có sản phẩm nào khớp bộ lọc.'
              : 'Chưa có sản phẩm nào có định mức bao bì.'
          }
          storageKey="procurement.packaging-product-overview"
          filtersActive={filtersActive}
          onResetFilters={resetFilters}
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
