/**
 * duoc-CR-784 — GIÁ MUA GẦN NHẤT (bám `renderMatrix` của bản mẫu, mở rộng): mỗi mã VTBB một dòng với ngày mua, nhà cung
 * cấp, đơn giá của n lần mua có giá gần nhất (n = 3 / 5 / 10; xanh = đắt hơn lần cũ kế bên, đỏ = rẻ hơn), biến động lần 1
 * so lần 2 / lần n và giá trung bình. Lọc + xếp + phân trang tại MÁY CHỦ (luật §8); tham số đi kèm Xuất Excel để ra đúng
 * thứ tự. Tiêu đề gộp nhóm cột do `DataTable` vẽ (`group` của cột).
 */
import { useEffect, useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { DataTable } from '@/shared/data-table'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'

import { PackagingExportExcelButton } from '../components/packaging-header-buttons'
import { exportPackagingLastPrices } from '../api/packaging-cost-api'
import { PackagingLastPricesCard } from '../components/packaging-last-prices-card'
import {
  PackagingLastPricesToolbar,
  type LastPricesFilters,
} from '../components/packaging-last-prices-toolbar'
import { usePackagingCodeOptions } from '../hooks/use-packaging-impact'
import { usePackagingLastPrices } from '../hooks/use-packaging-last-prices'
import { usePackagingLastPricesColumns } from '../hooks/use-packaging-last-prices-columns'
import {
  buildLastPricesParams,
  isRecentMode,
  RECENT_CODES_LIMIT,
  sortKeyOutsideN,
} from '../utils/packaging-last-prices'
import { sortPackagingCodeOptions } from '../utils/packaging-code-match'
import {
  buildLastPricesUrlSearch,
  DEFAULT_LAST_PRICES_FILTERS,
  parseLastPricesUrlState,
} from '../utils/packaging-list-url-state'

const EMPTY_FILTERS = DEFAULT_LAST_PRICES_FILTERS

export function PackagingLastPricesPage() {
  const { can } = usePermission()
  const isMobile = useIsMobile()
  const [searchParams, setSearchParams] = useSearchParams()
  //  Bộ lọc / cột xếp / trang sống trên URL (F5 / gửi link mở lại đúng chỗ): đọc MỘT lần lúc mở màn, sau đó state là nguồn
  //  và URL đi theo (effect bên dưới, `replace` — gõ ô tìm không đẻ ra cả chục mục lịch sử của nút Quay lại).
  const [initial] = useState(() => parseLastPricesUrlState(searchParams))
  const [filters, setFilters] = useState<LastPricesFilters>(initial.filters)
  const [sortBy, setSortBy] = useState(initial.sortBy)
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>(initial.sortDir)
  const [pageSize, setPageSize] = useState(initial.pageSize)
  const [exporting, setExporting] = useState(false)
  const once = useSingleFlight()
  //  Danh sách mã cho ô chọn mã — cùng nguồn với màn Tác động và Lịch sử mua hàng.
  const codeOptionsQuery = usePackagingCodeOptions()
  const codeOptions = useMemo(
    () => sortPackagingCodeOptions(codeOptionsQuery.data ?? []),
    [codeOptionsQuery.data],
  )
  const columns = usePackagingLastPricesColumns(filters.n, filters.showQty)

  //  Chế độ gần nhất (mới mở, chưa chọn gì): chỉ 20 mã mua gần nhất, xếp ngày mua mới nhất trước, không phân trang.
  const recent = isRecentMode(filters)

  /** Bộ lọc + thứ tự gửi máy chủ — dùng chung cho danh sách và Xuất Excel. */
  const filterParams = useMemo(
    () =>
      buildLastPricesParams(filters, recent ? { by: 'p1_date', dir: 'desc' } : { by: sortBy, dir: sortDir }),
    [filters, sortBy, sortDir, recent],
  )
  const [rawPage, setPage] = usePageResetOnFilterChange([filterParams, pageSize], initial.page)
  const page = recent ? 1 : rawPage
  const list = usePackagingLastPrices({
    ...filterParams,
    page,
    page_size: recent ? RECENT_CODES_LIMIT : pageSize,
  })

  const urlSearch = buildLastPricesUrlSearch({
    filters,
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

  const changeFilters = (next: LastPricesFilters) => {
    //  Bớt số lần mà đang xếp theo một lần đã biến mất → bỏ xếp, khỏi xếp theo cột không còn thấy.
    if (sortBy && sortKeyOutsideN(sortBy, next.n)) setSortBy('')
    setFilters(next)
  }

  //  `all` / `trendAllLit` chỉ là cờ giao diện, không phải bộ lọc dữ liệu.
  const filtersActive =
    JSON.stringify({ ...filters, n: 0, showQty: false, all: false, trendAllLit: false }) !==
    JSON.stringify({ ...EMPTY_FILTERS, n: 0, showQty: false, all: false, trendAllLit: false })

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

  const exportButton = can('packaging_cost', 'export') && (
    <PackagingExportExcelButton exporting={exporting} onClick={() => void exportExcel()} />
  )

  return (
    //  `fill` chỉ từ `md`: ở khổ hẹp bảng thành danh sách thẻ dài, nhét vào khe cao cố định là cuộn LỒNG (xem crud-list-page).
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Giá mua gần nhất"
        //  Câu giới thiệu ẩn ở khổ điện thoại (cùng nếp các màn CRUD): đọc một lần rồi thôi mà ăn ba bốn dòng đầu màn.
        description={
          isMobile
            ? undefined
            : 'Đơn giá của n lần mua có giá gần nhất của từng mã vật tư bao bì (VNĐ, chưa VAT). Lần 1 là lần mua mới nhất; dòng đơn giá 0 bị bỏ qua.'
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
          columns={columns}
          rows={list.data?.items}
          getRowId={(row) => row.code}
          isLoading={list.isLoading}
          isError={list.isError}
          emptyMessage={
            filtersActive ? 'Không có mã nào khớp bộ lọc.' : 'Chưa có mã vật tư bao bì nào có giá.'
          }
          storageKey="procurement.packaging-last-prices"
          mobileCard={(row) => (
            <PackagingLastPricesCard row={row} n={filters.n} showQty={filters.showQty} />
          )}
          mobileSort
          filtersActive={filtersActive}
          onResetFilters={() =>
            changeFilters({ ...EMPTY_FILTERS, n: filters.n, showQty: filters.showQty, all: filters.all })
          }
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={(by, dir) => {
            setSortBy(by)
            setSortDir(dir)
            //  Xếp theo cột khác khi đang ở chế độ gần nhất = muốn xem rộng: nạp hết mọi mã theo thứ tự đó.
            if (recent) setFilters((current) => ({ ...current, all: true }))
          }}
          toolbar={
            <PackagingLastPricesToolbar
              filters={filters}
              groups={list.data?.groups ?? []}
              suppliers={list.data?.suppliers ?? []}
              codeOptions={codeOptions}
              codeOptionsLoading={codeOptionsQuery.isLoading}
              onChange={changeFilters}
              recentMode={recent}
            />
          }
          //  Chế độ gần nhất: ẩn chân phân trang (chú thích "20 mã mua gần nhất" nằm ở thanh lọc).
          pagination={
            recent
              ? undefined
              : {
                  page,
                  pageSize,
                  total: list.data?.total ?? 0,
                  onPageChange: setPage,
                  onPageSizeChange: setPageSize,
                  unitLabel: 'mã',
                }
          }
        />
      </Card>
    </PageContainer>
  )
}
