import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { prBadge } from '../config/cruds'
import Select from 'react-select'
import AsyncSelect from 'react-select/async'

// Ô chọn sản phẩm có tìm kiếm (gõ mã hoặc tên → LIKE trên server). Dùng cho DS cả ngàn SP.
function ProductPicker({ code, name, disabled, onPick }: { code?: string; name?: string; disabled?: boolean; onPick: (prod: any) => void }) {
  const t = useRef<any>(null)
  const loadOptions = (input: string) =>
    new Promise<any[]>((resolve) => {
      clearTimeout(t.current)
      t.current = setTimeout(async () => {
        try {
          const r = await api.get('/api/products', { params: { search: input, page_size: 30 } })
          resolve((r.data.data.items || []).map((p: any) => ({ value: p.code, label: `${p.code} — ${p.name}`, prod: p })))
        } catch { resolve([]) }
      }, 250)
    })
  const cur = code ? { value: code, label: name ? `${code} — ${name}` : code } : null
  return (
    <AsyncSelect
      value={cur} isDisabled={disabled} isClearable cacheOptions defaultOptions
      loadOptions={loadOptions} placeholder="Gõ mã/tên để tìm..."
      noOptionsMessage={({ inputValue }) => (inputValue ? 'Không tìm thấy' : 'Gõ để tìm sản phẩm')}
      loadingMessage={() => 'Đang tìm...'}
      onChange={(o: any) => onPick(o?.prod || null)}
      menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
      styles={{
        control: (b) => ({ ...b, minHeight: 36, borderRadius: 8, borderColor: '#E9EDF7', fontSize: 13 }),
        menuPortal: (b) => ({ ...b, zIndex: 9999 }),
      }}
    />
  )
}

const API = '/api/purchase-requests'
const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
const LINE_STATUS = ['Chưa đặt hàng', 'Đã đặt hàng', 'Đã gửi ĐMH cho KT', 'Đã nhận hàng', 'Hoàn thành', 'Hủy đơn', 'Tạm ngưng']
const LS_COLOR: Record<string, string> = {
  'Chưa đặt hàng': '#94a3b8', 'Đã đặt hàng': '#00AEEF', 'Đã gửi ĐMH cho KT': '#7c3aed',
  'Đã nhận hàng': '#0d9488', 'Hoàn thành': '#16a34a', 'Hủy đơn': '#b91c1c', 'Tạm ngưng': '#d97706',
}
const emptyItem = {
  product_code: '', product_name: '', item_group: '', group_desc: '', qty: 0, unit: '',
  price: 0, warehouse: '', required_date: '', assignee: '', line_status: 'Chưa đặt hàng', progress_note: '', note: '',
}

