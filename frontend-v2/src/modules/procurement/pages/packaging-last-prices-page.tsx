/**
 * duoc-CR-784 — GIÁ MUA GẦN NHẤT (bám `renderMatrix` của bản mẫu, mở rộng): mỗi mã VTBB một dòng với ngày mua, nhà cung
 * cấp, đơn giá của n lần mua có giá gần nhất (n = 3 / 5 / 10; xanh = đắt hơn lần cũ kế bên, đỏ = rẻ hơn), biến động lần 1
 * so lần 2 / lần n và giá trung bình. Lọc + xếp + phân trang tại MÁY CHỦ (luật §8); tham số đi kèm Xuất Excel để ra đúng
 * thứ tự. Tiêu đề gộp nhóm cột do `DataTable` vẽ (`group` của cột).
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

import { exportPackagingLastPrices } from '../api/packaging-cost-api'
import {
  PackagingLastPricesToolbar,
  type LastPricesFilters,
} from '../components/packaging-last-prices-toolbar'
import { usePackagingLastPrices } from '../hooks/use-packaging-last-prices'
import { usePackagingLastPricesColumns } from '../hooks/use-packaging-last-prices-columns'
import {
  buildLastPricesParams,
  LAST_PRICE_DEFAULT_N,
  sortKeyOutsideN,
} from '../utils/packaging-last-prices'

const EMPTY_FILTERS: LastPricesFilters = {
  q: '',
  group: '',
  n: LAST_PRICE_DEFAULT_N,
  scope: 'bom',
  suppliers: [],
  from: '',
  to: '',
  trend: 'all',
  minPct: 0,
  onlyPriced: true,
  bomOnly: false,
  showQty: false,
}

export function PackagingLastPricesPage() {
  const { can } = usePermission()
  const [filters, setFilters] = useState<LastPricesFilters>(EMPTY_FILTERS)
  const [sortBy, setSortBy] = useState('')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [pageSize, setPageSize] = useState(50)
  const [exporting, setExporting] = useState(false)
  const debouncedQ = useDebouncedValue(filters.q, 350)
  const once = useSingleFlight()
  const columns = usePackagingLastPricesColumns(filters.n, filters.showQty)

  /** Bộ lọc + thứ tự gửi máy chủ — dùng chung cho danh sách và Xuất Excel. */
  const filterParams = useMemo(
    () => buildLastPricesParams(filters, debouncedQ, { by: sortBy, dir: sortDir }),
    [filters, debouncedQ, sortBy, sortDir],
  )
  const [page, setPage] = usePageResetOnFilterChange([filterParams, pageSize])
  const list = usePackagingLastPrices({ ...filterParams, page, page_size: pageSize })

  const changeFilters = (next: LastPricesFilters) => {
    //  Bớt số lần mà đang xếp theo một lần đã biến mất → bỏ xếp, khỏi xếp theo cột không còn thấy.
    if (sortBy && sortKeyOutsideN(sortBy, next.n)) setSortBy('')
    setFilters(next)
  }

  const filtersActive =
    JSON.stringify({ ...filters, n: 0, showQty: false }) !==
    JSON.stringify({ ...EMPTY_FILTERS, n: 0, showQty: false })

  const exportExcel = () =>
    once(async () => {
      setExporting(true)
      try {
        await exportPackagingLastPrices({ ...filterParams, show_qty: filters.showQty || undefined })
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Không xuất được tệp Excel')
      } finally {
        setExporting(false)
      }
    })

  return (
    <PageContainer fill>
      <PageHeader
        title="Giá mua gần nhất"
        description="Đơn giá của n lần mua có giá gần nhất của từng mã vật tư bao bì (chưa VAT, VND). Lần 1 là lần mua mới nhất; dòng đơn giá 0 bị bỏ qua."
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
          rows={list.data?.items}
          getRowId={(row) => row.code}
          isLoading={list.isLoading}
          isError={list.isError}
          emptyMessage={
            filtersActive ? 'Không có mã nào khớp bộ lọc.' : 'Chưa có mã vật tư bao bì nào có giá.'
          }
          storageKey="procurement.packaging-last-prices"
          filtersActive={filtersActive}
          onResetFilters={() => changeFilters({ ...EMPTY_FILTERS, n: filters.n, showQty: filters.showQty })}
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={(by, dir) => {
            setSortBy(by)
            setSortDir(dir)
          }}
          toolbar={
            <PackagingLastPricesToolbar
              filters={filters}
              groups={list.data?.groups ?? []}
              suppliers={list.data?.suppliers ?? []}
              onChange={changeFilters}
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
    </PageContainer>
  )
}
