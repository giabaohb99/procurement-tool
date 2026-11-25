/**
 * duoc-CR-784 — bảng SẢN PHẨM BỊ ẢNH HƯỞNG của màn Tác động giá (bám `drawImpact` của bản mẫu).
 *
 * Máy chủ phân trang + tìm + xếp (luật §8: bảng phân trang tại máy chủ thì xếp tại máy chủ — chọn cả nhóm
 * nhãn có thể ra hàng nghìn sản phẩm). Bảng chỉ vẽ MỘT trang và báo thao tác của người dùng qua `view`
 * (`usePackagingImpactTableState`, nằm ở màn vì chúng là một phần thân `POST /impact`). Ô thành phần ghi mã +
 * "giá cũ → giá đang dùng"; mã nằm trong danh sách đang chọn thì tô nổi. Tìm + Lọc nâng cao + xếp cả năm cột thành phần
 * đều làm ở máy chủ; KPI luôn tính trên toàn bộ tập nên khi đang lọc, thanh công cụ nói rõ "Đang lọc: x / M sản phẩm".
 */
import { Search } from 'lucide-react'
import { useMemo } from 'react'

import { DataTable } from '@/shared/data-table'
import { Input } from '@/shared/ui/input'

import { buildPackagingProductColumns } from '../config/packaging-product-columns'
import type { PackagingImpactTableState } from '../hooks/use-packaging-impact-table-state'
import type { PackagingImpactProduct } from '../types/packaging-cost-types'
import { PackagingImpactAdvancedFilter } from './packaging-impact-advanced-filter'

interface PackagingImpactProductsTableProps {
  /** Dòng của TRANG hiện tại (đã lọc + xếp ở máy chủ). */
  rows: PackagingImpactProduct[] | undefined
  /** Tổng số dòng sau lọc từ khóa (không phải số dòng của trang). */
  total: number
  /** Số sản phẩm bị ảnh hưởng CHƯA lọc (`kpis.affected_products`) — mẫu số của "Đang lọc: x / M". */
  affected?: number
  isLoading: boolean
  isError: boolean
  view: PackagingImpactTableState
}

export function PackagingImpactProductsTable({
  rows,
  total,
  affected,
  isLoading,
  isError,
  view,
}: PackagingImpactProductsTableProps) {
  const { keyword, sortBy, sortDir, page, pageSize, filterCount } = view
  //  Rỗng vì bộ lọc ≠ rỗng vì chưa có gì (luật bảng có bộ lọc): hai câu khác nhau.
  const filtersActive = keyword !== '' || filterCount > 0
  const offset = (page - 1) * pageSize

  const columns = useMemo(
    () => buildPackagingProductColumns({ offset, rows, newCostKey: 'cost_applied_bottle' }),
    [offset, rows],
  )

  return (
    <DataTable
      //  Dòng khóa theo mã, không có `id` số: để mặc định thì lúc đang tải bảng chèn cột ID rồi gỡ, làm tách nhóm cột.
      idColumn={false}
      columns={columns}
      rows={rows}
      getRowId={(row) => row.fg_code}
      isLoading={isLoading}
      isError={isError}
      emptyMessage={
        filtersActive
          ? 'Không có sản phẩm nào khớp từ khóa / bộ lọc.'
          : 'Không có sản phẩm nào dùng các mã đã chọn.'
      }
      storageKey="procurement.packaging-impact-products"
      filtersActive={filtersActive}
      onResetFilters={view.resetFilters}
      sortBy={sortBy}
      sortDir={sortDir}
      onSortChange={view.setSort}
      toolbar={
        <div className="flex flex-1 flex-wrap items-center gap-2">
          <div className="relative w-72 max-w-full">
            <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              className="pl-9"
              aria-label="Tìm sản phẩm"
              placeholder="Tìm mã HH, tên, mã thành phần…"
              value={keyword}
              onChange={(event) => view.setKeyword(event.target.value)}
            />
          </div>
          <PackagingImpactAdvancedFilter value={view.filters} onApply={view.setFilters} />
          {filtersActive && affected != null && !isLoading && (
            <span role="status" className="text-sm text-muted-foreground">
              Đang lọc: <b className="text-foreground">{total.toLocaleString('vi-VN')}</b> /{' '}
              {affected.toLocaleString('vi-VN')} sản phẩm
            </span>
          )}
        </div>
      }
      pagination={{
        page,
        pageSize,
        total,
        onPageChange: view.setPage,
        onPageSizeChange: view.setPageSize,
        unitLabel: 'sản phẩm',
      }}
    />
  )
}
