import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'

const API = '/api/payment-requests'
const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
const ST: Record<string, { label: string; cls: string }> = {
  draft: { label: 'Nháp', cls: 'gray' }, submitted: { label: 'Chờ duyệt', cls: 'warn' },
  approved: { label: 'Đã duyệt', cls: 'ok' }, paid: { label: 'Đã chi', cls: 'ok' },
}
const stBadge = (s: string) => { const x = ST[s] || { label: s, cls: 'gray' }; return <span className={'badge ' + x.cls}>{x.label}</span> }

export default function PaymentRequestDetail() {
  const { id } = useParams()
  const isNew = id === 'new'
  const { can } = useAuth()
  const navigate = useNavigate()
  const [req, setReq] = useState<any>(null)
  const [companies, setCompanies] = useState<any[]>([])
  const [files, setFiles] = useState<any[]>([])
  const [err, setErr] = useState(''); const [msg, setMsg] = useState('')

  async function loadAll() {
    const r = await api.get(`${API}/${id}`); setReq(r.data.data)
    api.get('/api/attachments', { params: { entity: 'payment_request', entity_id: id } }).then((x) => setFiles(x.data.data))
  }
  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items))
    if (!isNew) loadAll()
  }, [id])

  if (isNew) return (
    <div style={{ padding: 20 }}>
      <h2 className="page-title">Tạo yêu cầu thanh toán</h2>
      <div className="card" style={{ padding: 20 }}>
        Phiếu yêu cầu thanh toán được tạo từ màn <b>Công nợ</b>: chọn các khoản nợ (cùng/khác NCC) rồi bấm
        <i> "Tạo yêu cầu thanh toán"</i> — hệ thống tự tách mỗi nhà cung cấp 1 phiếu.
        <div style={{ marginTop: 14 }}><button className="btn" onClick={() => navigate('/payables')}><i className="ti ti-cash" />Tới màn Công nợ</button></div>
      </div>
    </div>
  )
  if (!req) return <div style={{ padding: 40 }}>Đang tải...</div>

  const editable = req.status === 'draft' && can('payment_request', 'write')
  const companyName = companies.find((c) => c.id === req.company_id)?.name || '—'
  const setLineAmount = (i: number, v: number) =>
    setReq((s: any) => ({ ...s, lines: s.lines.map((l: any, idx: number) => idx === i ? { ...l, amount: v } : l) }))

  async function save() {
    setErr(''); setMsg('')
    try {
      await api.patch(`${API}/${id}`, { request_date: req.request_date, note: req.note, lines: req.lines.map((l: any) => ({ payable_id: l.payable_id, amount: Number(l.amount) || 0 })) })
      setMsg('Đã lưu'); loadAll()
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi khi lưu') }
  }
  async function action(path: string) {
    setErr('')
    try { await api.post(`${API}/${id}/${path}`); loadAll() } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi') }
  }
  async function uploadFiles(fl: FileList | null) {
    if (!fl?.length) return
    const fd = new FormData(); fd.append('entity', 'payment_request'); fd.append('entity_id', String(id))
    Array.from(fl).forEach((f) => fd.append('files', f))
    await api.post('/api/attachments', fd); loadAll()
  }

  const total = req.lines.reduce((s: number, l: any) => s + (Number(l.amount) || 0), 0)

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate('/payment-requests')}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>Yêu cầu thanh toán {req.code}</h2>
        {stBadge(req.status)}
        <span style={{ flex: 1 }} />
        {can('payment_request', 'print') && <button className="btn ghost" onClick={() => window.open(`/print/payment-request/${id}`, '_blank')}><i className="ti ti-printer" />In phiếu</button>}
        {editable && can('payment_request', 'write') && <button className="btn" onClick={save}>Lưu</button>}
        {req.status === 'draft' && can('payment_request', 'write') && <button className="btn secondary" onClick={() => action('submit')}><i className="ti ti-send" />Gửi duyệt</button>}
        {req.status === 'submitted' && can('payment_request', 'approve') && <button className="btn" onClick={() => action('approve')}><i className="ti ti-check" />Duyệt</button>}
        {req.status === 'approved' && can('payment_request', 'write') && <button className="btn" onClick={() => { if (confirm('Xác nhận đã chi tiền? Công nợ sẽ được trừ tương ứng.')) action('pay') }}><i className="ti ti-cash" />Ghi nhận đã chi</button>}
      </div>

      <div className="card" style={{ padding: 18, marginBottom: 16 }}>
        <h3 className="sec-title">Thông tin phiếu</h3>
        <div className="form-grid">
          <div className="form-row"><label>Nhà cung cấp</label><input value={req.supplier_name || req.supplier_code} disabled /></div>
          <div className="form-row"><label>Loại công nợ</label><input value={req.source_type === 'shipping' ? 'Vận chuyển' : 'Hàng hóa'} disabled /></div>
          <div className="form-row"><label>Công ty</label><input value={companyName} disabled /></div>
          <div className="form-row"><label>Ngày lập</label><input type="date" value={req.request_date || ''} disabled={!editable} onChange={(e) => setReq((s: any) => ({ ...s, request_date: e.target.value }))} /></div>
          <div className="form-row" style={{ gridColumn: '1 / -1' }}><label>Ghi chú</label><textarea value={req.note || ''} disabled={!editable} onChange={(e) => setReq((s: any) => ({ ...s, note: e.target.value }))} /></div>
        </div>
      </div>

      <div className="card" style={{ padding: 18, marginBottom: 16 }}>
        <h3 className="sec-title">Các khoản công nợ thanh toán</h3>
        <div className="items-scroll">
          <table className="items-table" style={{ minWidth: 800 }}>
            <thead><tr><th>#</th><th>PO</th><th>Số HĐ</th><th>Ngày PS</th><th>Hạn trả</th><th style={{ textAlign: 'right' }}>Tổng nợ</th><th style={{ textAlign: 'right' }}>Đã trả</th><th style={{ textAlign: 'right' }}>Đề nghị trả</th></tr></thead>
            <tbody>
              {req.lines.map((l: any, i: number) => (
                <tr key={i}>
                  <td>{i + 1}</td><td>{l.po_code}</td><td>{l.invoice_no}</td><td>{l.incur_date}</td><td>{l.due_date}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(l.payable_total)}</td>
                  <td style={{ textAlign: 'right' }}>{fmt(l.payable_paid)}</td>
                  <td style={{ textAlign: 'right' }}>
                    {editable ? <input className="cell-input" type="number" style={{ width: 120, textAlign: 'right' }} value={l.amount} onChange={(e) => setLineAmount(i, Number(e.target.value))} /> : fmt(l.amount)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div style={{ textAlign: 'right', fontSize: 16, color: 'var(--navy)', marginTop: 12 }}>Tổng đề nghị thanh toán: <b>{fmt(total)}</b></div>
      </div>

      <div className="card" style={{ padding: 18, marginBottom: 16 }}>
        <h3 className="sec-title"><i className="ti ti-paperclip" /> Chứng từ thanh toán (ủy nhiệm chi…)</h3>
        {can('payment_request', 'write') && <input type="file" multiple onChange={(e) => uploadFiles(e.target.files)} />}
        <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
          {files.map((f) => (
            <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
              <i className="ti ti-file" /><a href={f.url} target="_blank" style={{ color: 'var(--teal)', flex: 1, textDecoration: 'underline' }}>{f.filename}</a>
              {can('payment_request', 'write') && <button className="icon-btn" onClick={async () => { if (confirm('Xóa file?')) { await api.delete(`/api/attachments/${f.id}`); loadAll() } }}><i className="ti ti-trash" style={{ color: 'var(--red)' }} /></button>}
            </div>
          ))}
          {files.length === 0 && <span style={{ color: '#999', fontSize: 13 }}>Chưa có file nào.</span>}
        </div>
      </div>

      {err && <div className="err">{err}</div>}
      {msg && <div style={{ color: 'var(--green)', fontSize: 13 }}>{msg}</div>}

      {editable && can('payment_request', 'delete') && (
        <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)', marginTop: 16 }}
                onClick={async () => { if (confirm('Xóa phiếu này?')) { await api.delete(`${API}/${id}`); navigate('/payment-requests') } }}><i className="ti ti-trash" /> Xóa phiếu</button>
      )}
    </div>
  )
}
