import { useMemo } from 'react'
import { Link } from 'react-router-dom'
import Pagination from '../Pagination'
import TableHead, { TableCells, TableColGroup } from '../TableHead'
import TableScroll from '../TableScroll'
import TableToolbar from '../TableToolbar'
import type { ReactNode } from 'react'
import { useTableColumns, TableColumn } from '../../hooks/useTableColumns'
import type { PackagingHistoryRow } from '../../api/packaging-cost-types'
import { fmtDateStr } from '../../utils/datetime'
import { diffColor, diffText, pctText, PRICE_SOURCE_PO_LINE, qtyText } from '../../utils/packaging-price'
import { historyRoleText, historyRowKey } from '../../utils/packaging-query'
import { AmountText, CodeLink, Dash, OneLine, PriceText } from './PackagingCells'
import './packaging.css'

/** Đơn giá 0 = dòng không có giá: hiện "0" mờ (không tô xanh / đỏ, không tính vào KPI / biểu đồ). */
function PriceCell({ row }: { row: PackagingHistoryRow }) {
  if (row.price === 0) {
    return <span className="pkg-num" title="Đơn giá 0 — không tính vào giá bình quân, thấp nhất, cao nhất">0</span>
  }
  return <PriceText value={row.price} bold />
}

/** Chênh so lần mua CÓ GIÁ liền trước. Không đổi thì một số 0 mờ, không kèm "(0,0%)" — cả trăm dòng "0 (0,0%)" che mất dòng có đổi. */
function DiffCell({ row }: { row: PackagingHistoryRow }) {
  const diff = diffText(row.diff)
  if (!diff) return <Dash />
  if (row.diff === 0) return <span className="pkg-num pkg-muted">0</span>
  const pct = pctText(row.pct)
  return <span className="pkg-num" style={{ color: diffColor(row.diff) }}>{diff}{pct && ` (${pct})`}</span>
}

/** Nhãn "ĐMH đang mở" (giá còn có thể đổi) + số ĐMH nguồn bấm được; dữ liệu cũ không có ĐMH thì để trống. */
function SourceCell({ row }: { row: PackagingHistoryRow }) {
  const open = row.source_type === PRICE_SOURCE_PO_LINE
  if (!open && row.doc_id <= 0) return null
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
      {open && <span className="badge warn" title="Dòng đơn mua hàng đã duyệt, chưa hoàn thành — giá có thể còn đổi">ĐMH đang mở</span>}
      {row.doc_id > 0 && (
        <Link to={`/purchase-orders/${row.doc_id}`} onClick={(e) => e.stopPropagation()}>{row.po_code || `#${row.doc_id}`}</Link>
      )}
    </span>
  )
}

/**
 * Bảng lần mua của màn Lịch sử mua hàng. Mọi ô MỘT dòng (cắt bằng "…"). Cột bật xếp gửi `sort_by` = khóa cột lên máy chủ
 * (`date, code, name, supplier, warehouse, qty, price, amount, vat, source` + `hh_code, hh_name, role` ở chế độ sản phẩm); "Lần" và
 * "So lần trước" tính theo từng mã nên chưa xếp được. Một mã: bỏ cột Tên (đã có ở tiêu đề biểu đồ) nhường chỗ cho nhà cung cấp.
 * Giá trị mua = thành tiền Misa khi có, không thì giá x số lượng (máy chủ tính). Chế độ sản phẩm: mỗi dòng = một lần mua x một
 * (sản phẩm, thành phần), khóa dòng là (sản phẩm, id).
 */
