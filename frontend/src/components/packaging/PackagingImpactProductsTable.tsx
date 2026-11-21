import { useMemo } from 'react'
import Pagination from '../Pagination'
import TableHead, { TableCells, TableColGroup } from '../TableHead'
import TableToolbar from '../TableToolbar'
import TableScroll from '../TableScroll'
import { useTableColumns, TableColumn } from '../../hooks/useTableColumns'
import type { PackagingImpactProduct, PackagingPart } from '../../api/packaging-cost-types'
import { diffColor, joinWarnings, priceText, roleLabel } from '../../utils/packaging-price'
import { DiffText, OneLine, PriceText } from './PackagingCells'

/** Năm cột thành phần của định mức: vai trò (`PackagingRole`) + `perCarton` = giá tính cho cả thùng, chia quy cách thùng. */
const PART_COLUMNS = [
  { role: 1, perCarton: false }, { role: 2, perCarton: false }, { role: 3, perCarton: false },
  { role: 4, perCarton: true }, { role: 5, perCarton: true },
] as const

/** Ô THÀNH PHẦN: mã trên, giá dưới — giá đổi thì "cũ → mới" với số mới tô theo chiều tăng / giảm; mã đang chọn tô nổi. */
function PartCell({ part }: { part: PackagingPart | undefined }) {
  if (!part?.code) return <span className="pkg-muted">—</span>
  const current = part.applied ?? part.new
  const changed = part.old != null && current != null && Math.abs(current - part.old) > 1e-9
  return (
    <div className={'pkg-part' + (part.selected ? ' sel' : '')}>
      <div className="code">{part.code}</div>
      <div className="price">
        {current == null ? <span className="pkg-muted">chưa có giá</span> : changed ? (
          <>
            <span className="pkg-muted">{priceText(part.old)} →</span>{' '}
            <b style={{ color: diffColor(current - (part.old ?? 0)) }}>{priceText(current)}</b>
          </>
        ) : priceText(current)}
      </div>
    </div>
  )
}

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
  const columns = useMemo<TableColumn<PackagingImpactProduct>[]>(() => [
    { key: 'stt', label: 'STT', width: 56, align: 'center', fixed: true, cell: (_r, i) => offset + i + 1 },
    { key: 'hh_code', label: 'Mã HH', width: 110, sort: 'hh_code', fixed: true, cell: (r) => <b className="pkg-num">{r.hh_code}</b> },
    { key: 'hh_name', label: 'Tên hàng hóa', width: 250, sort: 'hh_name', cell: (r) => <OneLine>{r.hh_name}</OneLine> },
    { key: 'carton_qty', label: 'Quy cách thùng', width: 100, align: 'right', sort: 'carton_qty',
      cell: (r) => (r.carton_qty ? r.carton_qty.toLocaleString('vi-VN') : <span className="pkg-muted">—</span>) },
    ...PART_COLUMNS.map<TableColumn<PackagingImpactProduct>>((p) => ({
      key: `part_${p.role}`,
      label: p.perCarton ? `${roleLabel(p.role)} (giá /thùng)` : roleLabel(p.role),
      width: 140,
      cell: (r) => <PartCell part={r.parts.find((x) => x.role === p.role)} />,
    })),
    { key: 'cost_old_bottle', label: 'CP bao bì/chai cũ', width: 110, align: 'right', sort: 'cost_old_bottle', cell: (r) => <PriceText value={r.cost_old_bottle} /> },
    { key: 'cost_applied_bottle', label: 'CP bao bì/chai mới', width: 110, align: 'right', sort: 'cost_applied_bottle', cell: (r) => <PriceText value={r.cost_applied_bottle} bold /> },
    { key: 'diff_bottle', label: 'Tăng/giảm /chai', width: 110, align: 'right', sort: 'diff_bottle', cell: (r) => <DiffText value={r.diff_bottle} bold /> },
    { key: 'diff_carton', label: 'Tăng/giảm /thùng', width: 120, align: 'right', sort: 'diff_carton', cell: (r) => <DiffText value={r.diff_carton} bold /> },
    { key: 'note', label: 'Ghi chú', width: 220, cell: (r) => <span className="pkg-hint">{joinWarnings(r.warnings)}</span> },
  ], [offset])

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
