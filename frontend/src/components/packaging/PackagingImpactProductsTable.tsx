import { useMemo } from 'react'
import Pagination from '../Pagination'
import TableHead, { TableCells, TableColGroup } from '../TableHead'
import TableToolbar from '../TableToolbar'
import TableScroll from '../TableScroll'
import { useTableColumns } from '../../hooks/useTableColumns'
import type { PackagingImpactProduct } from '../../api/packaging-cost-types'
import { buildProductColumns } from './PackagingProductColumns'

/**
 * Bảng SẢN PHẨM BỊ ẢNH HƯỞNG: máy chủ phân trang + tìm + xếp (chọn cả nhóm nhãn có thể ra hàng nghìn sản phẩm).
 * Bảng chỉ vẽ MỘT trang; thao tác của người dùng báo ngược lên màn qua các callback.
 */
export default function PackagingImpactProductsTable({
  rows, total, loading, failed, keyword, onKeyword, sortBy, sortDir, onSort, page, pageSize, onPage,
}: {
  rows: PackagingImpactProduct[] | undefined
  total: number
  loading: boolean
  failed: boolean
  keyword: string
  onKeyword: (v: string) => void
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

  return (
    <div>
      <TableToolbar {...table}>
        <div style={{ flex: 1, textAlign: 'left' }}>
          <input aria-label="Tìm sản phẩm" placeholder="Tìm mã HH, tên, mã thành phần…" value={keyword}
            style={{ width: 320, maxWidth: '100%', height: 34 }} onChange={(e) => onKeyword(e.target.value)} />
        </div>
      </TableToolbar>
      <TableScroll>
        <table className="dense" style={{ minWidth: minW, tableLayout: 'fixed' }}>
          <TableColGroup columns={table.columns} colW={table.colW} />
          <TableHead columns={table.columns} startResize={table.startResize} sortBy={sortBy} sortDir={sortDir} onSort={onSort} />
          <tbody>
            {list.map((r, i) => <tr key={r.hh_code}><TableCells columns={table.columns} row={r} index={i} /></tr>)}
            {list.length === 0 && (
              <tr><td colSpan={table.columns.length} className="table-empty">
                {failed ? 'Không tính được tác động — thử lại sau.' : loading ? 'Đang tính…'
                  : keyword ? 'Không có sản phẩm khớp từ khóa.' : 'Không có sản phẩm nào dùng các mã đã chọn.'}
              </td></tr>
            )}
          </tbody>
        </table>
      </TableScroll>
      <div className="table-foot"><Pagination page={page} pageSize={pageSize} total={total} onChange={onPage} /></div>
    </div>
  )
}
