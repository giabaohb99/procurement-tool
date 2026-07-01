import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { contractExpiryBadge } from '../config/cruds'

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
const SUP_TYPE = [{ value: 'goods', label: 'NCC bán hàng' }, { value: 'transport', label: 'Đơn vị vận chuyển' }]
const LEGAL_TYPE = ['Công ty', 'Cá nhân', 'Hợp danh', 'Hộ kinh doanh']
const TABS = [
  { key: 'info', label: 'Thông tin' },
  { key: 'eval', label: 'Đánh giá' },
  { key: 'contracts', label: 'Hợp đồng' },
  { key: 'payables', label: 'Công nợ' },
]

export default function SupplierDetail() {
  const { id } = useParams()
  const isNew = id === 'new'
  const { can } = useAuth()
  const navigate = useNavigate()
  const [sup, setSup] = useState<any>({ code: '', name: '', legal_type: '', tax_code: '', address: '', supplier_type: 'goods', contact_person: '', phone: '', payment_terms: '', bank_account: '', bank_name: '', vat: 0.08, is_active: true })
  const [tab, setTab] = useState('info')
  const [contracts, setContracts] = useState<any[]>([])
  const [payables, setPayables] = useState<any[]>([])
  const [companies, setCompanies] = useState<any[]>([])
  const [kpi, setKpi] = useState<any>(null)
  const [err, setErr] = useState(''); const [msg, setMsg] = useState('')
  const companyName = (cid: number) => companies.find((c) => c.id === cid)?.name || ''

  async function loadRelated(s: any) {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items))
    if (!s?.code) return
    api.get('/api/contracts', { params: { party_code: s.code, page_size: 500 } }).then((r) => setContracts(r.data.data.items))
    api.get('/api/payables', { params: { supplier_code: s.code, year: 'all', page_size: 500 } }).then((r) => setPayables(r.data.data.items))
    api.get('/api/reports/matrix', { params: { year: 'all' } }).then((r) => {
      const row = (r.data.data.supplier || []).find((x: any) => x.key === s.name)
      setKpi(row || null)
    }).catch(() => {})
  }
  useEffect(() => {
    if (isNew) return
    api.get(`/api/suppliers/${id}`).then((r) => { setSup(r.data.data); loadRelated(r.data.data) })
  }, [id])

  const setH = (k: string, v: any) => setSup((s: any) => ({ ...s, [k]: v }))
  async function save() {
    setErr(''); setMsg('')
    const body = {
      name: sup.name, legal_type: sup.legal_type, tax_code: sup.tax_code, address: sup.address,
      supplier_type: sup.supplier_type, contact_person: sup.contact_person, phone: sup.phone,
      payment_terms: sup.payment_terms, bank_account: sup.bank_account, bank_name: sup.bank_name,
      vat: Number(sup.vat) || 0, is_active: sup.is_active,
    }
    try {
      if (isNew) { const r = await api.post('/api/suppliers', { code: sup.code, ...body }); navigate(`/suppliers/${r.data.data.id}`) }
      else { await api.patch(`/api/suppliers/${id}`, body); setMsg('Đã lưu'); }
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi khi lưu') }
  }
  async function remove() {
    if (!confirm('Xóa nhà cung cấp này?')) return
    try { await api.delete(`/api/suppliers/${id}`); navigate('/suppliers') }
    catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi khi xóa') }
  }

  const payTotal = payables.reduce((s, p) => s + (p.total || 0), 0)
  const payPaid = payables.reduce((s, p) => s + (p.paid_amount || 0), 0)
  const payRemain = payables.reduce((s, p) => s + (p.remaining || 0), 0)

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate('/suppliers')}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>{isNew ? 'Thêm nhà cung cấp' : `${sup.name || ''}`}</h2>
        <span className="badge" style={{ background: sup.supplier_type === 'transport' ? '#e0f2fe' : '#dcfce7', color: sup.supplier_type === 'transport' ? '#0284c7' : '#15803d' }}>
          {sup.supplier_type === 'transport' ? 'Vận chuyển' : 'Bán hàng'}
        </span>
        <span style={{ flex: 1 }} />
        {tab === 'info' && can('supplier', isNew ? 'create' : 'write') && <button className="btn" onClick={save}>{isNew ? 'Tạo' : 'Lưu'}</button>}
        {!isNew && tab === 'info' && can('supplier', 'delete') && <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={remove}><i className="ti ti-trash" />Xóa</button>}
      </div>

      {!isNew && (
        <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap', marginBottom: 14, borderBottom: '1px solid var(--border)' }}>
          {TABS.map((t) => (
            <button key={t.key} onClick={() => setTab(t.key)} style={{ border: 'none', background: 'none', padding: '8px 12px', cursor: 'pointer', fontSize: 13.5, fontWeight: tab === t.key ? 700 : 500, color: tab === t.key ? 'var(--teal)' : 'var(--muted)', borderBottom: tab === t.key ? '2px solid var(--teal)' : '2px solid transparent' }}>{t.label}</button>
          ))}
        </div>
      )}

      {tab === 'info' && (
        <div className="card" style={{ padding: 18 }}>
          <div className="form-grid">
            <div className="form-row"><label>Mã / viết tắt</label><input value={sup.code || ''} disabled={!isNew} onChange={(e) => setH('code', e.target.value)} /></div>
            <div className="form-row"><label>Vai trò cung cấp</label>
              <select value={sup.supplier_type} onChange={(e) => setH('supplier_type', e.target.value)}>{SUP_TYPE.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}</select>
            </div>
            <div className="form-row" style={{ gridColumn: '1 / -1' }}><label>Tên pháp lý</label><input value={sup.name || ''} onChange={(e) => setH('name', e.target.value)} /></div>
            <div className="form-row"><label>Loại nhà cung cấp</label>
              <select value={sup.legal_type || ''} onChange={(e) => setH('legal_type', e.target.value)}>
                <option value="">— Chọn —</option>{LEGAL_TYPE.map((o) => <option key={o} value={o}>{o}</option>)}
              </select>
            </div>
            <div className="form-row"><label>Mã số thuế</label><input value={sup.tax_code || ''} onChange={(e) => setH('tax_code', e.target.value)} /></div>
            <div className="form-row"><label>Người liên hệ</label><input value={sup.contact_person || ''} onChange={(e) => setH('contact_person', e.target.value)} /></div>
            <div className="form-row"><label>Điện thoại</label><input value={sup.phone || ''} onChange={(e) => setH('phone', e.target.value)} /></div>
            <div className="form-row" style={{ gridColumn: '1 / -1' }}><label>Địa chỉ</label><textarea value={sup.address || ''} onChange={(e) => setH('address', e.target.value)} /></div>
            <div className="form-row"><label>Hình thức thanh toán</label><input value={sup.payment_terms || ''} placeholder="vd Công nợ 30 ngày" onChange={(e) => setH('payment_terms', e.target.value)} /></div>
            <div className="form-row"><label>VAT (vd 0.08)</label><input type="number" value={sup.vat ?? 0} onChange={(e) => setH('vat', Number(e.target.value))} /></div>
            <div className="form-row"><label>Số tài khoản</label><input value={sup.bank_account || ''} onChange={(e) => setH('bank_account', e.target.value)} /></div>
            <div className="form-row"><label>Ngân hàng</label><input value={sup.bank_name || ''} onChange={(e) => setH('bank_name', e.target.value)} /></div>
            <div className="form-row"><label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}><input type="checkbox" checked={!!sup.is_active} onChange={(e) => setH('is_active', e.target.checked)} style={{ width: 18, height: 18 }} /> Đang dùng</label></div>
          </div>
          {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}
          {msg && <div style={{ color: 'var(--green)', fontSize: 13, marginTop: 8 }}>{msg}</div>}
        </div>
      )}

      {tab === 'eval' && (
        <div className="grid-2">
          <div className="card" style={{ padding: 18 }}>
            <h3 className="sec-title">KPI giao hàng (cả kỳ)</h3>
            {kpi ? (
              <div style={{ fontSize: 14, lineHeight: 2 }}>
                <div>Số lần giao dịch: <b>{fmt(kpi.trans)}</b></div>
                <div>Số lần trễ: <b style={{ color: 'var(--red)' }}>{fmt(kpi.late)}</b></div>
                <div>Tỷ lệ trễ: <b style={{ color: kpi.rate > 30 ? 'var(--red)' : 'var(--ink)' }}>{fmt(kpi.rate)}%</b></div>
                {kpi.rate > 30 && <div style={{ color: 'var(--red)', fontSize: 13 }}>Cảnh báo: tỷ lệ trễ cao (&gt;30%)</div>}
              </div>
            ) : <span style={{ color: '#999' }}>Chưa có dữ liệu giao dịch.</span>}
          </div>
          <div className="card" style={{ padding: 18 }}>
            <h3 className="sec-title">Tổng quan công nợ</h3>
            <div style={{ fontSize: 14, lineHeight: 2 }}>
              <div>Tổng nợ: <b>{fmt(payTotal)}</b></div>
              <div>Đã trả: <b style={{ color: 'var(--green)' }}>{fmt(payPaid)}</b></div>
              <div>Còn phải trả: <b style={{ color: 'var(--teal)' }}>{fmt(payRemain)}</b></div>
              <div>Số hợp đồng: <b>{contracts.length}</b></div>
            </div>
          </div>
        </div>
      )}

      {tab === 'contracts' && (
        <div className="card" style={{ padding: 18 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
            <h3 className="sec-title" style={{ margin: 0, border: 'none', padding: 0 }}>Hợp đồng của NCC</h3>
            {can('contract', 'create') && <button className="btn ghost" onClick={() => navigate('/contracts/new')}><i className="ti ti-plus" />Thêm hợp đồng</button>}
          </div>
          <div className="items-scroll">
            <table className="items-table" style={{ minWidth: 700 }}>
              <thead><tr><th>Mã HĐ</th><th>Trích yếu</th><th>Loại</th><th>Công ty ký</th><th>Từ</th><th>Đến</th><th style={{ textAlign: 'center' }}>Đã ký</th><th>Hết hạn</th></tr></thead>
              <tbody>
                {contracts.map((c) => (
                  <tr key={c.id} className="clickable" onClick={() => navigate(`/contracts/${c.id}`)}>
                    <td>{c.code}</td><td>{c.title}</td><td>{c.contract_type}</td><td>{companyName(c.company_id)}</td>
                    <td>{c.start_date}</td><td>{c.end_date}</td>
                    <td style={{ textAlign: 'center' }}>{c.signed ? '✓' : ''}</td><td>{contractExpiryBadge(c.expiry)}</td>
                  </tr>
                ))}
                {contracts.length === 0 && <tr><td colSpan={8} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Chưa có hợp đồng</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {tab === 'payables' && (
        <div className="card" style={{ padding: 18 }}>
          <h3 className="sec-title">Công nợ (Tổng {fmt(payTotal)} · Còn lại {fmt(payRemain)})</h3>
          <div className="items-scroll">
            <table className="items-table" style={{ minWidth: 760 }}>
              <thead><tr><th>Loại</th><th>PO</th><th>Số HĐ</th><th>Ngày PS</th><th>Hạn trả</th><th style={{ textAlign: 'right' }}>Tổng</th><th style={{ textAlign: 'right' }}>Đã trả</th><th style={{ textAlign: 'right' }}>Còn lại</th><th>Trạng thái</th></tr></thead>
              <tbody>
                {payables.map((p) => (
                  <tr key={p.id}>
                    <td>{p.source_type === 'shipping' ? 'Vận chuyển' : 'Hàng hóa'}</td><td>{p.po_code}</td><td>{p.invoice_no}</td>
                    <td>{p.incur_date}</td><td>{p.due_date}</td>
                    <td style={{ textAlign: 'right' }}>{fmt(p.total)}</td><td style={{ textAlign: 'right' }}>{fmt(p.paid_amount)}</td>
                    <td style={{ textAlign: 'right', fontWeight: 600 }}>{fmt(p.remaining)}</td>
                    <td><span className={'badge ' + (p.status === 'Đã TT' ? 'ok' : 'err')}>{p.status}</span></td>
                  </tr>
                ))}
                {payables.length === 0 && <tr><td colSpan={9} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Chưa có công nợ</td></tr>}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  )
}
