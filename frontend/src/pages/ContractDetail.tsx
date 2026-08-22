import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { askConfirm } from '../components/confirm'
import { useAuth } from '../auth/AuthContext'
import { contractExpiryBadge } from '../config/cruds'
import { CONTRACT_TYPES } from '../utils/contractTypes'
import { CONTRACT_PARTY_TYPES, CONTRACT_STATUSES } from '../utils/contractStatus'
import SearchSelect from '../components/SearchSelect'
import DateRangePicker from '../components/DateRangePicker'
import DocumentAttachmentSection from '../components/DocumentAttachmentSection'

// B-02: hai ô này lưu MÃ, hiện nhãn tiếng Việt — gửi chữ tiếng Việt lên backend trả 422.
const PARTY_TYPES = CONTRACT_PARTY_TYPES
const C_STATUS = CONTRACT_STATUSES

export default function ContractDetail() {
  const { id } = useParams()
  const isNew = id === 'new'
  const { can } = useAuth()
  const navigate = useNavigate()
  const [c, setC] = useState<any>({ party_type: 'supplier', party_code: '', party_name: '', company_id: 0, title: '', contract_type: '', start_date: '', end_date: '', signed: false, status: 'active', note: '' })
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
  const canEdit = can('contract', isNew ? 'create' : 'write')
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
    if (!(await askConfirm({ message: 'Xóa hợp đồng này?' }))) return
    try { await api.delete(`/api/contracts/${id}`); navigate('/contracts') } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi') }
  }
  async function upload(fl: FileList | null) {
    if (!fl?.length) return
    const fd = new FormData(); fd.append('entity', 'contract'); fd.append('entity_id', String(id))
    Array.from(fl).forEach((f) => fd.append('files', f))
    try { await api.post('/api/attachments', fd); loadAll() } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi tải file') }
  }

  const isNCC = c.party_type === 'supplier'

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
            <SearchSelect value={c.party_type} options={PARTY_TYPES} disabled={!canEdit} placeholder="Chọn…" onChange={(v) => setH('party_type', v)} />
          </div>
          {isNCC ? (
            <div className="form-row"><label>Nhà cung cấp *</label>
              <SearchSelect value={c.party_code || ''} disabled={!canEdit} placeholder="Chọn/tìm NCC…"
                options={suppliers.map((s) => ({ value: s.code, label: `${s.code} — ${s.name}` }))}
                onChange={(v) => onPickParty(v)} />
            </div>
          ) : (
            <div className="form-row"><label>Tên đối tượng *</label><input value={c.party_name || ''} disabled={!canEdit} onChange={(e) => setH('party_name', e.target.value)} /></div>
          )}
          <div className="form-row"><label>Công ty (bên mình) ký *</label>
            <SearchSelect value={c.company_id ? String(c.company_id) : ''} disabled={!canEdit} placeholder="Chọn/tìm công ty…"
              options={companies.map((co) => ({ value: String(co.id), label: co.name }))}
              onChange={(v) => setH('company_id', Number(v) || 0)} />
          </div>
          <div className="form-row"><label>Loại hợp đồng</label>
            {/* Lưu MÃ (`purchase`…), hiện nhãn tiếng Việt — CR-118. Gửi giá trị ngoài bộ này backend trả 422. */}
            <SearchSelect value={c.contract_type || ''} options={CONTRACT_TYPES} disabled={!canEdit} placeholder="Chọn…" onChange={(v) => setH('contract_type', v)} />
          </div>
          <div className="form-row" style={{ gridColumn: '1 / -1' }}><label>Trích yếu hợp đồng</label><input value={c.title || ''} disabled={!canEdit} onChange={(e) => setH('title', e.target.value)} /></div>
          {/* Hiệu lực hợp đồng = 1 khoảng ngày → dùng chung bộ chọn khoảng (không có nút nhanh vì là kỳ hạn tương lai) */}
          <div className="form-row" style={{ gridColumn: 'span 2' }}><label>Hiệu lực hợp đồng (từ → đến)</label>
            <DateRangePicker block presets={false} disabled={!canEdit}
              placeholder="Chọn ngày hiệu lực → hết hạn"
              endYear={new Date().getFullYear() + 10}
              value={{ from: c.start_date || '', to: c.end_date || '' }}
              onChange={(v) => setC((s: any) => ({ ...s, start_date: v.from, end_date: v.to }))} />
          </div>
          <div className="form-row"><label>Trạng thái</label>
            <SearchSelect value={c.status} options={C_STATUS} disabled={!canEdit} placeholder="Chọn…" onChange={(v) => setH('status', v)} />
          </div>
          <div className="form-row"><label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer' }}><input type="checkbox" checked={!!c.signed} disabled={!canEdit} onChange={(e) => setH('signed', e.target.checked)} style={{ width: 18, height: 18 }} /> Đã ký</label></div>
          <div className="form-row" style={{ gridColumn: '1 / -1' }}><label>Ghi chú</label><textarea value={c.note || ''} disabled={!canEdit} onChange={(e) => setH('note', e.target.value)} /></div>
        </div>
        {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}
        {msg && <div style={{ color: 'var(--green)', fontSize: 13, marginTop: 8 }}>{msg}</div>}
      </div>

      <DocumentAttachmentSection
        entity="contract"
        entityId={Number(id)}
        files={files}
        editable={canEdit}
        isNew={isNew}
        title="Tệp hợp đồng & phụ lục đính kèm"
        onRefresh={loadAll}
      />
    </div>
  )
}
