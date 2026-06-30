import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { prBadge } from '../config/cruds'

const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
const GROUPS = ['Bao bì', 'Nguyên liệu', 'In ấn', 'Chai lọ', 'Hóa chất']

type Col = { key: string; label: string; w: number; type?: string; options?: string[] }

const SUPPLIER_COLS: Col[] = [
  { key: 'contact_date', label: 'Ngày LH', w: 110, type: 'date' },
  { key: 'reply_date', label: 'NCC phản hồi', w: 120, type: 'date' },
  { key: 'result_date', label: 'Ngày trả KQ', w: 120, type: 'date' },
  { key: 'supplier_code', label: 'NCC (viết tắt) *', w: 140, type: 'supplier' },
  { key: 'supplier_name', label: 'Tên pháp lý', w: 220 },
  { key: 'tax_code', label: 'MST', w: 110 },
  { key: 'reg_address', label: 'Địa chỉ ĐKKD', w: 200 },
  { key: 'warehouse_address', label: 'Địa chỉ kho', w: 200 },
  { key: 'google_maps', label: 'Google Maps', w: 160 },
  { key: 'contact_person', label: 'Người LH (NVKD)', w: 140 },
  { key: 'contact_phone', label: 'SĐT', w: 110 },
  { key: 'supply_group', label: 'Nhóm SP cung ứng', w: 160 },
  { key: 'quote_folder', label: 'Folder báo giá', w: 160 },
  { key: 'production_tech', label: 'Công nghệ SX', w: 150 },
  { key: 'production_time', label: 'Thời gian SX', w: 120 },
  { key: 'nvkd_eval', label: 'Đánh giá NVKD', w: 130 },
  { key: 'invoice_policy', label: 'Chính sách hóa đơn', w: 170 },
  { key: 'reliability', label: 'Mức tin cậy', w: 130, type: 'select', options: ['', 'Cao', 'Trung bình', 'Thấp'] },
  { key: 'delivery_policy', label: 'Chính sách giao nhận', w: 170 },
  { key: 'debt_policy', label: 'Chính sách công nợ', w: 160, type: 'select', options: ['', 'Tiền mặt', 'Công nợ 30 ngày', 'Công nợ 60 ngày', 'Công nợ 90 ngày', 'Trả trước'] },
  { key: 'defect_return', label: 'Hàng lỗi/trả', w: 150 },
  { key: 'nspt_note', label: 'Nhận xét NSPT', w: 130, type: 'select', options: ['', 'Đạt', 'Không đạt'] },
  { key: 'nspt_reason', label: 'Lý do', w: 160 },
  { key: 'line_approve', label: 'Duyệt (TP/QL)', w: 130, type: 'select', options: ['', 'Duyệt', 'Không duyệt'] },
  { key: 'line_approve_note', label: 'Ghi chú duyệt', w: 180 },
]

