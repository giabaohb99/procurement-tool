import { useMemo } from 'react'
import Pagination from '../Pagination'
import TableHead, { TableCells, TableColGroup } from '../TableHead'
import TableToolbar from '../TableToolbar'
import TableScroll from '../TableScroll'
import { useTableColumns } from '../../hooks/useTableColumns'
import type { PackagingImpactProduct } from '../../api/packaging-cost-types'
import { buildProductColumns } from './PackagingProductColumns'
import PackagingFilterChipBar from './PackagingFilterChipBar'
import type { ImpactAdvancedFilters } from '../../utils/packaging-impact-filters'

/**
 * Bảng SẢN PHẨM BỊ ẢNH HƯỞNG: máy chủ phân trang + tìm + xếp (chọn cả nhóm nhãn có thể ra hàng nghìn sản phẩm).
 * Bảng chỉ vẽ MỘT trang; thao tác của người dùng báo ngược lên màn qua các callback. Tìm + thanh lọc điều kiện (chip) + xếp cả năm cột thành
 * phần đều làm ở máy chủ; KPI luôn tính trên toàn bộ tập nên khi đang lọc, thanh công cụ nói rõ "Đang lọc: x / M sản phẩm".
 */
export default function PackagingImpactProductsTable({
  rows, total, affected, loading, failed, keyword, onKeyword, filters, filterCount, onFilters, onResetFilters,
  sortBy, sortDir, onSort, page, pageSize, onPage,
}: {
  rows: PackagingImpactProduct[] | undefined
  total: number
  /** Số sản phẩm bị ảnh hưởng CHƯA lọc (`kpis.affected_products`) — mẫu số của "Đang lọc: x / M". */
  affected?: number
  loading: boolean
  failed: boolean
  keyword: string
  onKeyword: (v: string) => void
  /** Lọc nâng cao ĐANG ÁP + số nhóm điều kiện đang bật. */
  filters: ImpactAdvancedFilters
  filterCount: number
  onFilters: (next: ImpactAdvancedFilters) => void
  /** Xóa cả từ khóa lẫn lọc nâng cao (giữ cột xếp). */
  onResetFilters: () => void
  sortBy: string
  sortDir: 'asc' | 'desc'
  onSort: (key: string) => void
  page: number
  pageSize: number
  onPage: (page: number, pageSize: number) => void
}) {
  const offset = (page - 1) * pageSize
  const columns = useMemo(() => buildProductColumns({ offset, newKey: 'cost_applied_bottle' }), [offset])

  const table = useTableColumns('packaging-impact-products', columns)
  const minW = table.columns.reduce((s, c) => s + (typeof c.width === 'number' ? c.width : 100), 0)
  const list = rows ?? []
  //  Rỗng vì bộ lọc ≠ rỗng vì chưa có gì: hai câu khác nhau.
  const filtersActive = keyword !== '' || filterCount > 0

  return (
    <div>
      <TableToolbar {...table}>
        <PackagingFilterChipBar variant="impact" value={filters} onChange={onFilters} keyword={keyword} onKeyword={onKeyword}>
          {filtersActive && affected != null && !loading && (
            <span role="status" className="pkg-hint">Đang lọc: <b>{total.toLocaleString('vi-VN')}</b> / {affected.toLocaleString('vi-VN')} sản phẩm</span>
          )}
          {filtersActive && <button type="button" className="btn ghost" onClick={onResetFilters}><i className="ti ti-filter-off" />Xóa lọc</button>}
        </PackagingFilterChipBar>
      </TableToolbar>
      <TableScroll>
        <table className="dense" style={{ minWidth: minW, tableLayout: 'fixed' }}>
          <TableColGroup columns={table.columns} colW={table.colW} />
          <TableHead columns={table.columns} startResize={table.startResize} sortBy={sortBy} sortDir={sortDir} onSort={onSort} />
          <tbody>
            {list.map((r, i) => <tr key={r.fg_code}><TableCells columns={table.columns} row={r} index={i} /></tr>)}
            {list.length === 0 && (
              <tr><td colSpan={table.columns.length} className="table-empty">
                {failed ? 'Không tính được tác động — thử lại sau.' : loading ? 'Đang tính…'
                  : filtersActive ? 'Không có sản phẩm nào khớp từ khóa / bộ lọc.' : 'Không có sản phẩm nào dùng các mã đã chọn.'}
              </td></tr>
            )}
          </tbody>
        </table>
      </TableScroll>
      <div className="table-foot"><Pagination page={page} pageSize={pageSize} total={total} onChange={onPage} /></div>
    </div>
  )
}