export default function PackagingHistoryTable({
  rows, total, productMode, singleCode, sortBy, sortDir, onSort, page, pageSize, onPage, onReload, summary, empty,
}: {
  rows: PackagingHistoryRow[]
  total: number
  productMode: boolean
  singleCode: boolean
  sortBy: string
  sortDir: 'asc' | 'desc'
  onSort: (key: string) => void
  page: number
  pageSize: number
  onPage: (page: number, pageSize: number) => void
  onReload: () => void
  summary?: ReactNode
  empty: ReactNode
}) {
  const columns = useMemo<TableColumn<PackagingHistoryRow>[]>(() => {
    const seq: TableColumn<PackagingHistoryRow> = { key: 'seq', label: 'Lần', width: 55, align: 'right', cell: (r) => <span className="pkg-muted pkg-num">{r.seq}</span> }
    const date: TableColumn<PackagingHistoryRow> = { key: 'date', label: 'Ngày mua', width: 110, sort: 'date', fixed: true, cell: (r) => (r.date ? fmtDateStr(r.date) : <Dash />) }
    const code: TableColumn<PackagingHistoryRow> = { key: 'code', label: 'Mã VTBB', width: 110, sort: 'code', cell: (r) => <CodeLink code={r.code} /> }
    const name: TableColumn<PackagingHistoryRow> = { key: 'name', label: 'Tên vật tư', width: 200, sort: 'name', cell: (r) => (r.name ? <OneLine>{r.name}</OneLine> : <span className="pkg-muted">(chưa có tên)</span>) }
    //  Chế độ sản phẩm (bản mẫu `renderHistBySP`): Mã SP · Tên sản phẩm · Thành phần · Mã VTBB · Tên vật tư · Lần · Ngày mua...;
    //  chế độ mã: Lần · Ngày mua · Mã VTBB...; một mã thì bỏ cột Tên (đã có ở tiêu đề biểu đồ).
    const cols: TableColumn<PackagingHistoryRow>[] = productMode
      ? [
          { key: 'hh_code', label: 'Mã SP', width: 110, sort: 'hh_code', cell: (r) => <b>{r.hh_code}</b> },
          { key: 'hh_name', label: 'Tên sản phẩm', width: 220, sort: 'hh_name', cell: (r) => (r.hh_name ? <OneLine>{r.hh_name}</OneLine> : <span className="pkg-muted">(chưa có tên)</span>) },
          { key: 'role', label: 'Thành phần', width: 110, sort: 'role', cell: (r) => historyRoleText(r) || <Dash /> },
          code, name, seq, date,
        ]
      : [seq, date, code, ...(singleCode ? [] : [name])]
    cols.push(
      { key: 'supplier', label: 'Nhà cung cấp', width: singleCode ? 260 : 190, sort: 'supplier', cell: (r) => (r.supplier ? <OneLine>{r.supplier}</OneLine> : <Dash />) },
      { key: 'warehouse', label: 'Kho', width: 190, sort: 'warehouse', cell: (r) => (r.warehouse ? <OneLine>{r.warehouse}</OneLine> : <Dash />) },
      {
        key: 'qty', label: 'Số lượng', width: 120, align: 'right', sort: 'qty',
        cell: (r) => {
          const t = qtyText(r.qty)
          return t ? <span className="pkg-num">{t}{r.unit && <span className="pkg-muted" style={{ marginLeft: 4, fontSize: 12 }}>{r.unit}</span>}</span> : <Dash />
        },
      },
      { key: 'price', label: 'Đơn giá', width: 110, align: 'right', sort: 'price', cell: (r) => <PriceCell row={r} /> },
      { key: 'amount', label: 'Giá trị mua', width: 130, align: 'right', sort: 'amount', cell: (r) => <AmountText value={r.amount} /> },
      { key: 'diff', label: 'So lần trước', width: 150, align: 'right', cell: (r) => <DiffCell row={r} /> },
      { key: 'source', label: 'Nguồn', width: 170, sort: 'source', cell: (r) => <SourceCell row={r} /> },
    )
    return cols
  }, [productMode, singleCode])

  const table = useTableColumns(`packaging-history-${productMode ? 'product' : 'code'}`, columns)
  const minW = table.columns.reduce((s, c) => s + (typeof c.width === 'number' ? c.width : 100), 0)

  return (
    <div>
      <TableToolbar {...table} onRefresh={onReload}>
        <div className="pkg-summary" style={{ flex: 1, textAlign: 'left', minWidth: 280 }}>{summary}</div>
      </TableToolbar>
      <TableScroll>
        <table className="dense" style={{ minWidth: minW, tableLayout: 'fixed' }}>
          <TableColGroup columns={table.columns} colW={table.colW} />
          <TableHead columns={table.columns} startResize={table.startResize} sortBy={sortBy} sortDir={sortDir} onSort={onSort} />
          <tbody>
            {rows.map((r, i) => (
              <tr key={historyRowKey(r)} className={r.price === 0 ? 'pkg-zero' : undefined}><TableCells columns={table.columns} row={r} index={i} /></tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={table.columns.length} className="table-empty">{empty}</td></tr>}
          </tbody>
        </table>
      </TableScroll>
      <div className="table-foot"><Pagination page={page} pageSize={pageSize} total={total} onChange={onPage} /></div>
    </div>
  )
}