const PRODUCT_COLS: Col[] = [
  { key: 'supplier_code', label: 'NCC *', w: 140, type: 'supplier' },
  { key: 'internal_code', label: 'Mã nội bộ', w: 120 },
  { key: 'product_name', label: 'Tên SP theo NCC *', w: 220 },
  { key: 'spec', label: 'Thông số KT', w: 180 },
  { key: 'origin', label: 'Xuất xứ', w: 100 },
  { key: 'quote_unit', label: 'ĐVT báo giá', w: 120, type: 'unit' },
  { key: 'moq', label: 'MOQ', w: 90, type: 'num' },
  { key: 'price_by_volume', label: 'Giá theo khung', w: 120, type: 'num' },
  { key: 'volume_range', label: 'Khung SL', w: 110 },
  { key: 'vat', label: 'VAT(%)', w: 90, type: 'select', options: ['0', '2', '4', '6', '8', '10'] },
  { key: 'request_qty', label: 'SL YC', w: 90, type: 'num' },
  { key: 'amount', label: 'Thành tiền', w: 120, type: 'computed' },
  { key: 'internal_unit', label: 'ĐVT quy đổi', w: 120, type: 'unit' },
  { key: 'amount_converted', label: 'TT quy đổi', w: 120, type: 'num' },
  { key: 'shipping_cost', label: 'Phí VC', w: 100, type: 'num' },
  { key: 'delivery_time', label: 'TG giao', w: 110 },
  { key: 'delivery_place', label: 'Nơi giao nhận', w: 150 },
  { key: 'quote_file', label: 'File báo giá', w: 150 },
  { key: 'sample_ready', label: 'Mẫu sẵn', w: 80, type: 'check' },
  { key: 'sample_date', label: 'Ngày mẫu', w: 120, type: 'date' },
  { key: 'sample_qty', label: 'SL mẫu', w: 90, type: 'num' },
  { key: 'lab_result', label: 'KQ LAB', w: 120, type: 'select', options: ['', 'Đạt', 'Không đạt'] },
  { key: 'lab_note', label: 'Ghi chú LAB', w: 150 },
  { key: 'nspt_note', label: 'Nhận xét NSPT', w: 140, type: 'select', options: ['', 'Đạt', 'Không đạt'] },
  { key: 'nspt_reason', label: 'Lý do NSPT', w: 160 },
  { key: 'line_approve', label: 'Duyệt (TP/QL)', w: 130, type: 'select', options: ['', 'Duyệt', 'Không duyệt'] },
  { key: 'line_approve_note', label: 'Ghi chú duyệt', w: 180 },
]

