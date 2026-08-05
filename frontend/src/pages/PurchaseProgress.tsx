import { useEffect, useMemo, useRef, useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import SearchSelect from '../components/SearchSelect'
import DateRangePicker from '../components/DateRangePicker'
import FilterPanel, { FilterItem } from '../components/FilterPanel'
import Pagination from '../components/Pagination'
import { fmtDate } from '../utils/datetime'
import TableHead, { TableCells, TableColGroup } from '../components/TableHead'
import TableToolbar from '../components/TableToolbar'
import { useTableColumns, TableColumn } from '../hooks/useTableColumns'

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
const NOWRAP = { whiteSpace: 'nowrap' as const, overflow: 'hidden', textOverflow: 'ellipsis' }
const MUTED = { color: 'var(--muted)' } as const
const R = { textAlign: 'right' as const }

// Trạng thái tiến độ dòng (đồng bộ ĐMH) — dùng cho filter + badge màu
const PG_COLOR: Record<string, string> = {
  'Chưa đặt hàng': '#94a3b8', 'Đã đặt hàng': '#2563eb', 'Đã nhận hàng': '#0891b2',
  'Chưa gửi ĐMH cho KT': '#db2777', 'Đã gửi ĐMH cho KT': '#7c3aed',
  'Hoàn thành': '#16a34a', 'Tạm ngưng': '#d97706', 'Hủy đơn': '#dc2626',
}
const PG_OPTS = Object.keys(PG_COLOR)

/** Bộ lọc rỗng — dùng cho khởi tạo và nút "Xóa lọc" */
const EMPTY_FILTERS = {
  company_id: '', department: '', month: '', status: '', q: '',
  order_date_from: '', order_date_to: '', received_date_from: '', received_date_to: '',
  recv_state: '',
}
const pgBadge = (s: string) =>
  <span className="badge" style={{ background: (PG_COLOR[s] || '#94a3b8') + '22', color: PG_COLOR[s] || '#64748b', whiteSpace: 'nowrap' }}>{s || '—'}</span>

// CL quy định − nhận: <0 = trễ (đỏ), >=0 = đúng/sớm (xanh)
const diffCell = (n: number) =>
  <span style={{ color: n < 0 ? 'var(--red)' : n > 0 ? 'var(--green)' : 'var(--muted)' }}>{n || 0}</span>

type Ctx = {
  companyName: (id: number) => string
  canOpenPO: boolean
  navigate: (p: string) => void
  page: number
  pageSize: number
}

type Col = {
  key: string
  label: string
  w: number
  sort?: string          // key gửi lên backend (cột thật) — không có => không sort được
  sup?: boolean          // chỉ hiện khi có quyền xem NCC/vận chuyển
  hide?: boolean         // cột phụ: mặc định ẩn, bật lại ở menu "Cột"
  td?: CSSProperties     // style riêng cho <td>
  cell: (r: any, ctx: Ctx, i: number) => ReactNode
}

// Khai báo 1 lần: dùng chung cho <colgroup>, <thead> và <tbody> nên index luôn khớp.
// Bảng có ~46 cột → chỉ bày sẵn cột chính, cột phụ đánh dấu `hide` cho gọn.
const COLS: Col[] = [
  { key: 'stt', label: 'STT', w: 44, td: { ...R, ...MUTED }, cell: (r, c, i) => r.stt ?? (c.page - 1) * c.pageSize + i + 1 },
  {
    key: 'po_code', label: 'Mã ĐMH', w: 150, sort: 'po_code', td: NOWRAP,
    cell: (r, c) => c.canOpenPO ? (
      <a href={`/purchase-orders/${r.po_id}`}
        onClick={(e) => { e.preventDefault(); c.navigate(`/purchase-orders/${r.po_id}`) }}
        style={{ cursor: 'pointer', color: 'var(--navy)', fontWeight: 600, textDecoration: 'underline' }}
        title="Mở đơn mua hàng">{r.po_code}</a>
    ) : (
      <span style={{ fontWeight: 600, color: 'var(--navy)' }} title="Bạn không có quyền xem chi tiết đơn mua hàng">{r.po_code}</span>
    ),
  },
  { key: 'misa_code', hide: true, label: 'Mã MISA', w: 92, sort: 'misa_code', td: { ...NOWRAP, ...MUTED }, cell: (r) => r.misa_code },
  { key: 'pr_code', label: 'Mã PYC', w: 104, sort: 'pr_code', td: { ...NOWRAP, ...MUTED }, cell: (r) => r.pr_code },
  { key: 'company', label: 'Công ty', w: 180, cell: (r, c) => c.companyName(r.company_id) },
  { key: 'department', label: 'Bộ phận', w: 124, sort: 'department', cell: (r) => r.department },
  { key: 'supplier_code', hide: true, label: 'Mã NCC', w: 130, sort: 'supplier_code', sup: true, td: { ...NOWRAP, ...MUTED }, cell: (r) => r.supplier_code },
  { key: 'supplier_name', label: 'Nhà cung cấp', w: 230, sort: 'supplier_name', sup: true, cell: (r) => r.supplier_name },
  { key: 'nspt', label: 'NSPT', w: 150, sort: 'nspt', cell: (r) => r.nspt },
  { key: 'order_date', label: 'Ngày ĐH', w: 88, sort: 'order_date', td: NOWRAP, cell: (r) => fmtDate(r.order_date) },
  { key: 'product_code', label: 'Mã SP', w: 140, sort: 'product_code', td: { ...NOWRAP, ...MUTED }, cell: (r) => r.product_code },
  { key: 'product_name', label: 'Tên SP', w: 220, sort: 'product_name', td: { fontWeight: 500 }, cell: (r) => r.product_name },
  { key: 'invoice_name', hide: true, label: 'Tên hóa đơn', w: 150, sort: 'invoice_name', cell: (r) => r.invoice_name },
  { key: 'item_group', hide: true, label: 'Nhóm hàng', w: 120, sort: 'item_group', cell: (r) => r.item_group },
  { key: 'spec', hide: true, label: 'Quy cách', w: 190, sort: 'spec', cell: (r) => r.spec },
  { key: 'fg_code', hide: true, label: 'Mã HH', w: 84, sort: 'fg_code', td: { ...NOWRAP, ...MUTED }, cell: (r) => r.fg_code },
  { key: 'invoice_no', hide: true, label: 'Số HĐ', w: 160, sort: 'invoice_no', td: NOWRAP, cell: (r) => r.invoice_no },
  { key: 'required_date', hide: true, label: 'Ngày cần', w: 88, sort: 'required_date', td: NOWRAP, cell: (r) => fmtDate(r.required_date) },
  { key: 'unit', label: 'ĐVT', w: 56, sort: 'unit', cell: (r) => r.unit },
  { key: 'qty_request', hide: true, label: 'SL YC', w: 76, sort: 'qty_request', td: R, cell: (r) => fmt(r.qty_request) },
  { key: 'qty_order', label: 'SL đặt', w: 76, sort: 'qty_order', td: R, cell: (r) => fmt(r.qty_order) },
  { key: 'price', label: 'Đơn giá', w: 96, sort: 'price', td: R, cell: (r) => fmt(r.price) },
  { key: 'vat', hide: true, label: 'VAT%', w: 60, sort: 'vat', td: R, cell: (r) => r.vat || 0 },
  { key: 'order_amount', label: 'Thành tiền ĐH', w: 128, td: { ...R, fontWeight: 600 }, cell: (r) => fmt(r.order_amount) },
  { key: 'progress_status', label: 'Tiến độ', w: 176, sort: 'progress_status', cell: (r) => pgBadge(r.progress_status) },
  { key: 'delivery_no', hide: true, label: 'Lần giao', w: 72, sort: 'delivery_no', td: R, cell: (r) => r.delivery_no ?? '—' },
  { key: 'warehouse_code', hide: true, label: 'Kho', w: 96, sort: 'warehouse_code', td: NOWRAP, cell: (r) => r.warehouse_code },
  { key: 'carrier_code', hide: true, label: 'Mã ĐVVC', w: 160, sort: 'carrier_code', sup: true, td: { ...NOWRAP, ...MUTED }, cell: (r) => r.carrier_code },
  { key: 'carrier_name', hide: true, label: 'Đơn vị VC', w: 160, sort: 'carrier_name', sup: true, cell: (r) => r.carrier_name },
  { key: 'ship_qty', hide: true, label: 'SL giao', w: 84, sort: 'ship_qty', td: R, cell: (r) => fmt(r.ship_qty) },
  { key: 'received_qty', label: 'SL nhận', w: 84, sort: 'received_qty', td: R, cell: (r) => fmt(r.received_qty) },
  { key: 'promised_date', hide: true, label: 'Cam kết giao', w: 100, sort: 'promised_date', td: NOWRAP, cell: (r) => fmtDate(r.promised_date) },
  { key: 'expected_date', hide: true, label: 'Dự kiến nhận', w: 100, sort: 'expected_date', td: NOWRAP, cell: (r) => fmtDate(r.expected_date) },
  { key: 'received_date', label: 'Ngày nhận', w: 100, sort: 'received_date', td: NOWRAP, cell: (r) => fmtDate(r.received_date) },
  { key: 'std_days', hide: true, label: 'Ngày QĐ', w: 76, sort: 'std_days', td: R, cell: (r) => r.std_days || 0 },
  { key: 'regulated_date', hide: true, label: 'Ngày quy định', w: 108, sort: 'regulated_date', td: NOWRAP, cell: (r) => fmtDate(r.regulated_date) },
  { key: 'diff_promise', hide: true, label: 'CL cam kết', w: 84, sort: 'diff_promise', td: R, cell: (r) => diffCell(r.diff_promise) },
  { key: 'diff_regulated', hide: true, label: 'CL quy định', w: 84, sort: 'diff_regulated', td: R, cell: (r) => diffCell(r.diff_regulated) },
  { key: 'diff_required', hide: true, label: 'CL vs YC', w: 76, sort: 'diff_required', td: R, cell: (r) => diffCell(r.diff_required) },
  { key: 'delivery_invoice_no', hide: true, label: 'Số HĐ (giao)', w: 160, sort: 'delivery_invoice_no', td: NOWRAP, cell: (r) => r.delivery_invoice_no },
  { key: 'shipping_unit_price', hide: true, label: 'Đơn giá VC', w: 96, sort: 'shipping_unit_price', sup: true, td: R, cell: (r) => fmt(r.shipping_unit_price) },
  { key: 'shipping_amount', hide: true, label: 'Tiền VC', w: 108, sort: 'shipping_amount', sup: true, td: R, cell: (r) => fmt(r.shipping_amount) },
  { key: 'qc_result', hide: true, label: 'QC', w: 64, sort: 'qc_result', cell: (r) => r.qc_result },
  { key: 'delivery_status', hide: true, label: 'TT giao', w: 108, sort: 'delivery_status', cell: (r) => r.delivery_status },
  { key: 'amount', label: 'Thành tiền nhận', w: 128, td: { ...R, fontWeight: 600 }, cell: (r) => fmt(r.amount) },
  { key: 'document_status', label: 'Hồ sơ CT', w: 150, sort: 'document_status', cell: (r) => r.document_status },
]

export default function PurchaseProgress() {
  const navigate = useNavigate()
  const { can } = useAuth()
  const canOpenPO = can('purchase_order', 'read')   // không có quyền xem ĐMH -> KHÔNG cho click (tránh ra trang trắng)
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [showSupplier, setShowSupplier] = useState(true)
  const [companies, setCompanies] = useState<any[]>([])
  const [departments, setDepartments] = useState<any[]>([])
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [sortBy, setSortBy] = useState('')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [f, setF] = useState<any>(EMPTY_FILTERS)
  const setFilter = (k: string, v: any) => { setF((s: any) => ({ ...s, [k]: v })); setPage(1) }

  function handleSort(key: string) {
    const nextDir: 'asc' | 'desc' = (sortBy === key && sortDir === 'asc') ? 'desc' : 'asc'
    setSortBy(key); setSortDir(nextDir); setPage(1)
  }

  async function load() {
    const p: any = { page, page_size: pageSize }
    Object.entries(f).forEach(([k, v]) => { const val = typeof v === 'string' ? v.trim() : v; if (val) p[k] = val })
    if (sortBy) { p.sort_by = sortBy; p.sort_dir = sortDir }
    const r = await api.get('/api/purchase-progress', { params: p })
    const d = r.data.data
    setRows(d.items); setTotal(d.total); setShowSupplier(d.show_supplier)
  }
  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items))
    api.get('/api/departments', { params: { page_size: 500 } }).then((r) => setDepartments(r.data.data.items)).catch(() => {})
  }, [])

  // Tự tìm khi đổi filter (debounce) / đổi trang / đổi sort
  const timer = useRef<any>(null)
  useEffect(() => {
    clearTimeout(timer.current)
    timer.current = setTimeout(load, 300)
    return () => clearTimeout(timer.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [f, page, pageSize, sortBy, sortDir])

  const companyName = (cid: number) => companies.find((c) => c.id === cid)?.name || '—'

  // Chuyển khai báo cột nội bộ sang TableColumn dùng chung (ẩn/hiện cột + kéo giãn + header thống nhất)
  const tableColumns = useMemo<TableColumn<any>[]>(() => {
    const ctx: Ctx = { companyName, canOpenPO, navigate, page, pageSize }
    return COLS.filter((c) => !c.sup || showSupplier).map((c) => ({
      key: c.key,
      label: c.label,
      sort: c.sort,
      width: c.w,
      align: c.td?.textAlign === 'right' ? 'right' : 'left',
      defaultHidden: c.hide,
      td: c.td,
      cell: (r: any, i: number) => c.cell(r, ctx, i),
    }))
  }, [showSupplier, companies, canOpenPO, page, pageSize])

  const table = useTableColumns('purchase-progress', tableColumns)
  const minW = table.columns.reduce((s, c) => s + (typeof c.width === 'number' ? c.width : 100), 0)

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
        <h2 className="page-title" style={{ margin: 0 }}>Tiến độ mua hàng</h2>
        <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>Theo từng lần giao hàng · {fmt(total)} dòng</div>
      </div>

      <FilterPanel onClear={() => setF(EMPTY_FILTERS)} canClear={Object.values(f).some((v) => v)}>
        <FilterItem label="Công ty">
          <SearchSelect value={f.company_id} placeholder="Tất cả"
            options={companies.map((c) => ({ value: String(c.id), label: c.name }))}
            onChange={(v) => setFilter('company_id', v)} />
        </FilterItem>
        <FilterItem label="Bộ phận">
          <SearchSelect value={f.department} placeholder="Tất cả"
            options={departments.map((d) => ({ value: d.name, label: d.name }))}
            onChange={(v) => setFilter('department', v)} />
        </FilterItem>
        <FilterItem label="Tìm kiếm" grow>
          <input value={f.q} placeholder="Mã ĐMH / PYC / mã, tên SP…" onChange={(e) => setFilter('q', e.target.value)} />
        </FilterItem>

        <FilterItem label="Tháng (đặt hàng)" width={150} secondary active={!!f.month}>
          <input type="month" value={f.month} onChange={(e) => setFilter('month', e.target.value)} />
        </FilterItem>
        <FilterItem label="Trạng thái tiến độ" secondary active={!!f.status}>
          <SearchSelect value={f.status} placeholder="Tất cả"
            options={PG_OPTS.map((s) => ({ value: s, label: s }))}
            onChange={(v) => setFilter('status', v)} />
        </FilterItem>
        <FilterItem label="Tình trạng nhận" width={200} secondary active={!!f.recv_state}>
          <select value={f.recv_state} onChange={(e) => setFilter('recv_state', e.target.value)}>
            <option value="">Tất cả</option>
            <option value="unreceived">Chưa giao (SL nhận = 0)</option>
            <option value="under">Chưa đủ (nhận &lt; đặt)</option>
            <option value="full">Đã đủ (nhận ≥ đặt)</option>
          </select>
        </FilterItem>
        <FilterItem label="Ngày đặt hàng" width={260} secondary active={!!(f.order_date_from || f.order_date_to)}>
          <DateRangePicker block value={{ from: f.order_date_from, to: f.order_date_to }}
            onChange={(v) => { setF((s: any) => ({ ...s, order_date_from: v.from, order_date_to: v.to })); setPage(1) }} />
        </FilterItem>
        <FilterItem label="Ngày nhận" width={260} secondary active={!!(f.received_date_from || f.received_date_to)}>
          <DateRangePicker block value={{ from: f.received_date_from, to: f.received_date_to }}
            onChange={(v) => { setF((s: any) => ({ ...s, received_date_from: v.from, received_date_to: v.to })); setPage(1) }} />
        </FilterItem>
      </FilterPanel>

      <div className="card table-card">
        <TableToolbar {...table} onRefresh={load} />
        <div className="table-scroll">
          <table className="dense" style={{ minWidth: minW, tableLayout: 'fixed' }}>
            <TableColGroup columns={table.columns} colW={table.colW} />
            <TableHead columns={table.columns} startResize={table.startResize}
              sortBy={sortBy} sortDir={sortDir} onSort={handleSort} />
            <tbody>
              {rows.map((r, i) => (
                <tr key={`${r.item_id}-${r.delivery_id ?? 'x'}-${i}`}>
                  <TableCells columns={table.columns} row={r} index={i} />
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={table.columns.length} className="table-empty">Chưa có dữ liệu tiến độ</td></tr>}
            </tbody>
          </table>
        </div>
        <div className="table-foot">
          <Pagination page={page} pageSize={pageSize} total={total}
            onChange={(p, s) => { setPage(p); setPageSize(s) }} />
        </div>
      </div>
      <div style={{ marginTop: 8, fontSize: 12.5, color: 'var(--muted)' }}>
        * Mỗi dòng = 1 lần giao của 1 sản phẩm trên đơn mua hàng.
        {!showSupplier && ' Cột nhà cung cấp & chi phí vận chuyển được ẩn theo quyền của bạn.'}
      </div>
    </div>
  )
}
