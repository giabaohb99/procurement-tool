import { useEffect, useRef, useState } from 'react'
import type { CSSProperties, ReactNode } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import SearchSelect from '../components/SearchSelect'
import Pagination from '../components/Pagination'
import { fmtDate } from '../utils/datetime'
import { useResizableColumns, ResizeHandle } from '../hooks/useResizableColumns'

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
  td?: CSSProperties     // style riêng cho <td>
  cell: (r: any, ctx: Ctx, i: number) => ReactNode
}

// Khai báo 1 lần: dùng chung cho <colgroup>, <thead> và <tbody> nên index luôn khớp.
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
  { key: 'misa_code', label: 'Mã MISA', w: 92, sort: 'misa_code', td: { ...NOWRAP, ...MUTED }, cell: (r) => r.misa_code },
  { key: 'pr_code', label: 'Mã PYC', w: 104, sort: 'pr_code', td: { ...NOWRAP, ...MUTED }, cell: (r) => r.pr_code },
  { key: 'company', label: 'Công ty', w: 180, cell: (r, c) => c.companyName(r.company_id) },
  { key: 'department', label: 'Bộ phận', w: 124, sort: 'department', cell: (r) => r.department },
  { key: 'supplier_code', label: 'Mã NCC', w: 130, sort: 'supplier_code', sup: true, td: { ...NOWRAP, ...MUTED }, cell: (r) => r.supplier_code },
  { key: 'supplier_name', label: 'Nhà cung cấp', w: 230, sort: 'supplier_name', sup: true, cell: (r) => r.supplier_name },
  { key: 'nspt', label: 'NSPT', w: 150, sort: 'nspt', cell: (r) => r.nspt },
  { key: 'order_date', label: 'Ngày ĐH', w: 88, sort: 'order_date', td: NOWRAP, cell: (r) => fmtDate(r.order_date) },
  { key: 'product_code', label: 'Mã SP', w: 140, sort: 'product_code', td: { ...NOWRAP, ...MUTED }, cell: (r) => r.product_code },
  { key: 'product_name', label: 'Tên SP', w: 220, sort: 'product_name', td: { fontWeight: 500 }, cell: (r) => r.product_name },
  { key: 'invoice_name', label: 'Tên hóa đơn', w: 150, sort: 'invoice_name', cell: (r) => r.invoice_name },
  { key: 'item_group', label: 'Nhóm hàng', w: 120, sort: 'item_group', cell: (r) => r.item_group },
  { key: 'spec', label: 'Quy cách', w: 190, sort: 'spec', cell: (r) => r.spec },
  { key: 'fg_code', label: 'Mã HH', w: 84, sort: 'fg_code', td: { ...NOWRAP, ...MUTED }, cell: (r) => r.fg_code },
  { key: 'invoice_no', label: 'Số HĐ', w: 160, sort: 'invoice_no', td: NOWRAP, cell: (r) => r.invoice_no },
  { key: 'required_date', label: 'Ngày cần', w: 88, sort: 'required_date', td: NOWRAP, cell: (r) => fmtDate(r.required_date) },
  { key: 'unit', label: 'ĐVT', w: 56, sort: 'unit', cell: (r) => r.unit },
  { key: 'qty_request', label: 'SL YC', w: 76, sort: 'qty_request', td: R, cell: (r) => fmt(r.qty_request) },
  { key: 'qty_order', label: 'SL đặt', w: 76, sort: 'qty_order', td: R, cell: (r) => fmt(r.qty_order) },
  { key: 'price', label: 'Đơn giá', w: 96, sort: 'price', td: R, cell: (r) => fmt(r.price) },
  { key: 'vat', label: 'VAT%', w: 60, sort: 'vat', td: R, cell: (r) => r.vat || 0 },
  { key: 'order_amount', label: 'Thành tiền ĐH', w: 128, td: { ...R, fontWeight: 600 }, cell: (r) => fmt(r.order_amount) },
  { key: 'progress_status', label: 'Tiến độ', w: 176, sort: 'progress_status', cell: (r) => pgBadge(r.progress_status) },
  { key: 'delivery_no', label: 'Lần giao', w: 72, sort: 'delivery_no', td: R, cell: (r) => r.delivery_no ?? '—' },
  { key: 'warehouse_code', label: 'Kho', w: 96, sort: 'warehouse_code', td: NOWRAP, cell: (r) => r.warehouse_code },
  { key: 'carrier_code', label: 'Mã ĐVVC', w: 160, sort: 'carrier_code', sup: true, td: { ...NOWRAP, ...MUTED }, cell: (r) => r.carrier_code },
  { key: 'carrier_name', label: 'Đơn vị VC', w: 160, sort: 'carrier_name', sup: true, cell: (r) => r.carrier_name },
  { key: 'ship_qty', label: 'SL giao', w: 84, sort: 'ship_qty', td: R, cell: (r) => fmt(r.ship_qty) },
  { key: 'received_qty', label: 'SL nhận', w: 84, sort: 'received_qty', td: R, cell: (r) => fmt(r.received_qty) },
  { key: 'promised_date', label: 'Cam kết giao', w: 100, sort: 'promised_date', td: NOWRAP, cell: (r) => fmtDate(r.promised_date) },
  { key: 'expected_date', label: 'Dự kiến nhận', w: 100, sort: 'expected_date', td: NOWRAP, cell: (r) => fmtDate(r.expected_date) },
  { key: 'received_date', label: 'Ngày nhận', w: 100, sort: 'received_date', td: NOWRAP, cell: (r) => fmtDate(r.received_date) },
  { key: 'std_days', label: 'Ngày QĐ', w: 76, sort: 'std_days', td: R, cell: (r) => r.std_days || 0 },
  { key: 'regulated_date', label: 'Ngày quy định', w: 108, sort: 'regulated_date', td: NOWRAP, cell: (r) => fmtDate(r.regulated_date) },
  { key: 'diff_promise', label: 'CL cam kết', w: 84, sort: 'diff_promise', td: R, cell: (r) => diffCell(r.diff_promise) },
  { key: 'diff_regulated', label: 'CL quy định', w: 84, sort: 'diff_regulated', td: R, cell: (r) => diffCell(r.diff_regulated) },
  { key: 'diff_required', label: 'CL vs YC', w: 76, sort: 'diff_required', td: R, cell: (r) => diffCell(r.diff_required) },
  { key: 'delivery_invoice_no', label: 'Số HĐ (giao)', w: 160, sort: 'delivery_invoice_no', td: NOWRAP, cell: (r) => r.delivery_invoice_no },
  { key: 'shipping_unit_price', label: 'Đơn giá VC', w: 96, sort: 'shipping_unit_price', sup: true, td: R, cell: (r) => fmt(r.shipping_unit_price) },
  { key: 'shipping_amount', label: 'Tiền VC', w: 108, sort: 'shipping_amount', sup: true, td: R, cell: (r) => fmt(r.shipping_amount) },
  { key: 'qc_result', label: 'QC', w: 64, sort: 'qc_result', cell: (r) => r.qc_result },
  { key: 'delivery_status', label: 'TT giao', w: 108, sort: 'delivery_status', cell: (r) => r.delivery_status },
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
  const { startResize, colW } = useResizableColumns('colw:purchase-progress')
  const [f, setF] = useState<any>({
    company_id: '', department: '', month: '', status: '', q: '',
    order_date_from: '', order_date_to: '', received_date_from: '', received_date_to: '',
    recv_state: '',
  })
  const setFilter = (k: string, v: any) => { setF((s: any) => ({ ...s, [k]: v })); setPage(1) }
  const lbl = { fontSize: 12, color: 'var(--muted)' } as const

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
  const ctx: Ctx = { companyName, canOpenPO, navigate, page, pageSize }

  const cols = COLS.filter((c) => !c.sup || showSupplier)
  const minW = cols.reduce((s, c) => s + c.w, 0)

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
        <h2 className="page-title" style={{ margin: 0 }}>Tiến độ mua hàng</h2>
        <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>Theo từng lần giao hàng · {fmt(total)} dòng</div>
      </div>

      <div className="card filters" style={{ padding: 14, marginBottom: 12, display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div style={{ minWidth: 180 }}><label style={lbl}>Công ty</label>
          <SearchSelect value={f.company_id} placeholder="Tất cả"
            options={companies.map((c) => ({ value: String(c.id), label: c.name }))}
            onChange={(v) => setFilter('company_id', v)} />
        </div>
        <div style={{ minWidth: 180 }}><label style={lbl}>Bộ phận</label>
          <SearchSelect value={f.department} placeholder="Tất cả"
            options={departments.map((d) => ({ value: d.name, label: d.name }))}
            onChange={(v) => setFilter('department', v)} />
        </div>
        <div style={{ minWidth: 140 }}><label style={lbl}>Tháng (đặt hàng)</label>
          <input type="month" value={f.month} onChange={(e) => setFilter('month', e.target.value)} /></div>
        <div style={{ minWidth: 180 }}><label style={lbl}>Trạng thái tiến độ</label>
          <SearchSelect value={f.status} placeholder="Tất cả"
            options={PG_OPTS.map((s) => ({ value: s, label: s }))}
            onChange={(v) => setFilter('status', v)} />
        </div>
        <div style={{ minWidth: 190 }}><label style={lbl}>Tình trạng nhận</label>
          <select value={f.recv_state} onChange={(e) => setFilter('recv_state', e.target.value)}>
            <option value="">Tất cả</option>
            <option value="unreceived">Chưa giao (SL nhận = 0)</option>
            <option value="under">Chưa đủ (nhận &lt; đặt)</option>
            <option value="full">Đã đủ (nhận ≥ đặt)</option>
          </select>
        </div>
        <div><label style={lbl}>Ngày ĐH từ</label>
          <input type="date" value={f.order_date_from} onChange={(e) => setFilter('order_date_from', e.target.value)} /></div>
        <div><label style={lbl}>đến</label>
          <input type="date" value={f.order_date_to} onChange={(e) => setFilter('order_date_to', e.target.value)} /></div>
        <div><label style={lbl}>Ngày nhận từ</label>
          <input type="date" value={f.received_date_from} onChange={(e) => setFilter('received_date_from', e.target.value)} /></div>
        <div><label style={lbl}>đến</label>
          <input type="date" value={f.received_date_to} onChange={(e) => setFilter('received_date_to', e.target.value)} /></div>
        <div style={{ minWidth: 200, flex: 1 }}><label style={lbl}>Tìm kiếm</label>
          <input value={f.q} placeholder="Mã ĐMH / PYC / mã, tên SP…" onChange={(e) => setFilter('q', e.target.value)} /></div>
        <button className="btn ghost" onClick={() => setF({
          company_id: '', department: '', month: '', status: '', q: '',
          order_date_from: '', order_date_to: '', received_date_from: '', received_date_to: '',
          recv_state: '',
        })}>Xóa lọc</button>
      </div>

      <div className="card">
        <div className="items-scroll">
          <table className="items-table wide-table" style={{ minWidth: minW, tableLayout: 'fixed' }}>
            <colgroup>
              {cols.map((c, idx) => <col key={c.key} style={{ width: colW(idx, c.w) }} />)}
            </colgroup>
            <thead>
              <tr>
                {cols.map((c, idx) => {
                  const sortable = !!c.sort
                  const active = sortable && sortBy === c.sort
                  const arrow = active ? (sortDir === 'asc' ? ' ▲' : ' ▼') : (sortable ? ' ↕' : '')
                  const right = c.td?.textAlign === 'right'
                  return (
                    <th key={c.key}
                      onClick={sortable ? () => handleSort(c.sort!) : undefined}
                      style={{
                        position: 'relative', paddingRight: 12,
                        textAlign: right ? 'right' : 'left',
                        cursor: sortable ? 'pointer' : 'default', userSelect: 'none',
                      }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                        {c.label}<span style={{ color: active ? 'var(--teal)' : '#cbd5e1' }}>{arrow}</span>
                      </span>
                      <ResizeHandle onMouseDown={(e) => startResize(idx, e)} />
                    </th>
                  )
                })}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={`${r.item_id}-${r.delivery_id ?? 'x'}-${i}`}>
                  {cols.map((c) => <td key={c.key} style={c.td}>{c.cell(r, ctx, i)}</td>)}
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={cols.length} style={{ textAlign: 'center', color: '#999', padding: 20 }}>Chưa có dữ liệu tiến độ</td></tr>}
            </tbody>
          </table>
        </div>
        <Pagination page={page} pageSize={pageSize} total={total}
          onChange={(p, s) => { setPage(p); setPageSize(s) }} />
      </div>
      <div style={{ marginTop: 8, fontSize: 12.5, color: 'var(--muted)' }}>
        * Mỗi dòng = 1 lần giao của 1 sản phẩm trên đơn mua hàng.
        {!showSupplier && ' Cột nhà cung cấp & chi phí vận chuyển được ẩn theo quyền của bạn.'}
      </div>
    </div>
  )
}
