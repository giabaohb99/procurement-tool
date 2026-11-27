import { useMemo, useState } from 'react'
import DateRangePicker from '../../components/DateRangePicker'
import TableToolbar from '../../components/TableToolbar'
import PackagingCodePicker from '../../components/packaging/PackagingCodePicker'
import TableHead, { TableCells, TableColGroup } from '../../components/TableHead'
import TableScroll from '../../components/TableScroll'
import TableCards from '../../components/TableCards'
import { useNarrowScreen } from '../../hooks/useNarrowScreen'
import { CodeLink, DiffText, Dash, OneLine, PctText, PriceText } from '../../components/packaging/PackagingCells'
import type { PackagingPriceRow } from '../../api/packaging-cost-types'
import { useTableColumns, TableColumn } from '../../hooks/useTableColumns'
import { fmtDateStr } from '../../utils/datetime'
import '../../components/packaging/packaging.css'

/** Chưa có nguồn dữ liệu — bảng rỗng có chủ đích, không phải lỗi tải. */
const NO_ROWS: PackagingPriceRow[] = []
interface Filters { codes: string[]; group: string; scope: 'bom' | 'all' }
const EMPTY: Filters = { codes: [], group: '', scope: 'bom' }

/**
 * duoc-CR-798 — BẢNG GIÁ NGUYÊN LIỆU (27/11/2026): dựng y khuôn Bảng giá VTBB (cùng bộ cột, cùng khung bảng, chữ "VTBB"
 * đổi thành "nguyên liệu"), mục menu ngay dưới Bảng giá VTBB, cùng bản `frontend-v2`. CHƯA nối dữ liệu (chủ dự án chốt:
 * dựng màn trước, dữ liệu sau) nên bảng luôn rỗng; khi có nguồn giá thì nạp `rows` như màn VTBB. Không có cột Thao tác
 * (Báo giá) vì chưa có mã nào. Gác cùng khóa xem bảng giá (`PackagingGate` ở `App.tsx`). Thanh lọc đủ như màn VTBB (ô chọn mã,
 * chip nhóm, phạm vi mã, khoảng ngày tính min – max — 27/11/2026); chưa có dữ liệu nên bộ lọc chỉ giữ trạng thái trên màn.
 */
