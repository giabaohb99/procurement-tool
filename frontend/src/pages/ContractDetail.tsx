import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { contractExpiryBadge } from '../config/cruds'

const PARTY_TYPES = ['Nhà cung cấp', 'Khách hàng', 'Khác']
const C_TYPES = ['Mua bán', 'Nguyên tắc', 'Vận chuyển', 'Dịch vụ', 'Khác']
const C_STATUS = ['Hiệu lực', 'Hết hạn', 'Thanh lý']

export default function ContractDetail() {
  const { id } = useParams()
  const isNew = id === 'new'
  const { can } = useAuth()
  const navigate = useNavigate()
  const [c, setC] = useState<any>({ party_type: 'Nhà cung cấp', party_code: '', party_name: '', company_id: 0, title: '', contract_type: '', start_date: '', end_date: '', signed: false, status: 'Hiệu lực', note: '' })
  const [suppliers, setSuppliers] = useState<any[]>([])
  const [companies, setCompanies] = useState<any[]>([])
  const [files, setFiles] = useState<any[]>([])
  const [err, setErr] = useState(''); const [msg, setMsg] = useState('')

  useEffect(() => {
    api.get('/api/suppliers', { params: { page_size: 1000 } }).then((r) => setSuppliers(r.data.data.items))
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items))
    if (!isNew) loadAll()
  }, [id])

  async function loadAll() {
    const r = await api.get(`/api/contracts/${id}`); setC(r.data.data)
    api.get('/api/attachments', { params: { entity: 'contract', entity_id: id } }).then((x) => setFiles(x.data.data))
  }
  const setH = (k: string, v: any) => setC((s: any) => ({ ...s, [k]: v }))
  const onPickParty = (code: string) => {
    const s = suppliers.find((x) => x.code === code)
    setC((st: any) => ({ ...st, party_code: code, party_name: s ? s.name : st.party_name }))
  }

  async function save() {
    setErr(''); setMsg('')
    const body = { party_type: c.party_type, party_code: c.party_code, party_name: c.party_name, company_id: Number(c.company_id) || 0, title: c.title, contract_type: c.contract_type, start_date: c.start_date, end_date: c.end_date, signed: !!c.signed, status: c.status, note: c.note }
    try {
      if (isNew) { const r = await api.post('/api/contracts', body); navigate(`/contracts/${r.data.data.id}`) }
      else { await api.patch(`/api/contracts/${id}`, body); setMsg('Đã lưu'); loadAll() }
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi khi lưu') }
  }
  async function remove() {
    if (!confirm('Xóa hợp đồng này?')) return
    try { await api.delete(`/api/contracts/${id}`); navigate('/contracts') } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi') }
  }
  async function upload(fl: FileList | null) {
    if (!fl?.length) return
    const fd = new FormData(); fd.append('entity', 'contract'); fd.append('entity_id', String(id))
    Array.from(fl).forEach((f) => fd.append('files', f))
    try { await api.post('/api/attachments', fd); loadAll() } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi tải file') }
  }

  const isNCC = c.party_type === 'Nhà cung cấp'

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate('/contracts')}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>{isNew ? 'Thêm hợp đồng' : `Hợp đồng ${c.code || ''}`}</h2>
        {!isNew && contractExpiryBadge(c.expiry)}
        <span style={{ flex: 1 }} />
        {can('contract', isNew ? 'create' : 'write') && <button className="btn" onClick={save}>{isNew ? 'Tạo' : 'Lưu'}</button>}
        {!isNew && can('contract', 'delete') && <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={remove}><i className="ti ti-trash" />Xóa</button>}
      </div>

      <div className="card" style={{ padding: 18, marginBottom: 16 }}>
        <h3 className="sec-title">Thông tin hợp đồng</h3>
        <div className="form-grid">
          <div className="form-row"><label>Đối tượng *</label>
            <select value={c.party_type} onChange={(e) => setH('party_type', e.target.value)}>{PARTY_TYPES.map((o) => <option key={o} value={o}>{o}</option>)}</select>
          </div>
          {isNCC ? (
            <div className="form-row"><label>Nhà cung cấp *</label>
              <select value={c.party_code || ''} onChange={(e) => onPickParty(e.target.value)}>
                <option value="">— Chọn NCC —</option>{suppliers.map((s) => <option key={s.id} value={s.code}>{s.code} — {s.name}</option>)}
              </select>
            </div>
          ) : (
            <div className="form-row"><label>Tên đối tượng *</label><input value={c.party_name || ''} onChange={(e) => setH('party_name', e.target.value)} /></div>
          )}
          <div className="form-row"><label>Công ty (bên mình) ký *</label>
            <select value={c.company_id || ''} onChange={(e) => setH('company_id', Number(e.target.value))}>
              <option value="">— Chọn —</option>{companies.map((co) => <option key={co.id} value={co.id}>{co.name}</option>)}
            </select>
          </div>
          <div className="form-row"><label>Loại hợp đồng</label>
            <select value={c.contract_type || ''} onChange={(e) => setH('contract_type', e.target.value)}>
              <option value="">— Chọn —</option>{C_TYPES.map((o) => <option key={o} value={o}>{o}</option>)}
            </select>
          </div>
          <div className="form-row" style={{ gridColumn: '1 / -1' }}><label>Trích yếu hợp đồng</label><input value={c.title || ''} onChange={(e) => setH('title', e.target.value)} /></div>
          <div className="form-row"><label>Từ ngày</label><input type="date" value={c.start_date || ''} onChange={(e) => setH('start_date', e.target.value)} /></div>
          <div className="form-row"><label>Đến ngày</label><input type="date" value={c.end_date || ''} onChange={(e) => setH('end_date', e.target.value)} /></div>
          <div className="form-row"><label>Trạng thái</label>
            <select value={c.status} onChange={(e) => setH('status', e.target.value)}>{C_STATUS.map((o) => <option key={o} value={o}>{o}</option>)}</select>
          </div>
          <div className="form-row"><label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}><input type="checkbox" checked={!!c.signed} onChange={(e) => setH('signed', e.target.checked)} style={{ width: 18, height: 18 }} /> Đã ký</label></div>
          <div className="form-row" style={{ gridColumn: '1 / -1' }}><label>Ghi chú</label><textarea value={c.note || ''} onChange={(e) => setH('note', e.target.value)} /></div>
        </div>
        {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}
        {msg && <div style={{ color: 'var(--green)', fontSize: 13, marginTop: 8 }}>{msg}</div>}
      </div>

      <div className="card" style={{ padding: 18 }}>
        <h3 className="sec-title"><i className="ti ti-paperclip" /> Tệp hợp đồng đính kèm</h3>
        {isNew ? <span style={{ color: '#999', fontSize: 13 }}>Lưu hợp đồng trước rồi mới đính kèm file.</span> : (
          <>
            <input type="file" multiple onChange={(e) => upload(e.target.files)} />
            <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
              {files.map((f) => (
                <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                  <i className="ti ti-file" /><a href={f.url} target="_blank" style={{ color: 'var(--teal)', flex: 1, textDecoration: 'underline' }}>{f.filename}</a>
                  <button className="icon-btn" onClick={async () => { if (confirm('Xóa file?')) { await api.delete(`/api/attachments/${f.id}`); loadAll() } }}><i className="ti ti-trash" style={{ color: 'var(--red)' }} /></button>
                </div>
              ))}
              {files.length === 0 && <span style={{ color: '#999', fontSize: 13 }}>Chưa có file. Kéo/chọn file HĐ (PDF, ảnh…) để đính kèm.</span>}
            </div>
          </>
        )}
      </div>
    </div>
  )
}
