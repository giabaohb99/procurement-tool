import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { prBadge } from '../config/cruds'

const API = '/api/purchase-requests'
const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
const LINE_STATUS = ['', 'Chưa đặt hàng', 'Đã đặt hàng', 'Đã nhận', 'Hủy']
const emptyItem = {
  product_code: '', product_name: '', item_group: '', group_desc: '', qty: 0, unit: '',
  price: 0, warehouse: '', assignee: '', line_status: '', progress_note: '', note: '',
}

export default function PurchaseRequestDetail() {
  const { id } = useParams()
  const isNew = id === 'new'
  const { can } = useAuth()
  const navigate = useNavigate()

  const [pr, setPr] = useState<any>({
    code: '', requester: '', requester_position: '', department: '', head_of_dept: '',
    purpose: '', company_id: 0, request_date: new Date().toISOString().slice(0, 10),
    need_date: '', is_urgent: false, vat_rate: 0.08, note: '', status: 'draft', items: [],
    show_code_on_print: true, suggested_supplier: '', suggested_supplier_tax_code: '', suggested_supplier_contact: '',
    quote_filename: '', quote_file_url: '',
  })
  const [companies, setCompanies] = useState<any[]>([])
  const [groups, setGroups] = useState<string[]>([])
  const [units, setUnits] = useState<string[]>([])
  const [warehouses, setWarehouses] = useState<string[]>([])
  const [employees, setEmployees] = useState<any[]>([])
  const [departments, setDepartments] = useState<any[]>([])
  const [suppliers, setSuppliers] = useState<any[]>([])
  const [products, setProducts] = useState<any[]>([])
  const [logs, setLogs] = useState<any[]>([])
  const [files, setFiles] = useState<any[]>([])
  const [err, setErr] = useState('')
  const [msg, setMsg] = useState('')

  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items))
    api.get('/api/item-groups', { params: { page_size: 500 } }).then((r) => setGroups(r.data.data.items.map((x: any) => x.name)))
    api.get('/api/units', { params: { page_size: 200 } }).then((r) => setUnits(r.data.data.items.map((x: any) => x.name)))
    api.get('/api/warehouses', { params: { page_size: 200 } }).then((r) => setWarehouses(r.data.data.items.map((x: any) => x.name)))
    api.get('/api/employees', { params: { page_size: 1000 } }).then((r) => setEmployees(r.data.data.items))
    api.get('/api/departments', { params: { page_size: 500 } }).then((r) => setDepartments(r.data.data.items))
    api.get('/api/suppliers', { params: { page_size: 1000 } }).then((r) => setSuppliers(r.data.data.items))
    api.get('/api/products', { params: { page_size: 1000 } }).then((r) => setProducts(r.data.data.items))
  }, [])

  async function loadAll() {
    const r = await api.get(`${API}/${id}`)
    setPr(r.data.data)
    api.get('/api/audit-logs', { params: { entity: 'purchase_request', entity_id: id } }).then((x) => setLogs(x.data.data))
    api.get('/api/attachments', { params: { entity: 'purchase_request', entity_id: id } }).then((x) => setFiles(x.data.data))
  }
  useEffect(() => { if (!isNew) loadAll() }, [id])

  const editable = isNew || pr.status === 'draft' || pr.status === 'rejected'
  const setH = (k: string, v: any) => setPr((s: any) => ({ ...s, [k]: v }))
  const items = pr.items || []
  const setItem = (i: number, k: string, v: any) =>
    setPr((s: any) => ({ ...s, items: s.items.map((it: any, idx: number) => idx === i ? { ...it, [k]: v } : it) }))
  const addItems = (n = 1) => setPr((s: any) => ({ ...s, items: [...(s.items || []), ...Array.from({ length: n }, () => ({ ...emptyItem }))] }))
  const delItem = (i: number) => setPr((s: any) => ({ ...s, items: s.items.filter((_: any, idx: number) => idx !== i) }))

  const subtotal = items.reduce((s: number, it: any) => s + (Number(it.qty) || 0) * (Number(it.price) || 0), 0)
  const vat = subtotal * (Number(pr.vat_rate) || 0)
  const total = subtotal + vat

  const handleRequesterChange = (empName: string) => {
    const emp = employees.find(e => e.full_name === empName)
    if (emp) {
      const dept = departments.find(d => d.id === emp.department_id)
      const deptName = dept ? dept.name : ''
      const head = employees.find(e => e.department_id === emp.department_id && (
        e.position.toLowerCase().includes('trưởng') ||
        e.position.toLowerCase().includes('manager') ||
        e.position.toLowerCase().includes('head')
      ))
      setPr((s: any) => ({
        ...s,
        requester: emp.full_name,
        requester_position: emp.position || '',
        department: deptName,
        head_of_dept: head ? head.full_name : s.head_of_dept || '',
        company_id: emp.company_id || s.company_id
      }))
    } else {
      setPr((s: any) => ({ ...s, requester: empName }))
    }
  }

  const handleSupplierChange = (supName: string) => {
    const sup = suppliers.find(s => s.name === supName)
    setPr((s: any) => ({
      ...s,
      suggested_supplier: supName,
      suggested_supplier_tax_code: sup ? sup.tax_code : '',
      suggested_supplier_contact: sup ? (sup.phone || sup.address || '') : ''
    }))
  }

  const handleProductChange = (i: number, prodCode: string) => {
    const prod = products.find(p => p.code === prodCode)
    if (prod) {
      setPr((s: any) => ({
        ...s,
        items: s.items.map((it: any, idx: number) => idx === i ? {
          ...it,
          product_code: prod.code,
          product_name: prod.name,
          unit: prod.unit || it.unit,
          item_group: prod.item_group || it.item_group,
        } : it)
      }))
    } else {
      setItem(i, 'product_code', prodCode)
    }
  }

  async function uploadQuoteFile(fl: FileList | null) {
    if (!fl?.length) return
    const fd = new FormData()
    fd.append('entity', 'purchase_request_quote')
    fd.append('entity_id', String(id || 0))
    fd.append('files', fl[0])
    try {
      setErr('')
      const r = await api.post('/api/attachments', fd)
      const fileObj = r.data.data[0]
      setPr((s: any) => ({
        ...s,
        quote_filename: fileObj.filename,
        quote_file_url: fileObj.url,
      }))
      setMsg('Đã tải lên báo giá thành công')
    } catch (ex: any) {
      setErr(ex?.response?.data?.error?.message || 'Lỗi tải báo giá')
    }
  }

  const clearQuoteFile = () => {
    setPr((s: any) => ({
      ...s,
      quote_filename: '',
      quote_file_url: '',
    }))
  }

  async function save(submitAfterSave = false) {
    setErr(''); setMsg('')
    const body = {
      company_id: Number(pr.company_id) || 0, requester: pr.requester, requester_position: pr.requester_position,
      department: pr.department, head_of_dept: pr.head_of_dept, purpose: pr.purpose,
      request_date: pr.request_date, need_date: pr.need_date, is_urgent: pr.is_urgent,
      vat_rate: Number(pr.vat_rate) || 0, note: pr.note,
      show_code_on_print: pr.show_code_on_print,
      suggested_supplier: pr.suggested_supplier,
      suggested_supplier_tax_code: pr.suggested_supplier_tax_code,
      suggested_supplier_contact: pr.suggested_supplier_contact,
      quote_filename: pr.quote_filename,
      quote_file_url: pr.quote_file_url,
      items: items.filter((it: any) => it.product_name),
    }
    try {
      let savedPrId = id
      if (isNew) {
        const r = await api.post(API, body)
        savedPrId = r.data.data.id
        if (submitAfterSave) {
          await api.post(`${API}/${savedPrId}/submit`)
        }
        navigate(`/purchase-requests/${savedPrId}`)
      } else {
        await api.patch(`${API}/${id}`, body)
        if (submitAfterSave) {
          await api.post(`${API}/${id}/submit`)
        }
        setMsg('Đã lưu thành công')
        loadAll()
      }
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi khi lưu') }
  }

  async function action(path: string, payload: any = {}) {
    setErr('')
    try { await api.post(`${API}/${id}/${path}`, payload); loadAll() }
    catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi') }
  }

  async function uploadFiles(fl: FileList | null) {
    if (!fl?.length) return
    const fd = new FormData(); fd.append('entity', 'purchase_request'); fd.append('entity_id', String(id))
    Array.from(fl).forEach((f) => fd.append('files', f))
    try { await api.post('/api/attachments', fd); loadAll() }
    catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi tải file') }
  }

  const txt = (i: number, k: string, w = 120) => (
    <input className="cell-input" style={{ width: w }} value={items[i][k] ?? ''} disabled={!editable} onChange={(e) => setItem(i, k, e.target.value)} />
  )
  const num = (i: number, k: string, w = 90) => (
    <input className="cell-input" type="number" style={{ width: w }} value={items[i][k] ?? 0} disabled={!editable} onChange={(e) => setItem(i, k, Number(e.target.value))} />
  )
  const sel = (i: number, k: string, opts: string[], w = 130) => (
    <select className="cell-input" style={{ width: w }} value={items[i][k] ?? ''} disabled={!editable} onChange={(e) => setItem(i, k, e.target.value)}>
      <option value="">—</option>
      {opts.map((o) => <option key={o} value={o}>{o}</option>)}
    </select>
  )

  const isLogShown = !isNew && logs.length > 0;

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate('/purchase-requests')}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>{isNew ? 'Tạo Yêu cầu Thu mua mới' : (pr.purpose || pr.code)}</h2>
        {!isNew && prBadge(pr.status)}
        <span style={{ flex: 1 }} />
        {!isNew && <button className="btn ghost" onClick={() => window.open(`/print/purchase-request/${id}`, '_blank')}><i className="ti ti-printer" />In phiếu</button>}
        {!isNew && pr.status === 'submitted' && can('purchase_request', 'approve') && (
          <>
            <button className="btn" onClick={() => action('approve')}><i className="ti ti-check" />Duyệt</button>
            <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={() => action('reject', { reason: prompt('Lý do từ chối:') || '' })}><i className="ti ti-x" />Từ chối</button>
          </>
        )}
      </div>

      <div className={isLogShown ? "detail-grid" : ""}>
        <div>
          {/* Thông tin chung */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <h3 className="sec-title">Thông tin chung</h3>
            <div className="form-grid">
              <div className="form-row">
                <label>Mã phiếu yêu cầu</label>
                <input placeholder="Để trống để tự động tạo" value={pr.code || ''} disabled={!isNew} onChange={(e) => setH('code', e.target.value)} />
              </div>
              <div className="form-row">
                <label>Ngày tiếp nhận *</label>
                <input type="date" value={pr.request_date || ''} disabled={!editable} onChange={(e) => setH('request_date', e.target.value)} />
              </div>
              <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontWeight: 500 }}>
                  <input type="checkbox" checked={!!pr.show_code_on_print} disabled={!editable} onChange={(e) => setH('show_code_on_print', e.target.checked)} style={{ width: 16, height: 16 }} />
                  Hiển thị Mã phiếu trên form in
                </label>
              </div>
              <div className="form-row">
                <label>Công ty *</label>
                <select value={pr.company_id || ''} disabled={!editable} onChange={(e) => setH('company_id', Number(e.target.value))}>
                  <option value="">-- Chọn Công ty --</option>
                  {companies.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
                </select>
              </div>
              <div className="form-row">
                <label>Nhân sự YC *</label>
                <select value={pr.requester || ''} disabled={!editable} onChange={(e) => handleRequesterChange(e.target.value)}>
                  <option value="">-- Chọn Nhân sự --</option>
                  {employees.map((e) => <option key={e.id} value={e.full_name}>{e.code} - {e.full_name}</option>)}
                </select>
              </div>
              <div className="form-row">
                <label>Bộ phận YC *</label>
                <input value={pr.department || ''} placeholder="Tự động điền theo Nhân sự..." disabled />
              </div>
              <div className="form-row">
                <label>Chức vụ (Nếu có)</label>
                <input value={pr.requester_position || ''} placeholder="Tự động điền theo Nhân sự..." disabled={!editable} onChange={(e) => setH('requester_position', e.target.value)} />
              </div>
              <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                <label>Trưởng bộ phận (TBP) / Người liên hệ *</label>
                <input value={pr.head_of_dept || ''} placeholder="Tự động điền theo Nhân sự..." disabled={!editable} onChange={(e) => setH('head_of_dept', e.target.value)} />
              </div>
              <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                <label>Mục đích mua hàng *</label>
                <textarea placeholder="Nhập mục đích mua hàng hóa/dịch vụ..." style={{ minHeight: 60 }} value={pr.purpose || ''} disabled={!editable} onChange={(e) => setH('purpose', e.target.value)} />
              </div>
              <div className="form-row">
                <label>Thời gian cần hàng/dịch vụ</label>
                <input type="date" value={pr.need_date || ''} disabled={!editable} onChange={(e) => setH('need_date', e.target.value)} />
              </div>
              <div className="form-row">
                <label>VAT (%)</label>
                <input type="number" value={Math.round((Number(pr.vat_rate) || 0) * 100)} disabled={!editable} onChange={(e) => setH('vat_rate', Number(e.target.value) / 100)} />
              </div>
              <div className="form-row">
                <label style={{ display: 'flex', alignItems: 'center', gap: 6, cursor: 'pointer' }}>
                  <input type="checkbox" checked={!!pr.is_urgent} disabled={!editable} onChange={(e) => setH('is_urgent', e.target.checked)} style={{ width: 18, height: 18 }} />
                  Đơn gấp
                </label>
              </div>
              <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                <label>Nội dung mua hàng</label>
                <textarea placeholder="Nhập nội dung chi tiết..." style={{ minHeight: 80 }} value={pr.note || ''} disabled={!editable} onChange={(e) => setH('note', e.target.value)} />
              </div>
            </div>
          </div>

          {/* Mặt hàng - inline edit, kéo ngang */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 className="sec-title" style={{ margin: 0, borderBottom: 'none', paddingBottom: 0 }}>Danh sách Sản phẩm Yêu cầu</h3>
              {editable && (
                <button className="btn ghost" onClick={() => addItems(1)} style={{ height: 30, padding: '0 10px', fontSize: 13 }}>
                  <i className="ti ti-plus" /> Thêm SP
                </button>
              )}
            </div>
            <div className="items-scroll">
              <table className="items-table" style={{ minWidth: 1000 }}>
                <thead>
                  <tr>
                    <th style={{ width: 40 }}>No.</th>
                    <th style={{ width: 140 }}>Mã hàng</th>
                    <th>Tên sản phẩm *</th>
                    <th style={{ width: 140 }}>Phân loại</th>
                    <th style={{ width: 90 }}>ĐVT</th>
                    <th style={{ width: 90 }}>Số lượng</th>
                    <th style={{ width: 110 }}>Đơn giá</th>
                    <th style={{ width: 120 }}>Thành tiền</th>
                    <th>Ghi chú</th>
                    {editable && <th style={{ width: 40 }} />}
                  </tr>
                </thead>
                <tbody>
                  {items.map((it: any, i: number) => (
                    <tr key={i}>
                      <td>{i + 1}</td>
                      <td>
                        <select className="cell-input" style={{ width: 130 }} value={it.product_code || ''} disabled={!editable} onChange={(e) => handleProductChange(i, e.target.value)}>
                          <option value="">-- Chọn --</option>
                          {products.map((p) => <option key={p.id} value={p.code}>{p.code}</option>)}
                        </select>
                      </td>
                      <td>{txt(i, 'product_name', '100%')}</td>
                      <td>{sel(i, 'item_group', groups, 130)}</td>
                      <td>{sel(i, 'unit', units, 80)}</td>
                      <td>{num(i, 'qty', 80)}</td>
                      <td>{num(i, 'price', 100)}</td>
                      <td style={{ textAlign: 'right', fontWeight: 500 }}>{fmt((Number(it.qty) || 0) * (Number(it.price) || 0))}</td>
                      <td>{txt(i, 'note', '100%')}</td>
                      {editable && (
                        <td style={{ textAlign: 'center' }}>
                          <button className="icon-btn" onClick={() => delItem(i)}><i className="ti ti-trash" style={{ color: 'var(--red)' }} /></button>
                        </td>
                      )}
                    </tr>
                  ))}
                  {items.length === 0 && <tr><td colSpan={editable ? 10 : 9} style={{ textAlign: 'center', color: '#999', padding: 20 }}>Chưa có sản phẩm nào</td></tr>}
                </tbody>
              </table>
            </div>
            {editable && items.length > 0 && (
              <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                <button className="btn ghost" onClick={() => addItems(Math.max(1, parseInt(prompt('Thêm bao nhiêu dòng?', '5') || '0') || 0))} style={{ height: 30, padding: '0 8px', fontSize: 12 }}><i className="ti ti-rows" /> Thêm nhiều dòng</button>
              </div>
            )}
            <div style={{ marginTop: 14, textAlign: 'right', fontSize: 14 }}>
              <div>Tổng tiền hàng: <b>{fmt(subtotal)}</b></div>
              <div>VAT ({Math.round((Number(pr.vat_rate) || 0) * 100)}%): <b>{fmt(vat)}</b></div>
              <div style={{ fontSize: 16, color: 'var(--navy)', marginTop: 4 }}>Tổng thanh toán: <b>{fmt(total)}</b></div>
            </div>
          </div>

          {/* Nhà cung cấp đề xuất */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <h3 className="sec-title">Nhà cung cấp đề xuất (Nếu có)</h3>
            <div className="form-grid" style={{ marginBottom: 14 }}>
              <div className="form-row">
                <label>Tên nhà cung cấp đề xuất</label>
                <select value={pr.suggested_supplier || ''} disabled={!editable} onChange={(e) => handleSupplierChange(e.target.value)}>
                  <option value="">-- Chọn NCC --</option>
                  {suppliers.map((s) => <option key={s.id} value={s.name}>{s.name}</option>)}
                </select>
              </div>
              <div className="form-row">
                <label>Mã số thuế NCC</label>
                <input value={pr.suggested_supplier_tax_code || ''} placeholder="Mã số thuế NCC" disabled={!editable} onChange={(e) => setH('suggested_supplier_tax_code', e.target.value)} />
              </div>
              <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                <label>Liên hệ NCC (SĐT / Email / Địa chỉ...)</label>
                <input value={pr.suggested_supplier_contact || ''} placeholder="Thông tin liên hệ nhà cung cấp..." disabled={!editable} onChange={(e) => setH('suggested_supplier_contact', e.target.value)} />
              </div>
            </div>

            {/* Đính kèm báo giá */}
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: 14 }}>
              <label style={{ fontSize: 13, color: 'var(--muted)', fontWeight: 500, display: 'block', marginBottom: 6 }}>Báo giá đính kèm (Nếu có)</label>
              {!isNew ? (
                <div>
                  {!pr.quote_file_url ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <input type="file" id="quote-upload" style={{ display: 'none' }} disabled={!editable} onChange={(e) => uploadQuoteFile(e.target.files)} />
                      <label htmlFor="quote-upload" className="btn ghost" style={{ cursor: 'pointer', height: 32, fontSize: 13 }}>
                        <i className="ti ti-upload" /> Chọn báo giá đính kèm
                      </label>
                    </div>
                  ) : (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                      <i className="ti ti-file" />
                      <a href={pr.quote_file_url} target="_blank" style={{ color: 'var(--teal)', flex: 1, textDecoration: 'underline' }}>{pr.quote_filename}</a>
                      {editable && (
                        <button className="icon-btn" onClick={clearQuoteFile}>
                          <i className="ti ti-trash" style={{ color: 'var(--red)' }} />
                        </button>
                      )}
                    </div>
                  )}
                </div>
              ) : (
                <span style={{ color: '#999', fontSize: 13 }}><i>(Vui lòng tạo phiếu yêu cầu để có thể đính kèm báo giá)</i></span>
              )}
            </div>
          </div>

          {/* Chứng từ đính kèm khác */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <h3 className="sec-title"><i className="ti ti-paperclip" /> Chứng từ/Tài liệu đính kèm khác (Bản vẽ, đề xuất khác)</h3>
            {!isNew ? (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                  <input type="file" id="file-upload" multiple style={{ display: 'none' }} disabled={!editable} onChange={(e) => uploadFiles(e.target.files)} />
                  <label htmlFor="file-upload" className="btn ghost" style={{ cursor: 'pointer', height: 32, fontSize: 13 }}>
                    <i className="ti ti-upload" /> Chọn file đính kèm
                  </label>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {files.map((f) => (
                    <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                      <i className="ti ti-file" />
                      <a href={f.url} target="_blank" style={{ color: 'var(--teal)', flex: 1, textDecoration: 'underline' }}>{f.filename}</a>
                      {editable && (
                        <button className="icon-btn" onClick={async () => { if (confirm('Xóa file?')) { await api.delete(`/api/attachments/${f.id}`); loadAll() } }}>
                          <i className="ti ti-trash" style={{ color: 'var(--red)' }} />
                        </button>
                      )}
                    </div>
                  ))}
                  {files.length === 0 && <span style={{ color: '#999', fontSize: 13 }}>Chưa có tài liệu nào khác được đính kèm.</span>}
                </div>
              </div>
            ) : (
              <span style={{ color: '#999', fontSize: 13 }}><i>(Vui lòng tạo phiếu yêu cầu để có thể đính kèm tài liệu khác)</i></span>
            )}
          </div>

          {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}
          {msg && <div style={{ color: 'var(--green)', fontSize: 13, marginTop: 8 }}>{msg}</div>}

          {/* Form Actions */}
          {editable && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20 }}>
              <button className="btn ghost" onClick={() => navigate('/purchase-requests')}>Hủy</button>
              <button className="btn secondary" onClick={() => save(false)}>Lưu nháp</button>
              <button className="btn" onClick={() => save(true)}>Lưu & Gửi Duyệt</button>
            </div>
          )}

          {!isNew && editable && can('purchase_request', 'delete') && (
            <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)', marginTop: 24 }}
                    onClick={async () => { if (confirm('Xóa yêu cầu mua này?')) { await api.delete(`${API}/${id}`); navigate('/purchase-requests') } }}><i className="ti ti-trash" /> Xóa yêu cầu</button>
          )}
        </div>

        {/* Lịch sử thao tác (Log) */}
        {isLogShown && (
          <div className="card" style={{ padding: 18 }}>
            <h3 className="sec-title"><i className="ti ti-history" /> Lịch sử thao tác</h3>
            <div className="timeline">
              {logs.map((l, i) => (
                <div key={i} className="tl-item">
                  <span className={'tl-dot ' + (l.action === 'approved' ? 'create' : l.action === 'rejected' ? 'delete' : l.action)} />
                  <div>
                    <div style={{ fontSize: 13 }}><b>{l.by}</b> — {l.action_label}{l.message ? `: ${l.message}` : ''}</div>
                    <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>{new Date(l.at).toLocaleString('vi-VN')}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
