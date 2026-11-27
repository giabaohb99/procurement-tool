/**
 * duoc-CR-784 — LỊCH SỬ MUA HÀNG của cụm Giá bao bì (bản mẫu `histRows` + `renderLast5`): từng lần mua của mã VTBB, hoặc
 * của các thành phần trong định mức của một / nhiều sản phẩm; kèm dòng KPI và biểu đồ "Diễn biến đơn giá" khi chọn đúng một mã.
 *
 * Lịch sử là bản chụp BẤT BIẾN của sổ giá — không có ô sửa đơn giá (sai thì sửa ở ĐMH / nguồn nạp). Lọc + xếp + phân trang tại
 * MÁY CHỦ (luật §8). Lựa chọn mã nằm ở URL (`?codes=A,B` · `?fg=HH1,HH2` · `mode`) để các bảng khác dẫn thẳng vào được.
 *
 * bao-CR-801 — cùng khuôn cho LỊCH SỬ MUA NGUYÊN LIỆU (`rawMaterial`, mở từ mã ở Bảng giá nguyên liệu): dữ liệu đi hai đường
 * riêng của nguyên liệu (`material-history`, `material-code-options`), gác bằng khóa `packaging_material_price`. Khác màn VTBB:
 * chỉ có chế độ theo mã (không có "Theo mã sản phẩm"), không có nút Nạp sổ Misa và nút In (chưa có trang in cho nguyên liệu),
 * mã trong bảng là chữ thường. Màn nguyên liệu TUYỆT ĐỐI không gọi `history` / `code-options` / `fg-options` của VTBB.
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
import { exportPackagingHistory, exportPackagingMaterialHistory } from '../api/packaging-cost-api'
import { PackagingHistoryCard } from '../components/packaging-history-card'
import { PackagingHistoryChart } from '../components/packaging-history-chart'
import { PackagingHistoryCodeChart } from '../components/packaging-history-code-chart'
import { PackagingHistorySummary } from '../components/packaging-history-summary'
import { PackagingExcelImportButton } from '../components/packaging-excel-import-button'
import { PackagingHistoryToolbar } from '../components/packaging-history-toolbar'
import { PACKAGING_MISA_IMPORT } from '../config/packaging-excel-imports'
import { usePackagingHistory, usePackagingHistoryOptions } from '../hooks/use-packaging-history'
import { usePackagingHistoryColumns } from '../hooks/use-packaging-history-columns'
import {
  buildHistoryParams,
  buildHistorySearch,
  EMPTY_HISTORY_FILTERS,
  historyRowKey,
  parseHistorySearch,
  toMaterialHistoryParams,
  type PackagingHistoryFilters,
  type PackagingHistorySelection,
} from '../utils/packaging-history'
import { packagingHistoryPrintHref } from '../utils/packaging-history-print'

const PACKAGING_DESCRIPTION =
  'Từng lần mua của mã vật tư bao bì hoặc của thành phần trong định mức sản phẩm, mới nhất trước. Giá VNĐ, chưa VAT, là bản chụp lúc mua: đỏ = đắt hơn lần trước, xanh = rẻ hơn.'
const MATERIAL_DESCRIPTION =
  'Từng lần mua của mã nguyên liệu, mới nhất trước. Giá VNĐ, chưa VAT, là bản chụp lúc mua: đỏ = đắt hơn lần trước, xanh = rẻ hơn.'

interface PackagingHistoryPageProps {
  /** Màn Lịch sử mua nguyên liệu (bao-CR-801): nguồn dữ liệu + khóa quyền của nguyên liệu, chỉ có chế độ theo mã. */
  rawMaterial?: boolean
}

