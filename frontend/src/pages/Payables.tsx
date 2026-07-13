import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { toast } from '../components/toast'
import { useAuth } from '../auth/AuthContext'
import SearchSelect from '../components/SearchSelect'
import NumberInput from '../components/NumberInput'
import Pagination from '../components/Pagination'

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
    company_id: '',
    supplier_code: searchParams.get('supplier') || '',
    po_code: searchParams.get('po_code') || '',
    invoice_no: '',
    source_type: '', status: '', aging: '', incur_from: '', incur_to: '', amount_from: 0, amount_to: 0,
    year: (searchParams.get('supplier') || searchParams.get('po_code')) ? 'all' : String(thisYear),   // vào từ dashboard: bỏ giới hạn năm để thấy đủ nợ
  })
  const [sel, setSel] = useState<number[]>([])
  const [err, setErr] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const setFilter = (k: string, v: any) => setF((s: any) => ({ ...s, [k]: v }))
  const lbl = { fontSize: 12, color: 'var(--muted)' } as const

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
  const paged = rows.slice((page - 1) * pageSize, page * pageSize)

  async function createRequest() {
    setErr('')
    const lines = rows.filter((r) => sel.includes(r.id)).map((r) => ({ payable_id: r.id, amount: r.remaining }))
    if (!lines.length) return
    try {
      const r = await api.post('/api/payment-requests', { request_date: new Date().toISOString().slice(0, 10), lines })
      const created = r.data.data
      toast.success(`Đã tạo ${created.length} phiếu yêu cầu thanh toán (mỗi nhà cung cấp 1 phiếu).`)
      if (created.length === 1) navigate(`/payment-requests/${created[0].id}`)
      else navigate('/payment-requests')
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi tạo yêu cầu thanh toán') }
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

      <div className="card filters" style={{ padding: 14, marginBottom: 12, display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div style={{ minWidth: 170 }}><label style={lbl}>Công ty</label>
          <SearchSelect value={f.company_id} placeholder="Tất cả"
            options={companies.map((c) => ({ value: String(c.id), label: c.name }))}
            onChange={(v) => setFilter('company_id', v)} />
        </div>
        <div style={{ minWidth: 190 }}><label style={lbl}>Nhà cung cấp</label>
          <SearchSelect value={f.supplier_code} placeholder="Tất cả"
            options={suppliers.map((c) => ({ value: c.code, label: c.name }))}
            onChange={(v) => setFilter('supplier_code', v)} />
        </div>
        <div style={{ minWidth: 120 }}><label style={lbl}>PO</label>
          <input value={f.po_code} placeholder="Mã PO…" onChange={(e) => setFilter('po_code', e.target.value)} /></div>
        <div style={{ minWidth: 120 }}><label style={lbl}>Số hóa đơn</label>
          <input value={f.invoice_no} placeholder="Số HĐ…" onChange={(e) => setFilter('invoice_no', e.target.value)} /></div>
        <div style={{ minWidth: 140 }}><label style={lbl}>Loại nợ</label>
          <SearchSelect value={f.source_type} placeholder="Tất cả"
            options={[{ value: 'goods', label: 'Hàng hóa' }, { value: 'shipping', label: 'Vận chuyển' }]}
            onChange={(v) => setFilter('source_type', v)} />
        </div>
        <div style={{ minWidth: 170 }}><label style={lbl}>Trạng thái</label>
          <SearchSelect value={f.status} placeholder="Tất cả"
            options={ST_OPTIONS}
            onChange={(v) => setFilter('status', v)} />
        </div>
        <div style={{ minWidth: 130 }}><label style={lbl}>Tuổi nợ</label>
          <SearchSelect value={f.aging} placeholder="Tất cả"
            options={['Chưa đến hạn', '1-30', '31-60', '61-90', '>90']}
            onChange={(v) => setFilter('aging', v)} />
        </div>
        <div style={{ minWidth: 110 }}><label style={lbl}>Năm</label>
          <SearchSelect value={String(f.year)} placeholder="Tất cả"
            options={[{ value: 'all', label: 'Tất cả' }, ...[thisYear, thisYear - 1, thisYear - 2].map((y) => ({ value: String(y), label: String(y) }))]}
            onChange={(v) => setFilter('year', v)} />
        </div>
        <div><label style={lbl}>Ngày phát sinh từ</label><input type="date" value={f.incur_from} onChange={(e) => setFilter('incur_from', e.target.value)} /></div>
        <div><label style={lbl}>đến</label><input type="date" value={f.incur_to} onChange={(e) => setFilter('incur_to', e.target.value)} /></div>
        <div style={{ minWidth: 130 }}><label style={lbl}>Số tiền từ</label>
          <NumberInput value={f.amount_from} onChange={(v) => setFilter('amount_from', v)} placeholder="" /></div>
        <div style={{ minWidth: 130 }}><label style={lbl}>đến</label>
          <NumberInput value={f.amount_to} onChange={(v) => setFilter('amount_to', v)} placeholder="" /></div>
      </div>

      {err && <div className="err" style={{ marginBottom: 8 }}>{err}</div>}
      <div className="card">
        <div className="items-scroll">
          <table className="items-table" style={{ minWidth: 1220 }}>
            <thead>
              <tr>
                <th style={{ width: 34 }} />
                <th>Nhà cung cấp</th><th>Mã NCC</th><th>Loại</th><th>Công ty</th><th>PO</th><th>Số hóa đơn</th>
                <th>Ngày phát sinh</th><th>Hạn trả</th><th>Tuổi nợ</th>
                <th style={{ textAlign: 'right' }}>Tổng nợ</th><th style={{ textAlign: 'right' }}>Đã trả</th>
                <th style={{ textAlign: 'right' }}>Còn lại</th><th>Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {paged.map((r) => (
                <tr key={r.id} style={sel.includes(r.id) ? { background: '#f0f9ff' } : {}}>
                  <td style={{ textAlign: 'center' }}>
                    <input type="checkbox" disabled={!payable(r)} checked={sel.includes(r.id)} onChange={() => toggle(r.id)} />
                  </td>
                  <td>{r.supplier_name || r.supplier_code}</td>
                  <td style={{ color: 'var(--muted)' }}>{r.supplier_code}</td>
                  <td>{r.source_type === 'shipping' ? 'Vận chuyển' : 'Hàng hóa'}</td>
                  <td>{companyName(r.company_id)}</td>
                  <td>{r.po_code}</td>
                  <td>{r.invoice_no ? r.invoice_no : <span style={{ color: 'var(--red)', fontSize: 12 }}>chưa có HĐ</span>}</td>
                  <td>{r.incur_date}</td><td>{r.due_date}</td><td>{agingBadge(r.aging)}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(r.total)}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(r.paid_amount)}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(r.remaining)}</td>
                  <td>{stBadge(r.status)}</td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={14} style={{ textAlign: 'center', color: '#999', padding: 20 }}>Chưa có công nợ</td></tr>}
            </tbody>
          </table>
        </div>
        <Pagination page={page} pageSize={pageSize} total={rows.length}
          onChange={(p, s) => { setPage(p); setPageSize(s) }} />
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
