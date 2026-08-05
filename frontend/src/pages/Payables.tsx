import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import SearchSelect from '../components/SearchSelect'
import NumberInput from '../components/NumberInput'
import DateRangePicker from '../components/DateRangePicker'
import FilterPanel, { FilterItem } from '../components/FilterPanel'
import Pagination from '../components/Pagination'
import { fmtDateTime } from '../utils/datetime'
import TableHead, { TableCells } from '../components/TableHead'
import TableToolbar from '../components/TableToolbar'
import { useTableColumns, TableColumn } from '../hooks/useTableColumns'

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
const AGING_CLS: Record<string, string> = { 'Chưa đến hạn': 'gray', '1-30': 'warn', '31-60': 'warn', '61-90': 'err', '>90': 'err' }
const agingBadge = (a: string) => <span className={'badge ' + (AGING_CLS[a] || 'gray')}>{a === 'Chưa đến hạn' ? a : a + ' ngày'}</span>
// Nhãn trạng thái đầy đủ (DB lưu viết tắt). Giá trị lọc gửi lên vẫn dùng mã DB.
const ST_LABEL: Record<string, string> = { 'Chờ TT': 'Chờ thanh toán', 'Trả một phần': 'Thanh toán một phần', 'Đã TT': 'Đã thanh toán' }
const ST_OPTIONS = [
  { value: 'Chờ TT', label: 'Chờ thanh toán' },
  { value: 'Trả một phần', label: 'Thanh toán một phần' },
  { value: 'Đã TT', label: 'Đã thanh toán' },
]
const stBadge = (s: string) => <span className={'badge ' + (s === 'Đã TT' ? 'ok' : s === 'Trả một phần' ? 'warn' : 'gray')}>{ST_LABEL[s] || s}</span>

/** Bộ lọc mặc định — năm hiện tại, các ô còn lại trống. Dùng cho nút "Xóa lọc". */
const EMPTY_FILTERS = (year: number) => ({
  company_id: '', supplier_code: '', po_code: '', invoice_no: '',
  source_type: '', status: '', aging: '', incur_from: '', incur_to: '',
  amount_from: 0, amount_to: 0, year: String(year),
})