export function PackagingHistoryPage({ rawMaterial = false }: PackagingHistoryPageProps) {
  const { can } = usePermission()
  const isMobile = useIsMobile()
  const [searchParams, setSearchParams] = useSearchParams()
  const selection = useMemo(
    () => parseHistorySearch(searchParams, rawMaterial),
    [searchParams, rawMaterial],
  )
  const [filters, setFilters] = useState<PackagingHistoryFilters>(EMPTY_HISTORY_FILTERS)
  const [sortBy, setSortBy] = useState('date')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [pageSize, setPageSize] = useState(50)
  const [exporting, setExporting] = useState(false)
  const debouncedQ = useDebouncedValue(filters.q, 350)
  const once = useSingleFlight()
  const isProduct = selection.mode === 'product'

  //  Ô chọn mã (và sản phẩm ở chế độ sản phẩm) lấy từ nguồn của ĐÚNG màn: VTBB hoặc nguyên liệu, không lẫn đường.
  const options = usePackagingHistoryOptions(rawMaterial, isProduct)

  /** Bộ lọc + thứ tự gửi máy chủ — dùng chung cho danh sách và Xuất Excel. */
  const filterParams = useMemo(
    () => buildHistoryParams(selection, filters, debouncedQ, { by: sortBy, dir: sortDir }),
    [selection, filters, debouncedQ, sortBy, sortDir],
  )
  const [page, setPage] = usePageResetOnFilterChange([filterParams, pageSize])
  const list = usePackagingHistory({ ...filterParams, page, page_size: pageSize }, rawMaterial)
  const series = list.data?.series ?? null
  //  Chế độ sản phẩm, đúng một sản phẩm: mỗi thành phần một đường giá (máy chủ chỉ trả khi có lần mua có giá).
  const seriesByCode = list.data?.series_by_code ?? null
  const columns = usePackagingHistoryColumns(isProduct, series !== null, rawMaterial)

  const changeSelection = (next: PackagingHistorySelection) =>
    setSearchParams(buildHistorySearch(next), { replace: true })

  const filtersActive = JSON.stringify(filters) !== JSON.stringify(EMPTY_HISTORY_FILTERS)

  const exportExcel = () =>
    once(async () => {
      setExporting(true)
      try {
        await (rawMaterial
          ? exportPackagingMaterialHistory(toMaterialHistoryParams(filterParams))
          : exportPackagingHistory(filterParams))
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
        title={rawMaterial ? 'Lịch sử mua nguyên liệu' : 'Lịch sử mua hàng'}
        //  Câu giới thiệu ẩn ở khổ điện thoại (cùng nếp các màn CRUD): đọc một lần rồi thôi mà ăn ba bốn dòng đầu màn.
        description={
          isMobile ? undefined : rawMaterial ? MATERIAL_DESCRIPTION : PACKAGING_DESCRIPTION
        }
        actions={
          <>
            {/* In = xem, nên gác theo quyền đọc (không đòi quyền xuất). Mở tab mới với ĐÚNG bộ lọc đang áp; trang in tự nạp đủ mọi dòng. */}
            {/* Nguyên liệu: chưa có trang in và không nạp sổ Misa ở màn này — hai nút chỉ của VTBB. */}
            {!rawMaterial && can('packaging_history', 'read') && (
              <PackagingPrintButton href={packagingHistoryPrintHref(filterParams)} />
            )}
            {!rawMaterial && <PackagingExcelImportButton kind={PACKAGING_MISA_IMPORT} />}
            {can(rawMaterial ? 'packaging_material_price' : 'packaging_history', 'export') && (
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
          codeOptions={options.codeOptions}
          productOptions={options.productOptions}
          optionsLoading={options.loading}
          suppliers={list.data?.suppliers ?? []}
          rawMaterial={rawMaterial}
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
        {!series && seriesByCode && seriesByCode.length > 0 && (
          <PackagingHistoryCodeChart
            lines={seriesByCode}
            subject={[selection.fg[0], list.data?.items[0]?.fg_name].filter(Boolean).join(' · ')}
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
          storageKey={
            rawMaterial
              ? 'procurement.packaging-material-history'
              : `procurement.packaging-history.${isProduct ? 'product' : 'code'}`
          }
          mobileCard={(row) => (
            <PackagingHistoryCard row={row} productMode={isProduct} rawMaterial={rawMaterial} />
          )}
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