export default function PackagingMaterialPriceList() {
  const narrow = useNarrowScreen()
  const [filters, setFilters] = useState<Filters>(EMPTY)
  const [range, setRange] = useState({ from: '', to: '' })
  const patch = (next: Partial<Filters>) => setFilters((f) => ({ ...f, ...next }))
  const filtersActive = JSON.stringify(filters) !== JSON.stringify(EMPTY) || !!(range.from || range.to)
  const clearFilters = () => { setFilters(EMPTY); setRange({ from: '', to: '' }) }
  const emptyText = filtersActive ? 'Không có mã nào khớp bộ lọc.' : 'Chưa có dữ liệu bảng giá nguyên liệu.'
  const columns = useMemo<TableColumn<PackagingPriceRow>[]>(() => [
    { key: 'code', label: 'Mã nguyên liệu', width: 120, sort: 'code', fixed: true, card: 'title', cell: (r) => <CodeLink code={r.code} /> },
    { key: 'name', label: 'Tên nguyên liệu', width: 250, sort: 'name', card: 'subtitle', cell: (r) => (r.name ? <OneLine>{r.name}</OneLine> : <span className="pkg-muted">(chưa có tên)</span>) },
    { key: 'group', label: 'Nhóm', width: 90, sort: 'group', cell: (r) => r.group },
    { key: 'unit', label: 'ĐVT', width: 70, cell: (r) => r.unit },
    { key: 'purchase_count', label: 'Số lần mua', width: 90, align: 'right', sort: 'purchase_count', cell: (r) => r.purchase_count },
    { key: 'last_date', label: 'Mua gần nhất', width: 110, sort: 'last_date', cell: (r) => (r.last_date ? fmtDateStr(r.last_date) : <Dash />) },
    { key: 'currency', label: 'Tiền tệ', width: 80, cell: () => 'VND' },
    { key: 'last_purchase_price', label: 'Giá mua gần nhất', width: 120, align: 'right', sort: 'last_purchase_price', cell: (r) => <PriceText value={r.last_purchase_price} /> },
    { key: 'prev_purchase_price', label: 'Giá mua lần trước', width: 120, align: 'right', sort: 'prev_purchase_price', cell: (r) => <PriceText value={r.prev_purchase_price} /> },
    { key: 'quote', label: 'Báo giá mới', width: 120, align: 'right', sort: 'quote_price', cell: (r) => (r.quote ? <PriceText value={r.quote.price} /> : <Dash />) },
    { key: 'old', label: 'Giá cũ', width: 100, align: 'right', sort: 'old', card: 'hero', cell: (r) => <PriceText value={r.old} bold /> },
    { key: 'new', label: 'Giá mới', width: 100, align: 'right', sort: 'new', card: 'hero', cell: (r) => <PriceText value={r.new} bold /> },
    { key: 'diff', label: 'Chênh lệch', width: 100, align: 'right', sort: 'diff', card: 'hero', cell: (r) => <DiffText value={r.diff} /> },
    { key: 'pct', label: '%', width: 80, align: 'right', sort: 'pct', card: 'hero', cell: (r) => <PctText value={r.pct} /> },
    { key: 'min', label: 'Min', width: 100, align: 'right', sort: 'min', cell: (r) => <PriceText value={r.min} /> },
    { key: 'max', label: 'Max', width: 100, align: 'right', sort: 'max', cell: (r) => <PriceText value={r.max} /> },
  ], [])
  const table = useTableColumns('packaging-material-price-list', columns)
  const minW = table.columns.reduce((s, c) => s + (typeof c.width === 'number' ? c.width : 100), 0)

  return (
    <div>
      <div className="pkg-head" style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12, flexWrap: 'wrap' }}>
        <div style={{ flex: 1, minWidth: 260 }}>
          <h2 className="page-title" style={{ margin: 0 }}>Bảng giá nguyên liệu</h2>
          <div className="pkg-hint">Giá cũ / mới từng mã nguyên liệu: có báo giá thì giá mới là báo giá, không thì là lần mua gần nhất. Đơn vị VNĐ, chưa VAT.</div>
        </div>
        <div style={{ width: 280 }}>
          <DateRangePicker block value={range} placeholder="Khoảng ngày tính min – max" onChange={setRange} />
        </div>
      </div>
      <div className="card table-card">
        <TableToolbar compact {...table}>
          <div className="pkg-row" style={{ flex: 1, minWidth: 0 }}>
            <div style={{ width: 380, maxWidth: '100%' }}>
              <PackagingCodePicker options={[]} value={filters.codes} onChange={(codes) => patch({ codes })}
                emptyPlaceholder="Tìm mã nguyên liệu — gõ mã, tên, nhóm hoặc NCC, chọn được nhiều mã" compact />
            </div>
            <div className="pkg-pills" role="group" aria-label="Lọc theo nhóm">
              <button type="button" className={'pkg-pill' + (filters.group === '' ? ' on' : '')} aria-pressed={filters.group === ''}
                onClick={() => patch({ group: '' })}>Tất cả</button>
            </div>
            <div className="pkg-seg" role="group" aria-label="Phạm vi mã">
              <button className={filters.scope === 'bom' ? 'on' : ''} onClick={() => patch({ scope: 'bom' })}>Mã trong định mức</button>
              <button className={filters.scope === 'all' ? 'on' : ''} onClick={() => patch({ scope: 'all' })}>Mọi mã có giá</button>
            </div>
            {filtersActive && <button className="btn ghost sm" onClick={clearFilters}><i className="ti ti-rotate" />Xóa lọc</button>}
          </div>
        </TableToolbar>
        {narrow ? (
          <TableCards columns={table.columns} rows={NO_ROWS} rowKey={(r) => r.code} empty={emptyText} />
        ) : (
          <TableScroll>
            <table className="dense" style={{ minWidth: minW, tableLayout: 'fixed' }}>
              <TableColGroup columns={table.columns} colW={table.colW} />
              <TableHead columns={table.columns} startResize={table.startResize} />
              <tbody>
                <tr><td colSpan={table.columns.length} className="table-empty">{emptyText}</td></tr>
              </tbody>
            </table>
          </TableScroll>
        )}
      </div>
    </div>
  )
}