export default function Payables() {
  const { can } = useAuth()
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const [rows, setRows] = useState<any[]>([])
  const [sum, setSum] = useState<any>({ total: 0, paid: 0, remaining: 0, overdue: 0 })
  const [companies, setCompanies] = useState<any[]>([])
  const [suppliers, setSuppliers] = useState<any[]>([])
  const thisYear = new Date().getFullYear()
  // supplier_code có thể được truyền qua ?supplier= (từ dashboard "Việc cần xử lý")
  const [f, setF] = useState<any>({
    ...EMPTY_FILTERS(thisYear),
    supplier_code: searchParams.get('supplier') || '',
    po_code: searchParams.get('po_code') || '',
    year: (searchParams.get('supplier') || searchParams.get('po_code')) ? 'all' : String(thisYear),   // vào từ dashboard: bỏ giới hạn năm để thấy đủ nợ
  })
  const [sel, setSel] = useState<number[]>([])
  const [err, setErr] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [sortField, setSortField] = useState<string>('')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const setFilter = (k: string, v: any) => setF((s: any) => ({ ...s, [k]: v }))
  // Có khác bộ lọc mặc định không → quyết định hiện nút "Xóa lọc"
  const dirty = useMemo(() => {
    const d: any = EMPTY_FILTERS(thisYear)
    return Object.keys(d).some((k) => String(f[k] ?? '') !== String(d[k]))
  }, [f, thisYear])

  function handleSort(field: string) {
    if (sortField === field) setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'))
    else { setSortField(field); setSortDir('asc') }
    setPage(1)
  }
  const params = () => {
    const p: any = { page_size: 1000 }
    Object.entries(f).forEach(([k, v]) => {
      const val = typeof v === 'string' ? v.trim() : v   // cắt space thừa để LIKE khớp
      if (val) p[k] = val
    })
    return p
  }
  async function load() {
    const [r, s] = await Promise.all([
      api.get('/api/payables', { params: params() }),
      api.get('/api/payables/summary', { params: params() }),
    ])
    setRows(r.data.data.items); setSum(s.data.data); setSel([]); setPage(1)
  }
  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items))
    api.get('/api/suppliers', { params: { page_size: 1000 } }).then((r) => setSuppliers(r.data.data.items))
  }, [])

  // Tự động tìm khi đổi bất kỳ filter nào (debounce 300ms) — không cần bấm nút Lọc
  const timer = useRef<any>(null)
  useEffect(() => {
    clearTimeout(timer.current)
    timer.current = setTimeout(load, 300)
    return () => clearTimeout(timer.current)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [f])

  const companyName = (cid: number) => companies.find((c) => c.id === cid)?.name || '—'
  const payable = (r: any) => r.status !== 'Đã TT' && r.remaining > 0 && !!(r.invoice_no || '').trim()
  const toggle = (id: number) => setSel((s) => s.includes(id) ? s.filter((x) => x !== id) : [...s, id])

  const selSuppliers = new Set(rows.filter((r) => sel.includes(r.id)).map((r) => r.supplier_code))

  // Sort phía client (dữ liệu đã tải hết); cột "company" sort theo tên công ty
  const sortedRows = (() => {
    if (!sortField) return rows
    const dir = sortDir === 'asc' ? 1 : -1
    const val = (r: any) => (sortField === 'company' ? companyName(r.company_id) : r[sortField])
    return [...rows].sort((a, b) => {
      const av = val(a), bv = val(b)
      if (av == null || av === '') return 1
      if (bv == null || bv === '') return -1
      if (typeof av === 'number' && typeof bv === 'number') return (av - bv) * dir
      return String(av).localeCompare(String(bv), 'vi') * dir
    })
  })()
  const paged = sortedRows.slice((page - 1) * pageSize, page * pageSize)

  const R: React.CSSProperties = { textAlign: 'right' }
  const COLS = useMemo<TableColumn<any>[]>(() => [
    // Cột chọn: luôn hiện (không cho ẩn) vì là chỗ tick tạo yêu cầu thanh toán
    {
      key: 'sel', label: '', width: 34, align: 'center', fixed: true,
      cell: (r) => <input type="checkbox" disabled={!payable(r)} checked={sel.includes(r.id)} onChange={() => toggle(r.id)} />,
    },
    { key: 'supplier_name', label: 'Nhà cung cấp', sort: 'supplier_name', cell: (r) => r.supplier_name || r.supplier_code },
    { key: 'supplier_code', label: 'Mã NCC', sort: 'supplier_code', td: { color: 'var(--muted)' } },
    { key: 'source_type', label: 'Loại', sort: 'source_type', cell: (r) => (r.source_type === 'shipping' ? 'Vận chuyển' : 'Hàng hóa') },
    { key: 'company', label: 'Công ty', sort: 'company', cell: (r) => companyName(r.company_id) },
    { key: 'po_code', label: 'PO', sort: 'po_code' },
    {
      key: 'invoice_no', label: 'Số hóa đơn', sort: 'invoice_no',
      cell: (r) => (r.invoice_no ? r.invoice_no : <span style={{ color: 'var(--red)', fontSize: 12 }}>chưa có HĐ</span>),
    },
    { key: 'created_at', label: 'Ngày phát sinh', sort: 'created_at', cell: (r) => fmtDateTime(r.created_at) || r.incur_date },
    { key: 'due_date', label: 'Hạn trả', sort: 'due_date' },
    { key: 'aging', label: 'Tuổi nợ', sort: 'aging', cell: (r) => agingBadge(r.aging) },
    { key: 'total', label: 'Tổng nợ', sort: 'total', align: 'right', td: R, cell: (r) => fmt(r.total) },
    { key: 'paid_amount', label: 'Đã trả', sort: 'paid_amount', align: 'right', td: R, cell: (r) => fmt(r.paid_amount) },
    { key: 'remaining', label: 'Còn lại', sort: 'remaining', align: 'right', td: { ...R, fontWeight: 600 }, cell: (r) => fmt(r.remaining) },
    { key: 'status', label: 'Trạng thái', sort: 'status', cell: (r) => stBadge(r.status) },
  ], [sel, companies])
  const table = useTableColumns('payables', COLS)

  // CR-025: KHÔNG tạo phiếu ngay nữa — chuyển các khoản đã tick sang màn "Tạo yêu cầu thanh toán"
  // qua URL/state; chỉ khi bấm "Tạo phiếu" ở màn đó mới ghi DB (tránh đẻ phiếu nháp).
  function createRequest() {
    setErr('')
    const picked = rows.filter((r) => sel.includes(r.id))
    if (!picked.length) return
    navigate(`/payment-requests/new?payables=${picked.map((r) => r.id).join(',')}`, { state: { rows: picked } })
  }

  const Card = ({ label, val, color }: any) => (
    <div className="card" style={{ padding: 14, flex: 1, minWidth: 150 }}>
      <div style={{ fontSize: 12, color: 'var(--muted)' }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700, color: color || 'var(--navy)' }}>{fmt(val)}</div>
    </div>
  )

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
        <h2 className="page-title" style={{ margin: 0 }}>Công nợ phải trả</h2>
        {can('payment_request', 'create') && (
          <button className="btn" disabled={!sel.length} onClick={createRequest}>
            <i className="ti ti-receipt" />Tạo yêu cầu thanh toán {sel.length ? `(${sel.length} khoản · ${selSuppliers.size} NCC)` : ''}
          </button>
        )}
      </div>

      <div style={{ display: 'flex', gap: 10, marginBottom: 12, flexWrap: 'wrap' }}>
        <Card label="Tổng nợ" val={sum.total} />
        <Card label="Đã trả" val={sum.paid} color="var(--green)" />
        <Card label="Còn phải trả" val={sum.remaining} color="var(--teal)" />
        <Card label="Quá hạn" val={sum.overdue} color="var(--red)" />
      </div>

      <FilterPanel onClear={() => setF(EMPTY_FILTERS(thisYear))} canClear={dirty}>
        <FilterItem label="Công ty">
          <SearchSelect value={f.company_id} placeholder="Tất cả"
            options={companies.map((c) => ({ value: String(c.id), label: c.name }))}
            onChange={(v) => setFilter('company_id', v)} />
        </FilterItem>
        <FilterItem label="Nhà cung cấp" width={200}>
          <SearchSelect value={f.supplier_code} placeholder="Tất cả"
            options={suppliers.map((c) => ({ value: c.code, label: c.name }))}
            onChange={(v) => setFilter('supplier_code', v)} />
        </FilterItem>
        <FilterItem label="Trạng thái">
          <SearchSelect value={f.status} placeholder="Tất cả"
            options={ST_OPTIONS}
            onChange={(v) => setFilter('status', v)} />
        </FilterItem>

        <FilterItem label="PO" width={140} secondary active={!!f.po_code}>
          <input value={f.po_code} placeholder="Mã PO…" onChange={(e) => setFilter('po_code', e.target.value)} />
        </FilterItem>
        <FilterItem label="Số hóa đơn" width={140} secondary active={!!f.invoice_no}>
          <input value={f.invoice_no} placeholder="Số HĐ…" onChange={(e) => setFilter('invoice_no', e.target.value)} />
        </FilterItem>
        <FilterItem label="Loại nợ" width={150} secondary active={!!f.source_type}>
          <SearchSelect value={f.source_type} placeholder="Tất cả"
            options={[{ value: 'goods', label: 'Hàng hóa' }, { value: 'shipping', label: 'Vận chuyển' }]}
            onChange={(v) => setFilter('source_type', v)} />
        </FilterItem>
        <FilterItem label="Tuổi nợ" width={150} secondary active={!!f.aging}>
          <SearchSelect value={f.aging} placeholder="Tất cả"
            options={['Chưa đến hạn', '1-30', '31-60', '61-90', '>90']}
            onChange={(v) => setFilter('aging', v)} />
        </FilterItem>
        <FilterItem label="Năm" width={120} secondary active={String(f.year) !== String(thisYear)}>
          <SearchSelect value={String(f.year)} placeholder="Tất cả"
            options={[{ value: 'all', label: 'Tất cả' }, ...[thisYear, thisYear - 1, thisYear - 2].map((y) => ({ value: String(y), label: String(y) }))]}
            onChange={(v) => setFilter('year', v)} />
        </FilterItem>
        <FilterItem label="Ngày phát sinh" width={260} secondary active={!!(f.incur_from || f.incur_to)}>
          <DateRangePicker block value={{ from: f.incur_from, to: f.incur_to }}
            onChange={(v) => setF((s: any) => ({ ...s, incur_from: v.from, incur_to: v.to }))} />
        </FilterItem>
        <FilterItem label="Số tiền (từ → đến)" width={230} secondary active={!!(f.amount_from || f.amount_to)}>
          <div className="filter-pair">
            <NumberInput value={f.amount_from} onChange={(v) => setFilter('amount_from', v)} placeholder="Từ…" />
            <span style={{ color: 'var(--muted)' }}>→</span>
            <NumberInput value={f.amount_to} onChange={(v) => setFilter('amount_to', v)} placeholder="Đến…" />
          </div>
        </FilterItem>
      </FilterPanel>

      {err && <div className="err" style={{ marginBottom: 8 }}>{err}</div>}
      <div className="card table-card">
        <TableToolbar {...table} onRefresh={load} />
        <div className="table-scroll">
          <table className="dense" style={{ minWidth: 1220 }}>
            <TableHead {...table} sortBy={sortField} sortDir={sortDir} onSort={handleSort} />
            <tbody>
              {paged.map((r, i) => (
                <tr key={r.id} style={sel.includes(r.id) ? { background: '#f0f9ff' } : {}}>
                  <TableCells columns={table.columns} row={r} index={i} />
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={table.columns.length} className="table-empty">Chưa có công nợ</td></tr>}
            </tbody>
          </table>
        </div>
        <div className="table-foot">
          <Pagination page={page} pageSize={pageSize} total={rows.length}
            onChange={(p, s) => { setPage(p); setPageSize(s) }} />
        </div>
      </div>
      <div style={{ marginTop: 8, fontSize: 12.5, color: 'var(--muted)' }}>
        * Chỉ chọn được khoản nợ <b>đã có Số hóa đơn</b> để tạo đề nghị thanh toán. (Công nợ hàng: nhập Số HĐ ở chi tiết sản phẩm trên đơn; Vận chuyển: tự lấy Mã MISA + Mã SP.)
      </div>
      {sel.length > 0 && selSuppliers.size > 1 && (
        <div style={{ marginTop: 8, fontSize: 13, color: 'var(--muted)' }}>
          * Đang chọn {selSuppliers.size} nhà cung cấp → hệ thống sẽ tách thành {selSuppliers.size} phiếu yêu cầu thanh toán riêng.
        </div>
      )}
    </div>
  )
}