export default function PurchaseRequestDetail() {
  const { id } = useParams()
  const isNew = id === 'new'
  const { user, can } = useAuth()
  const navigate = useNavigate()

  const [pr, setPr] = useState<any>({
    code: '', requester: '', requester_position: '', department: '', head_of_dept: '',
    purpose: '', company_id: 0, request_date: new Date().toISOString().slice(0, 10),
    need_date: '', is_urgent: false, note: '', status: 'draft', items: [],
    show_code_on_print: true, suggested_supplier: '', suggested_supplier_tax_code: '', suggested_supplier_contact: '',
    quote_filename: '', quote_file_url: '',
  })
  const [companies, setCompanies] = useState<any[]>([])
  const [itemGroups, setItemGroups] = useState<any[]>([])
  const [groups, setGroups] = useState<string[]>([])
  const [units, setUnits] = useState<string[]>([])
  const [warehouses, setWarehouses] = useState<string[]>([])
  const [employees, setEmployees] = useState<any[]>([])
  const [departments, setDepartments] = useState<any[]>([])
  const [logs, setLogs] = useState<any[]>([])
  const [files, setFiles] = useState<any[]>([])
  const [err, setErr] = useState('')
  const [msg, setMsg] = useState('')
  const [editIdx, setEditIdx] = useState<number | null>(null)   // dòng đang mở popup chi tiết

  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items)).catch(() => {})
    api.get('/api/item-groups', { params: { page_size: 500 } }).then((r) => { setItemGroups(r.data.data.items); setGroups(r.data.data.items.map((x: any) => x.name)) }).catch(() => {})
    api.get('/api/units', { params: { page_size: 200 } }).then((r) => setUnits(r.data.data.items.map((x: any) => x.name))).catch(() => {})
    api.get('/api/warehouses', { params: { page_size: 200 } }).then((r) => setWarehouses(r.data.data.items.map((x: any) => x.name))).catch(() => {})
    api.get('/api/employees', { params: { page_size: 1000 } }).then((r) => setEmployees(r.data.data.items)).catch(() => {})
    api.get('/api/departments', { params: { page_size: 500 } }).then((r) => setDepartments(r.data.data.items)).catch(() => {})
  }, [])

  async function loadAll() {
    const r = await api.get(`${API}/${id}`)
    setPr(r.data.data)
    api.get('/api/audit-logs', { params: { entity: 'purchase_request', entity_id: id } }).then((x) => setLogs(x.data.data)).catch(() => {})
    api.get('/api/attachments', { params: { entity: 'purchase_request', entity_id: id } }).then((x) => setFiles(x.data.data)).catch(() => {})
  }
  useEffect(() => { if (!isNew) loadAll() }, [id])

  useEffect(() => {
    if (!isNew || !user || pr.requester) return
    if (employees.length > 0) {
      const matchEmp = employees.find(e => e.email === user.email || e.full_name === user.full_name)
      if (matchEmp) { handleRequesterChange(matchEmp.full_name, true); return }
    }
    // Không có quyền xem DS nhân sự → điền theo tài khoản đăng nhập
    if (isStaff) {
      setPr((s: any) => ({
        ...s, requester: (user as any).full_name || '',
        department: (user as any).department_name || s.department,
        company_id: (user as any).company_id || s.company_id,
      }))
    }
  }, [isNew, employees, user])

  // Tự điền Trưởng bộ phận theo phòng ban (người yêu cầu không xem được DS nhân sự → hỏi server)
  useEffect(() => {
    if (!isNew || !pr.department || pr.head_of_dept) return
    api.get(`${API}/meta/dept-head`, { params: { department: pr.department } })
      .then((r) => { const h = r.data.data.head_of_dept; if (h) setH('head_of_dept', h) })
      .catch(() => {})
  }, [isNew, pr.department])

  const editable = isNew || pr.status === 'draft' || pr.status === 'rejected'
  const isStaff = !can('purchase_request', 'approve') && !can('purchase_request', 'delete')
  const canAssignPurchaser = can('purchase_request', 'approve')   // phân bổ NSTM
  const canManage = can('purchase_request', 'cancel')             // admin/quản lý: hủy/trả/hoàn thành
  // Trạng thái dòng chỉ cho NSTM phụ trách chính dòng đó hoặc admin/quản lý
  const isAssignee = (it: any) => !!it.assignee && it.assignee === (user as any)?.emp_code
  const canLineStatus = (it: any) => canAssignPurchaser || canManage || isAssignee(it)
  const canEditNote = (it: any) => editable || canLineStatus(it)

  // NSTM = nhân sự phòng thu mua; hiển thị TÊN, lưu MÃ NV
  const purDeptIds = departments.filter(d => (d.name || '').toLowerCase().includes('thu mua')).map(d => d.id)
  const purchaserOptions = employees
    .filter(e => purDeptIds.includes(e.department_id) || (e.department_name || '').toLowerCase().includes('thu mua'))
    .map(e => ({ value: e.code, label: e.full_name }))
  const empName = (code: string) => employees.find(e => e.code === code)?.full_name || code
  const companyOptions = companies.map(c => ({ value: c.id, label: c.name }))
  const employeeOptions = employees.map(e => ({ value: e.full_name, label: e.full_name }))
  const warehouseOptions = warehouses.map(w => ({ value: w, label: w }))

  const setH = (k: string, v: any) => setPr((s: any) => ({ ...s, [k]: v }))
  const items = pr.items || []
  const setItem = (i: number, k: string, v: any) =>
    setPr((s: any) => ({ ...s, items: s.items.map((it: any, idx: number) => idx === i ? { ...it, [k]: v } : it) }))
  const addItems = (n = 1) => setPr((s: any) => ({ ...s, items: [...(s.items || []), ...Array.from({ length: n }, () => ({ ...emptyItem }))] }))
  const delItem = (i: number) => setPr((s: any) => ({ ...s, items: s.items.filter((_: any, idx: number) => idx !== i) }))
  const copyItem = (i: number) => setPr((s: any) => {
    const src = { ...s.items[i] }; delete src.id
    const arr = [...s.items]; arr.splice(i + 1, 0, src); return { ...s, items: arr }
  })

  // Đổi trạng thái dòng ngay trên bảng ngoài
  async function changeLineStatus(i: number, val: string) {
    setItem(i, 'line_status', val)
    const it = items[i]
    if (!editable && it.id && canLineStatus(it)) {
      setErr(''); setMsg('')
      try { await api.patch(`${API}/${id}/item-status`, { items: [{ id: it.id, line_status: val }] }); setMsg('Đã cập nhật trạng thái'); loadAll() }
      catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi cập nhật trạng thái'); loadAll() }
    }
  }

  const subtotal = items.reduce((s: number, it: any) => s + (Number(it.qty) || 0) * (Number(it.price) || 0), 0)

  const groupDesc = (name: string) => {
    const g = itemGroups.find(x => x.name === name)
    if (!g) return ''
    const p: string[] = []
    if (g.std_days) p.push(`Hàng NCC có sẵn: ${g.std_days} ngày`)
    if (g.std_days_unavail) p.push(`không sẵn: ${g.std_days_unavail} ngày`)
    return p.join(' · ')
  }

  const handleRequesterChange = (empName: string, isAutoFill = false) => {
    const emp = employees.find(e => e.full_name === empName)
    if (emp) {
      const dept = departments.find(d => d.id === emp.department_id)
      const deptName = dept ? dept.name : ''
      // Trưởng bộ phận = nhân sự cùng phòng có chức danh "trưởng" (role_name/position)
      const head = employees.find(e => e.department_id === emp.department_id && e.id !== emp.id && (
        (e.role_name || '').toLowerCase().includes('trưởng') ||
        (e.position || '').toLowerCase().includes('trưởng') ||
        (e.role_name || '').toLowerCase().includes('manager') ||
        (e.position || '').toLowerCase().includes('head')
      ))
      setPr((s: any) => ({
        ...s,
        requester: emp.full_name,
        requester_position: isAutoFill && s.requester_position ? s.requester_position : (emp.position || emp.role_name || ''),
        department: isAutoFill && s.department ? s.department : deptName,
        head_of_dept: isAutoFill && s.head_of_dept ? s.head_of_dept : (head ? head.full_name : s.head_of_dept || ''),
        company_id: (isAutoFill && s.company_id) ? s.company_id : (emp.company_id || s.company_id),
      }))
    } else {
      setPr((s: any) => ({ ...s, requester: empName }))
    }
  }

  // Chọn SP từ ô tìm kiếm (nhận cả object) → tự điền tên/ĐVT/phân loại
  const applyProduct = (i: number, prod: any) => {
    if (!prod) { setItem(i, 'product_code', ''); return }
    setPr((s: any) => ({
      ...s,
      items: s.items.map((it: any, idx: number) => idx === i ? {
        ...it, product_code: prod.code, product_name: prod.name,
        unit: prod.unit || it.unit, item_group: prod.item_group || it.item_group,
        group_desc: groupDesc(prod.item_group || it.item_group),
      } : it),
    }))
  }

  async function uploadQuoteFile(fl: FileList | null) {
    if (!fl?.length) return
    const fd = new FormData(); fd.append('entity', 'purchase_request_quote'); fd.append('entity_id', String(id || 0)); fd.append('files', fl[0])
    try {
      setErr('')
      const r = await api.post('/api/attachments', fd)
      const f = r.data.data[0]
      setPr((s: any) => ({ ...s, quote_filename: f.filename, quote_file_url: f.url }))
      setMsg('Đã tải lên báo giá')
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi tải báo giá') }
  }
  const clearQuoteFile = () => setPr((s: any) => ({ ...s, quote_filename: '', quote_file_url: '' }))

  function validate(): string {
    if (!pr.company_id) return 'Vui lòng chọn Công ty'
    if (!pr.requester) return 'Vui lòng chọn Nhân sự yêu cầu'
    const valid = items.filter((it: any) => it.product_name)
    if (valid.length === 0) return 'Cần ít nhất 1 sản phẩm'
    for (const it of valid) {
      if (!(Number(it.qty) > 0)) return `Sản phẩm "${it.product_name}" cần Số lượng > 0`
      if (!it.warehouse) return `Sản phẩm "${it.product_name}" cần chọn Kho nhận`
    }
    return ''
  }

  async function save(submitAfterSave = false) {
    setErr(''); setMsg('')
    const v = validate()
    if (v) { setErr(v); return }
    const body = {
      company_id: Number(pr.company_id) || 0, requester: pr.requester, requester_position: pr.requester_position,
      department: pr.department, head_of_dept: pr.head_of_dept, purpose: pr.purpose,
      request_date: pr.request_date, need_date: pr.need_date, is_urgent: pr.is_urgent, note: pr.note,
      show_code_on_print: pr.show_code_on_print,
      suggested_supplier: pr.suggested_supplier, suggested_supplier_tax_code: pr.suggested_supplier_tax_code,
      suggested_supplier_contact: pr.suggested_supplier_contact,
      quote_filename: pr.quote_filename, quote_file_url: pr.quote_file_url,
      items: items.filter((it: any) => it.product_name),
    }
    try {
      if (isNew) {
        const r = await api.post(API, body)
        const nid = r.data.data.id
        if (submitAfterSave) await api.post(`${API}/${nid}/submit`)
        navigate(`/purchase-requests/${nid}`)
      } else {
        await api.patch(`${API}/${id}`, body)
        if (submitAfterSave) await api.post(`${API}/${id}/submit`)
        setMsg('Đã lưu'); loadAll()
      }
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi khi lưu') }
  }

  async function action(path: string, payload: any = {}) {
    setErr('')
    try { await api.post(`${API}/${id}/${path}`, payload); loadAll() }
    catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi') }
  }

  // Lưu popup chi tiết dòng khi phiếu KHÔNG còn ở trạng thái sửa (đã gửi duyệt trở đi)
  async function savePopupLine(it: any) {
    setErr(''); setMsg('')
    try {
      if (canLineStatus(it))
        await api.patch(`${API}/${id}/item-status`, { items: [{ id: it.id, line_status: it.line_status, progress_note: it.progress_note, note: it.note }] })
      if (canAssignPurchaser)
        await api.patch(`${API}/${id}/assign`, { items: [{ id: it.id, assignee: it.assignee || '' }] })
      setMsg('Đã cập nhật dòng'); setEditIdx(null); loadAll()
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi cập nhật dòng') }
  }

  async function uploadFiles(fl: FileList | null) {
    if (!fl?.length) return
    const fd = new FormData(); fd.append('entity', 'purchase_request'); fd.append('entity_id', String(id))
    Array.from(fl).forEach((f) => fd.append('files', f))
    try { await api.post('/api/attachments', fd); loadAll() }
    catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi tải file') }
  }

  const isLogShown = !isNew && logs.length > 0
  const edit = editIdx != null ? items[editIdx] : null

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
            <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={() => { const r = prompt('Lý do từ chối:'); if (r !== null) action('reject', { reason: r }) }}><i className="ti ti-x" />Từ chối</button>
          </>
        )}
        {!isNew && canManage && ['approved', 'processing'].includes(pr.status) && (
          <button className="btn secondary" onClick={() => { if (confirm('Đánh dấu phiếu HOÀN THÀNH?')) action('complete') }}><i className="ti ti-checks" />Hoàn thành</button>
        )}
        {!isNew && canManage && !['draft', 'cancelled'].includes(pr.status) && (
          <button className="btn ghost" onClick={() => { const r = prompt('Lý do trả phiếu về (Nháp):'); if (r !== null) action('return', { reason: r }) }}><i className="ti ti-arrow-back-up" />Trả về</button>
        )}
        {!isNew && canManage && pr.status !== 'cancelled' && (
          <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={() => { if (pr.status === 'draft') { if (confirm('Hủy phiếu này?')) action('cancel', { reason: '' }); return } const r = prompt('Lý do hủy đơn:'); if (r !== null) action('cancel', { reason: r }) }}><i className="ti ti-ban" />Hủy đơn</button>
        )}
      </div>

      <div className={isLogShown ? 'detail-grid' : ''}>
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
              <div className="form-row">
                <label>Công ty nhận hóa đơn *</label>
                <Select value={companyOptions.find(o => o.value === pr.company_id) || null}
                  onChange={(o: any) => setH('company_id', o ? o.value : 0)} options={companyOptions}
                  isDisabled={!editable} isClearable placeholder="Chọn công ty"
                  styles={{ control: (b) => ({ ...b, minHeight: 40, borderRadius: 12, borderColor: '#E9EDF7' }) }} />
              </div>
              <div className="form-row">
                <label>Nhân sự YC *</label>
                <Select value={employeeOptions.find(o => o.value === pr.requester) || (pr.requester ? { value: pr.requester, label: pr.requester } : null)}
                  onChange={(o: any) => handleRequesterChange(o ? o.value : '')} options={employeeOptions}
                  isDisabled={!editable || isStaff} isClearable placeholder="Chọn nhân sự"
                  styles={{ control: (b) => ({ ...b, minHeight: 40, borderRadius: 12, borderColor: '#E9EDF7' }) }} />
              </div>
              <div className="form-row">
                <label>Bộ phận YC *</label>
                <input value={pr.department || ''} placeholder="Tự động theo Nhân sự" disabled />
              </div>
              <div className="form-row">
                <label>Chức vụ (Nếu có)</label>
                <input value={pr.requester_position || ''} placeholder="Tự động theo Nhân sự" disabled={!editable} onChange={(e) => setH('requester_position', e.target.value)} />
              </div>
              <div className="form-row">
                <label>Trưởng bộ phận (TBP) / Người liên hệ *</label>
                <input value={pr.head_of_dept || ''} placeholder="Tự động theo phòng ban của người yêu cầu" disabled />
              </div>
              <div className="form-row">
                <label>Tùy chọn phiếu</label>
                <div style={{ display: 'flex', gap: 20, alignItems: 'center', height: 40 }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', margin: 0, color: 'var(--navy)' }}>
                    <input type="checkbox" checked={!!pr.show_code_on_print} disabled={!editable} onChange={(e) => setH('show_code_on_print', e.target.checked)} style={{ width: 18, height: 18 }} />
                    Hiển thị Mã phiếu
                  </label>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', margin: 0, color: 'var(--red)' }}>
                    <input type="checkbox" checked={!!pr.is_urgent} disabled={!editable} onChange={(e) => setH('is_urgent', e.target.checked)} style={{ width: 18, height: 18 }} />
                    Đơn gấp
                  </label>
                </div>
              </div>
              <div className="form-row">
                <label>Mục đích mua hàng *</label>
                <textarea placeholder="Nhập mục đích mua hàng/dịch vụ..." style={{ minHeight: 80 }} value={pr.purpose || ''} disabled={!editable} onChange={(e) => setH('purpose', e.target.value)} />
              </div>
              <div className="form-row">
                <label>Nội dung mua hàng</label>
                <textarea placeholder="Nhập nội dung chi tiết..." style={{ minHeight: 80 }} value={pr.note || ''} disabled={!editable} onChange={(e) => setH('note', e.target.value)} />
              </div>
            </div>
          </div>

          {/* Mặt hàng */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 className="sec-title" style={{ margin: 0, borderBottom: 'none', paddingBottom: 0 }}>Danh sách Sản phẩm Yêu cầu</h3>
              {editable && <button className="btn ghost" onClick={() => addItems(1)} style={{ height: 30, padding: '0 10px', fontSize: 13 }}><i className="ti ti-plus" /> Thêm SP</button>}
            </div>
            <div className="items-scroll">
              <table className="items-table" style={{ minWidth: 980, tableLayout: 'fixed' }}>
                <thead>
                  <tr>
                    <th style={{ width: 34, textAlign: 'center' }}>No.</th>
                    <th style={{ width: 150, textAlign: 'left' }}>Mã hàng</th>
                    <th style={{ width: 230, textAlign: 'left' }}>Tên sản phẩm *</th>
                    <th style={{ width: 130, textAlign: 'left' }}>Kho nhận</th>
                    <th style={{ width: 140, textAlign: 'left' }}>Phân loại</th>
                    <th style={{ width: 70, textAlign: 'right' }}>SL</th>
                    <th style={{ width: 100, textAlign: 'right' }}>Đơn giá</th>
                    <th style={{ width: 110, textAlign: 'right' }}>Thành tiền</th>
                    <th style={{ width: 150, textAlign: 'center' }}>Trạng thái</th>
                    <th style={{ width: 96, textAlign: 'center' }}>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {items.map((it: any, i: number) => (
                    <tr key={i}>
                      <td>{i + 1}</td>
                      <td>
                        {editable ? (
                          <ProductPicker code={it.product_code} name={it.product_name} onPick={(prod) => applyProduct(i, prod)} />
                        ) : <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }}>{it.product_code || '—'}</span>}
                      </td>
                      <td style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={it.product_name}>
                        {it.product_name || <span style={{ color: '#bbb' }}>(mở chi tiết để nhập)</span>}
                      </td>
                      <td>
                        {editable ? (
                          <select className="cell-input" value={it.warehouse || ''} onChange={(e) => setItem(i, 'warehouse', e.target.value)} style={{ width: '100%' }}>
                            <option value="">-- Kho --</option>
                            {warehouses.map((w) => <option key={w} value={w}>{w}</option>)}
                          </select>
                        ) : <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }} title={it.warehouse}>{it.warehouse || '—'}</span>}
                      </td>
                      <td>
                        {editable ? (
                          <select className="cell-input" value={it.item_group || ''} onChange={(e) => { setItem(i, 'item_group', e.target.value); setItem(i, 'group_desc', groupDesc(e.target.value)) }} style={{ width: '100%' }}>
                            <option value="">—</option>
                            {groups.map((g) => <option key={g} value={g}>{g}</option>)}
                          </select>
                        ) : <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }} title={it.item_group}>{it.item_group || '—'}</span>}
                      </td>
                      <td style={{ textAlign: 'right' }}>{fmt(it.qty)}</td>
                      <td style={{ textAlign: 'right' }}>{fmt(it.price)}</td>
                      <td style={{ textAlign: 'right', fontWeight: 500 }}>{fmt((Number(it.qty) || 0) * (Number(it.price) || 0))}</td>
                      <td>
                        {canLineStatus(it) ? (
                          <select className="cell-input" value={it.line_status || 'Chưa đặt hàng'}
                            onChange={(e) => changeLineStatus(i, e.target.value)}
                            style={{ width: '100%', color: LS_COLOR[it.line_status] || 'var(--ink)', fontWeight: 500 }}>
                            {LINE_STATUS.map((s) => <option key={s} value={s} style={{ color: 'var(--ink)' }}>{s}</option>)}
                          </select>
                        ) : (
                          <span className="badge" style={{ background: (LS_COLOR[it.line_status] || '#94a3b8') + '22', color: LS_COLOR[it.line_status] || '#64748b' }}>{it.line_status || 'Chưa đặt hàng'}</span>
                        )}
                      </td>
                      <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                        <button className="icon-btn" title="Chi tiết" onClick={() => setEditIdx(i)}><i className="ti ti-pencil" style={{ color: 'var(--teal)' }} /></button>
                        {editable && <button className="icon-btn" title="Nhân đôi" onClick={() => copyItem(i)}><i className="ti ti-copy" style={{ color: 'var(--muted)' }} /></button>}
                        {editable && <button className="icon-btn" title="Xóa" onClick={() => delItem(i)}><i className="ti ti-trash" style={{ color: 'var(--red)' }} /></button>}
                      </td>
                    </tr>
                  ))}
                  {items.length === 0 && <tr><td colSpan={10} style={{ textAlign: 'center', color: '#999', padding: 20 }}>Chưa có sản phẩm nào</td></tr>}
                </tbody>
              </table>
            </div>
            {editable && items.length > 0 && (
              <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                <button className="btn ghost" onClick={() => addItems(Math.max(1, parseInt(prompt('Thêm bao nhiêu dòng?', '5') || '0') || 0))} style={{ height: 30, padding: '0 8px', fontSize: 12 }}><i className="ti ti-rows" /> Thêm nhiều dòng</button>
              </div>
            )}
            <div style={{ marginTop: 14, textAlign: 'right', fontSize: 15 }}>
              Tổng tiền hàng: <b style={{ color: 'var(--navy)' }}>{fmt(subtotal)} đ</b>
            </div>
          </div>

          {/* Nhà cung cấp đề xuất */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <h3 className="sec-title">Nhà cung cấp đề xuất (Nếu có)</h3>
            <div className="form-grid" style={{ marginBottom: 14 }}>
              <div className="form-row">
                <label>Tên nhà cung cấp đề xuất</label>
                <input value={pr.suggested_supplier || ''} placeholder="Nhập tên nhà cung cấp..." disabled={!editable} onChange={(e) => setH('suggested_supplier', e.target.value)} />
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
            <div style={{ borderTop: '1px solid var(--border)', paddingTop: 14 }}>
              <label style={{ fontSize: 13, color: 'var(--muted)', fontWeight: 500, display: 'block', marginBottom: 6 }}>Báo giá đính kèm (Nếu có)</label>
              {!isNew ? (
                !pr.quote_file_url ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <input type="file" id="quote-upload" style={{ display: 'none' }} disabled={!editable} onChange={(e) => uploadQuoteFile(e.target.files)} />
                    <label htmlFor="quote-upload" className="btn ghost" style={{ cursor: 'pointer', height: 32, fontSize: 13 }}><i className="ti ti-upload" /> Chọn báo giá</label>
                  </div>
                ) : (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                    <i className="ti ti-file" /><a href={pr.quote_file_url} target="_blank" style={{ color: 'var(--teal)', flex: 1, textDecoration: 'underline' }}>{pr.quote_filename}</a>
                    {editable && <button className="icon-btn" onClick={clearQuoteFile}><i className="ti ti-trash" style={{ color: 'var(--red)' }} /></button>}
                  </div>
                )
              ) : <span style={{ color: '#999', fontSize: 13 }}><i>(Tạo phiếu để đính kèm báo giá)</i></span>}
            </div>
          </div>

          {/* Chứng từ khác */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <h3 className="sec-title"><i className="ti ti-paperclip" /> Chứng từ/Tài liệu đính kèm khác</h3>
            {!isNew ? (
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                  <input type="file" id="file-upload" multiple style={{ display: 'none' }} disabled={!editable} onChange={(e) => uploadFiles(e.target.files)} />
                  <label htmlFor="file-upload" className="btn ghost" style={{ cursor: 'pointer', height: 32, fontSize: 13 }}><i className="ti ti-upload" /> Chọn file</label>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {files.map((f) => (
                    <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                      <i className="ti ti-file" /><a href={f.url} target="_blank" style={{ color: 'var(--teal)', flex: 1, textDecoration: 'underline' }}>{f.filename}</a>
                      {editable && <button className="icon-btn" onClick={async () => { if (confirm('Xóa file?')) { await api.delete(`/api/attachments/${f.id}`); loadAll() } }}><i className="ti ti-trash" style={{ color: 'var(--red)' }} /></button>}
                    </div>
                  ))}
                  {files.length === 0 && <span style={{ color: '#999', fontSize: 13 }}>Chưa có tài liệu.</span>}
                </div>
              </div>
            ) : <span style={{ color: '#999', fontSize: 13 }}><i>(Tạo phiếu để đính kèm tài liệu)</i></span>}
          </div>

          {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}
          {msg && <div style={{ color: 'var(--green)', fontSize: 13, marginTop: 8 }}>{msg}</div>}

          {editable && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20 }}>
              <button className="btn ghost" onClick={() => navigate('/purchase-requests')}>Hủy</button>
              <button className="btn secondary" onClick={() => save(false)}>Lưu nháp</button>
              <button className="btn" onClick={() => save(true)}>Lưu &amp; Gửi Duyệt</button>
            </div>
          )}
        </div>

        {isLogShown && (
          <div className="card" style={{ padding: 18 }}>
            <h3 className="sec-title"><i className="ti ti-history" /> Lịch sử thao tác</h3>
            <div className="timeline">
              {logs.map((l, i) => (
                <div key={i} className="tl-item">
                  <span className={'tl-dot ' + (l.action === 'approved' ? 'create' : (l.action === 'rejected' || l.action === 'cancelled') ? 'delete' : 'update')} />
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

      {/* Popup chi tiết dòng */}
      {edit && editIdx != null && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(27,37,89,.3)', zIndex: 200, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '4vh 12px', overflowY: 'auto' }} onClick={() => setEditIdx(null)}>
          <div className="card" style={{ width: 760, maxWidth: '100%', padding: 20 }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 className="sec-title" style={{ margin: 0, border: 0, padding: 0 }}>Chi tiết dòng #{editIdx + 1}</h3>
              <span className="clickable" style={{ color: '#94a3b8', fontSize: 18 }} onClick={() => setEditIdx(null)}><i className="ti ti-x" /></span>
            </div>
            <div className="form-grid">
              <div className="form-row">
                <label>Mã vật tư</label>
                <ProductPicker code={edit.product_code} name={edit.product_name} disabled={!editable} onPick={(prod) => applyProduct(editIdx, prod)} />
              </div>
              <div className="form-row">
                <label>Tên vật tư *</label>
                <input value={edit.product_name || ''} disabled={!editable} onChange={(e) => setItem(editIdx, 'product_name', e.target.value)} />
              </div>
              <div className="form-row">
                <label>Phân loại</label>
                <select value={edit.item_group || ''} disabled={!editable} onChange={(e) => { setItem(editIdx, 'item_group', e.target.value); setItem(editIdx, 'group_desc', groupDesc(e.target.value)) }}>
                  <option value="">—</option>
                  {groups.map((g) => <option key={g} value={g}>{g}</option>)}
                </select>
              </div>
              <div className="form-row">
                <label>Mô tả phân loại</label>
                <input value={edit.group_desc || ''} disabled placeholder="Tự động theo phân loại" />
              </div>
              <div className="form-row">
                <label>Số lượng mua *</label>
                <input type="number" value={edit.qty ?? 0} disabled={!editable} onChange={(e) => setItem(editIdx, 'qty', Number(e.target.value))} />
              </div>
              <div className="form-row">
                <label>Giá đề xuất</label>
                <input type="number" value={edit.price ?? 0} disabled={!editable} onChange={(e) => setItem(editIdx, 'price', Number(e.target.value))} />
              </div>
              <div className="form-row">
                <label>ĐVT</label>
                <select value={edit.unit || ''} disabled={!editable} onChange={(e) => setItem(editIdx, 'unit', e.target.value)}>
                  <option value="">—</option>{units.map((u) => <option key={u} value={u}>{u}</option>)}
                </select>
              </div>
              <div className="form-row">
                <label>Thành tiền</label>
                <input value={fmt((Number(edit.qty) || 0) * (Number(edit.price) || 0)) + ' đ'} disabled />
              </div>
              <div className="form-row">
                <label>Kho nhận *</label>
                <select value={edit.warehouse || ''} disabled={!editable} onChange={(e) => setItem(editIdx, 'warehouse', e.target.value)}>
                  <option value="">-- Chọn kho --</option>{warehouses.map((w) => <option key={w} value={w}>{w}</option>)}
                </select>
              </div>
              <div className="form-row">
                <label>Ngày cần hàng</label>
                <input type="date" value={edit.required_date || ''} disabled={!editable} onChange={(e) => setItem(editIdx, 'required_date', e.target.value)} />
              </div>
              {canAssignPurchaser && (
                <div className="form-row">
                  <label>Nhân sự phụ trách</label>
                  <Select value={purchaserOptions.find(o => o.value === edit.assignee) || (edit.assignee ? { value: edit.assignee, label: empName(edit.assignee) } : null)}
                    onChange={(o: any) => setItem(editIdx, 'assignee', o ? o.value : '')} options={purchaserOptions}
                    isClearable placeholder="Chọn NSTM..." styles={{ control: (b) => ({ ...b, minHeight: 40, borderRadius: 12, borderColor: '#E9EDF7' }) }} />
                </div>
              )}
              {canLineStatus(edit) && (
                <div className="form-row">
                  <label>Trạng thái xử lý</label>
                  <select value={edit.line_status || 'Chưa đặt hàng'} onChange={(e) => setItem(editIdx, 'line_status', e.target.value)}>
                    {LINE_STATUS.map((s) => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              )}
              <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                <label>Chi tiết tiến độ</label>
                <textarea value={edit.progress_note || ''} disabled={!canEditNote(edit)} onChange={(e) => setItem(editIdx, 'progress_note', e.target.value)} />
              </div>
              <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                <label>Ghi chú khác</label>
                <textarea value={edit.note || ''} disabled={!canEditNote(edit)} onChange={(e) => setItem(editIdx, 'note', e.target.value)} />
              </div>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
              <button className="btn ghost" onClick={() => setEditIdx(null)}>{editable ? 'Đóng' : 'Hủy'}</button>
              {!editable && (canLineStatus(edit) || canAssignPurchaser) && (
                <button className="btn" onClick={() => savePopupLine(items[editIdx])}><i className="ti ti-device-floppy" />Lưu dòng</button>
              )}
              {editable && <button className="btn" onClick={() => setEditIdx(null)}>Xong</button>}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