export default function SurveyDetail({ type }: { type: 'supplier' | 'product' }) {
  const { id } = useParams()
  const isNew = id === 'new'
  const { can } = useAuth()
  const navigate = useNavigate()
  const slug = `surveys-${type}`
  const API = `/api/${slug}`
  const cols = type === 'supplier' ? SUPPLIER_COLS : PRODUCT_COLS
  
  // Identify core columns to show directly on the main table
  const coreKeys = type === 'supplier'
    ? ['contact_date', 'supplier_code', 'supplier_name', 'contact_person', 'contact_phone', 'nspt_note', 'line_approve']
    : ['supplier_code', 'product_name', 'quote_unit', 'moq', 'price_by_volume', 'request_qty', 'amount', 'lab_result', 'line_approve']
    
  const tableCols = cols.filter(c => coreKeys.includes(c.key))
  const drawerCols = cols.filter(c => !coreKeys.includes(c.key))

  const emptyLine = Object.fromEntries(cols.map((c) => [c.key, c.type === 'check' ? false : (c.type === 'num' || c.type === 'computed') ? 0 : '']))

  const [sv, setSv] = useState<any>({
    pr_code: '', received_date: new Date().toISOString().slice(0, 10), result_due_date: '',
    item_group: '', requirement_detail: '', request_qty: 0, market_price: 0, nspt: '',
    status: 'draft', approve_note: '', lines: [],
  })
  const [suppliers, setSuppliers] = useState<any[]>([])
  const [units, setUnits] = useState<string[]>([])
  const [prList, setPrList] = useState<any[]>([])
  const [logs, setLogs] = useState<any[]>([])
  const [files, setFiles] = useState<any[]>([])
  const [err, setErr] = useState(''); const [msg, setMsg] = useState('')
  
  // UX upgrade states
  const [editingIndex, setEditingIndex] = useState<number | null>(null)
  const [selectedIdxs, setSelectedIdxs] = useState<number[]>([])

  useEffect(() => {
    api.get('/api/suppliers', { params: { page_size: 1000 } }).then((r) => setSuppliers(r.data.data.items))
    api.get('/api/units', { params: { page_size: 200 } }).then((r) => setUnits(r.data.data.items.map((x: any) => x.name)))
    api.get('/api/purchase-requests', { params: { page_size: 1000 } }).then((r) => setPrList(r.data.data.items))
  }, [])

  // Khi chọn mã PYC -> tự điền các trường header từ yêu cầu mua đó
  const onPickPr = (code: string) => {
    const pr = prList.find((p) => p.code === code)
    setSv((s: any) => ({
      ...s,
      pr_code: code,
      ...(pr ? {
        requirement_detail: pr.purpose || s.requirement_detail,
        result_due_date: pr.need_date || s.result_due_date,
        nspt: pr.requester || s.nspt,
      } : {}),
    }))
  }

  async function loadAll() {
    const r = await api.get(`${API}/${id}`); setSv(r.data.data)
    api.get('/api/audit-logs', { params: { entity: 'survey', entity_id: id } }).then((x) => setLogs(x.data.data))
    api.get('/api/attachments', { params: { entity: 'survey', entity_id: id } }).then((x) => setFiles(x.data.data))
  }

  useEffect(() => { if (!isNew) loadAll() }, [id, type])

  const editable = isNew || sv.status === 'draft' || sv.status === 'rejected'
  const setH = (k: string, v: any) => setSv((s: any) => ({ ...s, [k]: v }))
  const lines = sv.lines || []
  const setLine = (i: number, patch: any) => setSv((s: any) => ({ ...s, lines: s.lines.map((it: any, idx: number) => idx === i ? { ...it, ...patch } : it) }))
  const addLines = (n = 1) => setSv((s: any) => ({ ...s, lines: [...(s.lines || []), ...Array.from({ length: n }, () => ({ ...emptyLine }))] }))
  const delLine = (i: number) => {
    setSv((s: any) => ({ ...s, lines: s.lines.filter((_: any, idx: number) => idx !== i) }))
    setSelectedIdxs(s => s.filter(idx => idx !== i).map(idx => idx > i ? idx - 1 : idx))
    if (editingIndex === i) setEditingIndex(null)
    else if (editingIndex !== null && editingIndex > i) setEditingIndex(editingIndex - 1)
  }

  const rowAmount = (it: any) => (Number(it.request_qty) || 0) * (Number(it.price_by_volume) || 0) * (1 + (Number(it.vat) || 0) / 100)
  const subtotal = type === 'product' ? lines.reduce((s: number, it: any) => s + rowAmount(it), 0) : 0

  const duplicateLine = (i: number) => {
    const cloned = { ...lines[i] }
    setSv((s: any) => ({ ...s, lines: [...s.lines, cloned] }))
  }

  const toggleSelect = (i: number) => {
    setSelectedIdxs(s => s.includes(i) ? s.filter(idx => idx !== i) : [...s, i])
  }

  const toggleSelectAll = () => {
    if (selectedIdxs.length === lines.length) setSelectedIdxs([])
    else setSelectedIdxs(lines.map((_, i) => i))
  }

  const deleteSelected = () => {
    if (confirm('Xóa các dòng đã chọn?')) {
      setSv((s: any) => ({
        ...s,
        lines: s.lines.filter((_: any, idx: number) => !selectedIdxs.includes(idx))
      }))
      setSelectedIdxs([])
      setEditingIndex(null)
    }
  }

  async function save() {
    setErr(''); setMsg('')
    const body: any = {
      pr_code: sv.pr_code, received_date: sv.received_date, result_due_date: sv.result_due_date,
      item_group: sv.item_group, requirement_detail: sv.requirement_detail,
      request_qty: Number(sv.request_qty) || 0, market_price: Number(sv.market_price) || 0, nspt: sv.nspt,
      lines: lines.filter((it: any) => type === 'supplier' ? it.supplier_code : it.product_name),
    }
    try {
      if (isNew) { const r = await api.post(API, body); navigate(`/${slug}/${r.data.data.id}`) }
      else { await api.patch(`${API}/${id}`, body); setMsg('Đã lưu thành công'); loadAll() }
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi khi lưu') }
  }

  async function action(path: string, payload: any = {}) {
    setErr('')
    try { await api.post(`${API}/${id}/${path}`, payload); loadAll() }
    catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi') }
  }

  async function uploadFiles(fl: FileList | null) {
    if (!fl?.length) return
    const fd = new FormData(); fd.append('entity', 'survey'); fd.append('entity_id', String(id))
    Array.from(fl).forEach((f) => fd.append('files', f))
    try { await api.post('/api/attachments', fd); loadAll() } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi tải file') }
  }

  function cell(col: Col, i: number) {
    const it = lines[i]
    if (!editable) {
      if (col.type === 'computed') return fmt(rowAmount(it))
      if (col.type === 'check') return it[col.key] ? '✓' : ''
      return it[col.key] ?? ''
    }
    if (col.type === 'computed') return <span style={{ fontWeight: 500 }}>{fmt(rowAmount(it))}</span>
    if (col.type === 'check') return <input type="checkbox" checked={!!it[col.key]} onChange={(e) => setLine(i, { [col.key]: e.target.checked })} />
    if (col.type === 'num') return <input className="cell-input" type="number" style={{ width: col.w }} value={it[col.key] ?? 0} onChange={(e) => setLine(i, { [col.key]: Number(e.target.value) })} />
    if (col.type === 'date') return <input className="cell-input" type="date" style={{ width: col.w }} value={it[col.key] ?? ''} onChange={(e) => setLine(i, { [col.key]: e.target.value })} />
    if (col.type === 'select') return (
      <select className="cell-input" style={{ width: col.w }} value={it[col.key] ?? ''} onChange={(e) => setLine(i, { [col.key]: col.key === 'vat' ? Number(e.target.value) : e.target.value })}>
        {col.options!.map((o) => <option key={o} value={o}>{o || '—'}</option>)}
      </select>
    )
    if (col.type === 'unit') return (
      <select className="cell-input" style={{ width: col.w }} value={it[col.key] ?? ''} onChange={(e) => setLine(i, { [col.key]: e.target.value })}>
        <option value="">—</option>{units.map((u) => <option key={u} value={u}>{u}</option>)}
      </select>
    )
    if (col.type === 'supplier') return (
      <select className="cell-input" style={{ width: col.w }} value={it[col.key] ?? ''} onChange={(e) => {
        const sup = suppliers.find((s) => s.code === e.target.value)
        setLine(i, sup ? { supplier_code: sup.code, supplier_name: sup.name, tax_code: sup.tax_code, reg_address: sup.address } : { supplier_code: e.target.value })
      }}>
        <option value="">—</option>{suppliers.map((s) => <option key={s.id} value={s.code}>{s.code}</option>)}
      </select>
    )
    return <input className="cell-input" style={{ width: col.w }} value={it[col.key] ?? ''} onChange={(e) => setLine(i, { [col.key]: e.target.value })} />
  }

  function drawerField(col: Col, i: number) {
    const it = lines[i]
    const label = col.label
    const k = col.key
    return (
      <div className="form-row" key={k} style={{ marginBottom: 12 }}>
        <label style={{ fontWeight: 600, fontSize: 13, color: 'var(--muted)', display: 'block', marginBottom: 4 }}>{label}</label>
        {(!editable || col.type === 'computed') ? (
          <div style={{ padding: '6px 8px', fontSize: 13.5, background: '#f8fafc', borderRadius: 6, border: '1px solid #e2e8f0', color: 'var(--ink)' }}>
            {col.type === 'computed' ? fmt(rowAmount(it)) : String(it[k] ?? '—')}
          </div>
        ) : col.type === 'check' ? (
          <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', padding: '6px 0' }}>
            <input type="checkbox" checked={!!it[k]} onChange={(e) => setLine(i, { [k]: e.target.checked })} style={{ width: 18, height: 18 }} />
            {label}
          </label>
        ) : col.type === 'num' ? (
          <input type="number" className="cell-input" style={{ width: '100%', height: 36 }} value={it[k] ?? 0} onChange={(e) => setLine(i, { [k]: Number(e.target.value) })} />
        ) : col.type === 'date' ? (
          <input type="date" className="cell-input" style={{ width: '100%', height: 36 }} value={it[k] ?? ''} onChange={(e) => setLine(i, { [k]: e.target.value })} />
        ) : col.type === 'select' ? (
          <select className="cell-input" style={{ width: '100%', height: 36 }} value={it[k] ?? ''} onChange={(e) => setLine(i, { [k]: k === 'vat' ? Number(e.target.value) : e.target.value })}>
            {col.options!.map((o) => <option key={o} value={o}>{o || '—'}</option>)}
          </select>
        ) : col.type === 'unit' ? (
          <select className="cell-input" style={{ width: '100%', height: 36 }} value={it[k] ?? ''} onChange={(e) => setLine(i, { [k]: e.target.value })}>
            <option value="">—</option>
            {units.map((u) => <option key={u} value={u}>{u}</option>)}
          </select>
        ) : (
          <input className="cell-input" style={{ width: '100%', height: 36 }} value={it[k] ?? ''} onChange={(e) => setLine(i, { [k]: e.target.value })} />
        )}
      </div>
    )
  }

  const title = type === 'supplier' ? 'Khảo sát Nhà cung cấp' : 'Khảo sát Sản phẩm'
  const isLogShown = !isNew && logs.length > 0;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate(`/${slug}`)}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>{isNew ? `Tạo ${title}` : `${title} ${sv.code || ''}`}</h2>
        {!isNew && prBadge(sv.status)}
        <span style={{ flex: 1 }} />
        {editable && can('survey', isNew ? 'create' : 'write') && <button className="btn" onClick={save}>{isNew ? 'Tạo' : 'Lưu'}</button>}
        {!isNew && editable && can('survey', 'write') && <button className="btn secondary" onClick={() => action('submit')}><i className="ti ti-send" />Gửi duyệt</button>}
        {!isNew && sv.status === 'submitted' && can('survey', 'approve') && (
          <>
            <button className="btn" onClick={() => action('approve')}><i className="ti ti-check" />Duyệt</button>
            <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={() => action('reject', { reason: prompt('Lý do từ chối:') || '' })}><i className="ti ti-x" />Từ chối</button>
          </>
        )}
      </div>

      <div className={isLogShown ? "detail-grid" : ""}>
        <div>
          {/* Thông tin tiếp nhận */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <h3 className="sec-title">Thông tin tiếp nhận</h3>
            <div className="form-grid">
              <div className="form-row"><label>Mã yêu cầu (PYC) *</label>
                <input list="pyc-list" placeholder="Nhập/chọn mã PYC để tự điền…" value={sv.pr_code} disabled={!editable} onChange={(e) => onPickPr(e.target.value)} />
                <datalist id="pyc-list">{prList.map((p) => <option key={p.id} value={p.code}>{p.purpose || ''}</option>)}</datalist>
              </div>
              <div className="form-row"><label>Ngày tiếp nhận</label><input type="date" value={sv.received_date || ''} disabled={!editable} onChange={(e) => setH('received_date', e.target.value)} /></div>
              <div className="form-row"><label>Ngày YC trả KQ</label><input type="date" value={sv.result_due_date || ''} disabled={!editable} onChange={(e) => setH('result_due_date', e.target.value)} /></div>
              <div className="form-row"><label>Nhóm hàng</label>
                <select value={sv.item_group || ''} disabled={!editable} onChange={(e) => setH('item_group', e.target.value)}>
                  <option value="">—</option>{GROUPS.map((g) => <option key={g} value={g}>{g}</option>)}
                </select>
              </div>
              <div className="form-row"><label>NSPT phụ trách</label><input value={sv.nspt || ''} disabled={!editable} onChange={(e) => setH('nspt', e.target.value)} /></div>
              <div className="form-row"><label>Số lượng YC</label><input type="number" value={sv.request_qty || 0} disabled={!editable} onChange={(e) => setH('request_qty', Number(e.target.value))} /></div>
              <div className="form-row"><label>Giá thị trường</label><input type="number" value={sv.market_price || 0} disabled={!editable} onChange={(e) => setH('market_price', Number(e.target.value))} /></div>
              <div className="form-row" style={{ gridColumn: '1 / -1' }}><label>Yêu cầu chi tiết</label><textarea value={sv.requirement_detail || ''} disabled={!editable} onChange={(e) => setH('requirement_detail', e.target.value)} /></div>
            </div>
          </div>

          {/* Bảng khảo sát */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 10 }}>
              <h3 className="sec-title" style={{ margin: 0, border: 'none', padding: 0 }}>{type === 'supplier' ? 'Bảng khảo sát NCC' : 'Bảng khảo sát Sản phẩm'}</h3>
              <div style={{ display: 'flex', gap: 8 }}>
                {editable && selectedIdxs.length > 0 && (
                  <button className="btn secondary" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={deleteSelected}>
                    <i className="ti ti-trash" /> Xóa các dòng đã chọn ({selectedIdxs.length})
                  </button>
                )}
                {editable && (
                  <>
                    <button className="btn ghost" onClick={() => addLines(1)} style={{ height: 32, fontSize: 13 }}><i className="ti ti-plus" />Thêm dòng</button>
                    <button className="btn ghost" onClick={() => addLines(Math.max(1, parseInt(prompt('Thêm bao nhiêu dòng?', '3') || '0') || 0))} style={{ height: 32, fontSize: 13 }}><i className="ti ti-rows" />Thêm nhiều</button>
                  </>
                )}
              </div>
            </div>

            <div className="items-scroll">
              <table className="items-table">
                <thead>
                  <tr>
                    {editable && <th style={{ width: 36, textAlign: 'center' }}><input type="checkbox" checked={lines.length > 0 && selectedIdxs.length === lines.length} onChange={toggleSelectAll} /></th>}
                    <th style={{ width: 36 }}>#</th>
                    {tableCols.map((c) => <th key={c.key} style={{ width: c.w }}>{c.label}</th>)}
                    <th style={{ width: 100, textAlign: 'center' }}>Hành động</th>
                  </tr>
                </thead>
                <tbody>
                  {lines.map((_: any, i: number) => (
                    <tr key={i} style={selectedIdxs.includes(i) ? { background: '#f0f9ff' } : {}}>
                      {editable && (
                        <td style={{ textAlign: 'center' }}>
                          <input type="checkbox" checked={selectedIdxs.includes(i)} onChange={() => toggleSelect(i)} />
                        </td>
                      )}
                      <td>{i + 1}</td>
                      {tableCols.map((c) => <td key={c.key}>{cell(c, i)}</td>)}
                      <td style={{ textAlign: 'center' }}>
                        <div style={{ display: 'inline-flex', gap: 6 }}>
                          <button className="icon-btn" title="Chỉnh sửa chi tiết" onClick={() => setEditingIndex(i)}>
                            <i className="ti ti-edit" style={{ fontSize: 16, color: 'var(--teal)' }} />
                          </button>
                          <button className="icon-btn" title="Nhân bản dòng" onClick={() => duplicateLine(i)}>
                            <i className="ti ti-copy" style={{ fontSize: 16, color: 'var(--muted)' }} />
                          </button>
                          {editable && (
                            <button className="icon-btn" title="Xóa dòng" onClick={() => { if (confirm('Xóa dòng này?')) delLine(i) }}>
                              <i className="ti ti-trash" style={{ fontSize: 16, color: 'var(--red)' }} />
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                  {lines.length === 0 && <tr><td colSpan={tableCols.length + (editable ? 3 : 2)} style={{ textAlign: 'center', color: '#999', padding: 14 }}>Chưa có dòng nào</td></tr>}
                </tbody>
              </table>
            </div>

            {type === 'product' && <div style={{ marginTop: 12, textAlign: 'right', fontSize: 15, color: 'var(--navy)' }}>Tổng thành tiền: <b>{fmt(subtotal)}</b></div>}
          </div>

          {sv.approve_note && <div className="card" style={{ padding: 14, marginBottom: 16 }}><b>Ghi chú duyệt:</b> {sv.approve_note}</div>}

          {!isNew && (
            <div className="card" style={{ padding: 18, marginBottom: 16 }}>
              <h3 className="sec-title"><i className="ti ti-paperclip" /> Chứng từ đính kèm</h3>
              <input type="file" multiple onChange={(e) => uploadFiles(e.target.files)} />
              <div style={{ marginTop: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
                {files.map((f) => (
                  <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                    <i className="ti ti-file" /><a href={f.url} target="_blank" style={{ color: 'var(--teal)', flex: 1, textDecoration: 'underline' }}>{f.filename}</a>
                    <button className="icon-btn" onClick={async () => { if (confirm('Xóa file?')) { await api.delete(`/api/attachments/${f.id}`); loadAll() } }}><i className="ti ti-trash" style={{ color: 'var(--red)' }} /></button>
                  </div>
                ))}
                {files.length === 0 && <span style={{ color: '#999', fontSize: 13 }}>Chưa có file nào.</span>}
              </div>
            </div>
          )}

          {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}
          {msg && <div style={{ color: 'var(--green)', fontSize: 13, marginTop: 8 }}>{msg}</div>}
        </div>

        {isLogShown && (
          <div className="card" style={{ padding: 18 }}>
            <h3 className="sec-title"><i className="ti ti-history" /> Lịch sử thao tác</h3>
            <div className="timeline">
              {logs.map((l, i) => (
                <div key={i} className="tl-item">
                  <span className={'tl-dot ' + (l.action === 'approved' ? 'create' : l.action === 'rejected' ? 'delete' : l.action)} />
                  <div><div style={{ fontSize: 13 }}><b>{l.by}</b> — {l.action_label}{l.message ? `: ${l.message}` : ''}</div>
                    <div style={{ fontSize: 12, color: 'var(--muted)' }}>{new Date(l.at).toLocaleString('vi-VN')}</div></div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Centered Modal for detailed editing */}
      {editingIndex !== null && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.45)', zIndex: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }} onClick={() => setEditingIndex(null)}>
          <div style={{ width: '680px', maxWidth: '100%', background: '#fff', borderRadius: '12px', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1), 0 10px 10px -5px rgba(0,0,0,0.04)', display: 'flex', flexDirection: 'column', maxHeight: '85vh', overflow: 'hidden' }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', borderBottom: '1px solid var(--border)' }}>
              <h3 style={{ margin: 0, fontSize: 16, color: 'var(--navy)', fontWeight: 600 }}>Chi tiết dòng: {lines[editingIndex].supplier_code || `Dòng số ${editingIndex + 1}`}</h3>
              <button className="icon-btn" onClick={() => setEditingIndex(null)}><i className="ti ti-x" style={{ fontSize: 18 }} /></button>
            </div>
            <div style={{ padding: '18px 20px', overflowY: 'auto', flex: 1, display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '12px 20px' }}>
              {drawerCols.map((c) => {
                const it = lines[editingIndex];
                const sampleFields = ['sample_date', 'sample_qty', 'lab_result', 'lab_note'];
                if (sampleFields.includes(c.key) && !it.sample_ready) {
                  return null;
                }
                return drawerField(c, editingIndex);
              })}
            </div>
            <div style={{ padding: '12px 18px', borderTop: '1px solid var(--border)', display: 'flex', justifyContent: 'flex-end', gap: 8 }}>
              <button className="btn" style={{ height: 36, padding: '0 18px', fontSize: 13 }} onClick={() => setEditingIndex(null)}>Xác nhận &amp; Đóng</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
