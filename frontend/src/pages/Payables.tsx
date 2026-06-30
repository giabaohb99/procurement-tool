import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
const AGING_CLS: Record<string, string> = { 'Chưa đến hạn': 'gray', '1-30': 'warn', '31-60': 'warn', '61-90': 'err', '>90': 'err' }
const agingBadge = (a: string) => <span className={'badge ' + (AGING_CLS[a] || 'gray')}>{a === 'Chưa đến hạn' ? a : a + ' ngày'}</span>
const stBadge = (s: string) => <span className={'badge ' + (s === 'Đã TT' ? 'ok' : s === 'Trả một phần' ? 'warn' : 'gray')}>{s}</span>

export default function Payables() {
  const { can } = useAuth()
  const navigate = useNavigate()
  const [rows, setRows] = useState<any[]>([])
  const [sum, setSum] = useState<any>({ total: 0, paid: 0, remaining: 0, overdue: 0 })
  const [companies, setCompanies] = useState<any[]>([])
  const [suppliers, setSuppliers] = useState<any[]>([])
  const thisYear = new Date().getFullYear()
  const [f, setF] = useState<any>({ company_id: '', supplier_code: '', source_type: '', status: '', aging: '', year: String(thisYear) })
  const [sel, setSel] = useState<number[]>([])
  const [err, setErr] = useState('')

  const params = () => {
    const p: any = { page_size: 1000 }
    Object.entries(f).forEach(([k, v]) => { if (v) p[k] = v })
    return p
  }
  async function load() {
    const [r, s] = await Promise.all([
      api.get('/api/payables', { params: params() }),
      api.get('/api/payables/summary', { params: params() }),
    ])
    setRows(r.data.data.items); setSum(s.data.data); setSel([])
  }
  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items))
    api.get('/api/suppliers', { params: { page_size: 1000 } }).then((r) => setSuppliers(r.data.data.items))
    load()
  }, [])

  const companyName = (cid: number) => companies.find((c) => c.id === cid)?.name || '—'
  const payable = (r: any) => r.status !== 'Đã TT' && r.remaining > 0
  const toggle = (id: number) => setSel((s) => s.includes(id) ? s.filter((x) => x !== id) : [...s, id])

  const selSuppliers = new Set(rows.filter((r) => sel.includes(r.id)).map((r) => r.supplier_code))

  async function createRequest() {
    setErr('')
    const lines = rows.filter((r) => sel.includes(r.id)).map((r) => ({ payable_id: r.id, amount: r.remaining }))
    if (!lines.length) return
    try {
      const r = await api.post('/api/payment-requests', { request_date: new Date().toISOString().slice(0, 10), lines })
      const created = r.data.data
      alert(`Đã tạo ${created.length} phiếu yêu cầu thanh toán (mỗi nhà cung cấp 1 phiếu).`)
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

      <div className="card" style={{ padding: 14, marginBottom: 12, display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div><label style={{ fontSize: 12, color: 'var(--muted)' }}>Công ty</label><br />
          <select value={f.company_id} onChange={(e) => setF((s: any) => ({ ...s, company_id: e.target.value }))}>
            <option value="">Tất cả</option>{companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div><label style={{ fontSize: 12, color: 'var(--muted)' }}>Nhà cung cấp</label><br />
          <select value={f.supplier_code} onChange={(e) => setF((s: any) => ({ ...s, supplier_code: e.target.value }))}>
            <option value="">Tất cả</option>{suppliers.map((c) => <option key={c.id} value={c.code}>{c.name}</option>)}
          </select>
        </div>
        <div><label style={{ fontSize: 12, color: 'var(--muted)' }}>Loại nợ</label><br />
          <select value={f.source_type} onChange={(e) => setF((s: any) => ({ ...s, source_type: e.target.value }))}>
            <option value="">Tất cả</option><option value="goods">Hàng hóa</option><option value="shipping">Vận chuyển</option>
          </select>
        </div>
        <div><label style={{ fontSize: 12, color: 'var(--muted)' }}>Trạng thái</label><br />
          <select value={f.status} onChange={(e) => setF((s: any) => ({ ...s, status: e.target.value }))}>
            <option value="">Tất cả</option><option value="Chờ TT">Chờ TT</option><option value="Trả một phần">Trả một phần</option><option value="Đã TT">Đã TT</option>
          </select>
        </div>
        <div><label style={{ fontSize: 12, color: 'var(--muted)' }}>Tuổi nợ</label><br />
          <select value={f.aging} onChange={(e) => setF((s: any) => ({ ...s, aging: e.target.value }))}>
            <option value="">Tất cả</option><option value="Chưa đến hạn">Chưa đến hạn</option>
            <option value="1-30">1-30</option><option value="31-60">31-60</option><option value="61-90">61-90</option><option value=">90">&gt;90</option>
          </select>
        </div>
        <div><label style={{ fontSize: 12, color: 'var(--muted)' }}>Năm</label><br />
          <select value={f.year} onChange={(e) => setF((s: any) => ({ ...s, year: e.target.value }))}>
            <option value="all">Tất cả</option>
            {[thisYear, thisYear - 1, thisYear - 2].map((y) => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
        <button className="btn" onClick={load}>Lọc</button>
      </div>

      {err && <div className="err" style={{ marginBottom: 8 }}>{err}</div>}
      <div className="card">
        <div className="items-scroll">
          <table className="items-table" style={{ minWidth: 1100 }}>
            <thead>
              <tr>
                <th style={{ width: 34 }} />
                <th>Nhà cung cấp</th><th>Loại</th><th>Công ty</th><th>PO</th><th>Số HĐ</th>
                <th>Ngày PS</th><th>Hạn trả</th><th>Tuổi nợ</th>
                <th style={{ textAlign: 'right' }}>Tổng nợ</th><th style={{ textAlign: 'right' }}>Đã trả</th>
                <th style={{ textAlign: 'right' }}>Còn lại</th><th>Trạng thái</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((r) => (
                <tr key={r.id} style={sel.includes(r.id) ? { background: '#f0f9ff' } : {}}>
                  <td style={{ textAlign: 'center' }}>
                    <input type="checkbox" disabled={!payable(r)} checked={sel.includes(r.id)} onChange={() => toggle(r.id)} />
                  </td>
                  <td>{r.supplier_name || r.supplier_code}</td>
                  <td>{r.source_type === 'shipping' ? 'Vận chuyển' : 'Hàng hóa'}</td>
                  <td>{companyName(r.company_id)}</td>
                  <td>{r.po_code}</td><td>{r.invoice_no}</td>
                  <td>{r.incur_date}</td><td>{r.due_date}</td><td>{agingBadge(r.aging)}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(r.total)}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(r.paid_amount)}</td>
                  <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(r.remaining)}</td>
                  <td>{stBadge(r.status)}</td>
                </tr>
              ))}
              {rows.length === 0 && <tr><td colSpan={13} style={{ textAlign: 'center', color: '#999', padding: 20 }}>Chưa có công nợ</td></tr>}
            </tbody>
          </table>
        </div>
      </div>
      {sel.length > 0 && selSuppliers.size > 1 && (
        <div style={{ marginTop: 8, fontSize: 13, color: 'var(--muted)' }}>
          * Đang chọn {selSuppliers.size} nhà cung cấp → hệ thống sẽ tách thành {selSuppliers.size} phiếu yêu cầu thanh toán riêng.
        </div>
      )}
    </div>
  )
}
