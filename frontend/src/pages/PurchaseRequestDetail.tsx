import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { fmtDateTime } from '../utils/datetime'
import { askConfirm, askPrompt } from '../components/confirm'
import { useAuth } from '../auth/AuthContext'
import { prBadge, poBadge } from '../config/cruds'
import ProductPicker from '../components/ProductPicker'
import SearchSelect from '../components/SearchSelect'
import NumberInput from '../components/NumberInput'
import ConfirmModal from '../components/ConfirmModal'
import PromptModal from '../components/PromptModal'
import NotFound from '../components/NotFound'
import { toast } from '../components/toast'

const API = '/api/purchase-requests'
const fmt = (n: any) => Number(n || 0).toLocaleString('vi-VN')
// Hiển thị số: để TRỐNG nếu chưa nhập (0/rỗng) để tránh hiểu lầm "đã nhập = 0"
const fmtBlank = (n: any) => { const v = Number(n || 0); return v ? v.toLocaleString('vi-VN') : '' }
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
  const [warehouses, setWarehouses] = useState<{ code: string; name: string }[]>([])
  const [employees, setEmployees] = useState<any[]>([])
  const [departments, setDepartments] = useState<any[]>([])
  const [logs, setLogs] = useState<any[]>([])
  const [files, setFiles] = useState<any[]>([])
  const [editIdx, setEditIdx] = useState<number | null>(null)   // dòng đang mở popup chi tiết
  const [confirmDelete, setConfirmDelete] = useState(false)
  const [promptAction, setPromptAction] = useState<{type: 'reject'|'return'|'cancel', title: string, message: string, placeholder?: string} | null>(null)
  const [confirmAction, setConfirmAction] = useState<{type: 'complete'|'cancel_draft'|'copy', title: string, message: string, confirmText?: string} | null>(null)
  const [notFound, setNotFound] = useState(false)
  const [pos, setPos] = useState<any[] | null>(null)   // ĐMH tạo từ phiếu này (cùng mã PYC); null = chưa tải/không quyền → ẩn khối
  const [orderedMap, setOrderedMap] = useState<Record<string, number>>({})   // SL đã đặt theo mã hàng (gộp mọi ĐMH cùng PYC)
  const [poExceed, setPoExceed] = useState<{ msg: string; normal: any[]; all: any[] } | null>(null)   // popup cảnh báo đặt vượt
  const [showPoModal, setShowPoModal] = useState(false)   // popup danh sách ĐMH liên quan

  useEffect(() => {
    api.get('/api/companies', { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items)).catch(() => {})
    api.get('/api/item-groups', { params: { page_size: 500 } }).then((r) => { setItemGroups(r.data.data.items); setGroups(r.data.data.items.map((x: any) => x.name)) }).catch(() => {})
    api.get('/api/units', { params: { page_size: 200 } }).then((r) => setUnits(r.data.data.items.map((x: any) => x.name))).catch(() => {})
    api.get('/api/warehouses', { params: { page_size: 200 } }).then((r) => setWarehouses(r.data.data.items.map((x: any) => ({ code: x.code, name: x.name })))).catch(() => {})
    api.get('/api/employees', { params: { page_size: 1000 } }).then((r) => setEmployees(r.data.data.items)).catch(() => {})
    api.get('/api/departments', { params: { page_size: 500 } }).then((r) => setDepartments(r.data.data.items)).catch(() => {})
  }, [])

  async function loadAll() {
    try {
      const r = await api.get(`${API}/${id}`)
      setPr(r.data.data)
    } catch (ex: any) {
      if ([403, 404].includes(ex?.response?.status)) { setNotFound(true); return }
      throw ex
    }
    api.get('/api/audit-logs', { params: { entity: 'purchase_request', entity_id: id } }).then((x) => setLogs(x.data.data)).catch(() => {})
    api.get('/api/attachments', { params: { entity: 'purchase_request', entity_id: id } }).then((x) => setFiles(x.data.data)).catch(() => {})
  }
  useEffect(() => { if (!isNew) { setNotFound(false); loadAll() } }, [id])

  // Tải danh sách ĐMH tạo từ phiếu này (lọc theo mã PYC). Lỗi/không quyền xem ĐMH → ẩn khối.
  useEffect(() => {
    if (isNew || !pr.code) { setPos(null); return }
    api.get('/api/purchase-orders', { params: { pr_code: pr.code, page_size: 200 }, _silent: true } as any)
      .then((r) => setPos((r.data.data.items || []).slice().sort((a: any, b: any) => b.id - a.id)))
      .catch(() => setPos(null))
    // SL đã đặt theo mã hàng → prefill 'còn thiếu' + cảnh báo đặt vượt khi tạo ĐMH
    api.get(`${API}/${id}/order-progress`, { _silent: true } as any)
      .then((r) => setOrderedMap(r.data.data.ordered || {}))
      .catch(() => setOrderedMap({}))
  }, [isNew, pr.code])

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
  // Nút "Tạo ĐMH" chỉ hiện cho phòng thu mua / quản lý / admin (và có quyền tạo ĐMH)
  const isPurchaserDept = ((user as any)?.department_name || '').toLowerCase().includes('thu mua')
  const canCreatePO = can('purchase_order', 'create') && (isPurchaserDept || canManage || canAssignPurchaser)
  // Còn dòng nào chưa đặt hàng → vẫn cho tạo ĐMH (không ẩn khi mới hoàn thành 1 dòng)
  const hasUnorderedItem = (pr.items || []).some((it: any) => (it.line_status || 'Chưa đặt hàng') === 'Chưa đặt hàng')
  // Cột/trường "NSTM phụ trách" chỉ cho phía thu mua (is_purchaser = có quyền xử lý khảo sát).
  // Ẩn hoàn toàn với người yêu cầu (NSYC/employee) & trưởng bộ phận của họ (dept_head).
  const showAssigneeCol = can('survey_request', 'process')
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
  const companyOptions = companies.map(c => ({ value: String(c.id), label: c.name }))
  const employeeOptions = employees.map(e => ({ value: e.full_name, label: e.full_name }))
  const warehouseOptions = warehouses.map(w => ({ value: w.name, label: `${w.code} - ${w.name}` }))
  // Nhãn hiển thị "MÃ - Tên" cho kho đã lưu (giá trị lưu vẫn là name); fallback name nếu không tìm thấy
  const whLabel = (name: string) => { const w = warehouses.find(w => w.name === name); return w ? `${w.code} - ${w.name}` : name }

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
      try { await api.patch(`${API}/${id}/item-status`, { items: [{ id: it.id, line_status: val }] }); toast.success('Đã cập nhật trạng thái'); loadAll() }
      catch { loadAll() /* interceptor đã toast lỗi */ }
    }
  }

  // Đổi NSTM phụ trách ngay trên bảng ngoài (chỉ người có quyền duyệt). Phiếu đã lưu -> auto-lưu; phiếu nháp -> theo nút Lưu.
  async function changeAssignee(i: number, val: string) {
    setItem(i, 'assignee', val)
    const it = items[i]
    if (!editable && it.id && canAssignPurchaser) {
      try { await api.patch(`${API}/${id}/assign`, { items: [{ id: it.id, assignee: val || '' }] }); toast.success('Đã cập nhật NSTM phụ trách'); loadAll() }
      catch (ex: any) { toast.error(ex?.response?.data?.error?.message || 'Lỗi cập nhật NSTM'); loadAll() }
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
      const r = await api.post('/api/attachments', fd)
      const f = r.data.data[0]
      setPr((s: any) => ({ ...s, quote_filename: f.filename, quote_file_url: f.url }))
      toast.success('Đã tải lên báo giá')
    } catch { /* interceptor đã toast lỗi */ }
  }
  const clearQuoteFile = () => setPr((s: any) => ({ ...s, quote_filename: '', quote_file_url: '' }))

  function validate(forSubmit: boolean): string {
    if (!pr.company_id) return 'Vui lòng chọn Công ty'
    if (!pr.requester) return 'Vui lòng chọn Nhân sự yêu cầu'
    const valid = items.filter((it: any) => it.product_name)
    if (valid.length === 0) return 'Cần ít nhất 1 sản phẩm'
    // Chi tiết bắt buộc (mã hàng/SL/kho/ngày cần hàng) CHỈ khi Gửi duyệt — lưu nháp / đóng popup dòng thì không bắt
    if (forSubmit) {
      for (const it of valid) {
        if (!it.product_code) return `Sản phẩm "${it.product_name}" cần chọn Mã hàng (chọn từ danh mục)`
        if (!(Number(it.qty) > 0)) return `Sản phẩm "${it.product_name}" cần Số lượng > 0`
        if (!it.warehouse) return `Sản phẩm "${it.product_name}" cần chọn Kho nhận`
        if (!it.required_date) return `Sản phẩm "${it.product_name}" cần nhập Ngày cần hàng`
      }
    }
    return ''
  }

  async function save(submitAfterSave = false): Promise<boolean> {
    const v = validate(submitAfterSave)
    if (v) { toast.error(v); return false }
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
        toast.success('Đã lưu'); loadAll()
      }
      return true
    } catch { /* interceptor đã toast lỗi */ return false }
  }

  async function action(path: string, payload: any = {}) {
    try { await api.post(`${API}/${id}/${path}`, payload); loadAll() }
    catch { /* interceptor đã toast lỗi */ }
  }

  async function copyDoc() {
    try { const r = await api.post(`${API}/${id}/copy`); navigate(`/purchase-requests/${r.data.data.id}`) }
    catch { /* interceptor đã toast lỗi */ }
  }

  // Điều hướng sang form ĐMH mới với header từ phiếu + danh sách dòng đã tính sẵn
  function goPO(items: any[]) {
    const fromPr = {
      pr_code: pr.code,
      company_id: pr.company_id,
      department: pr.department,
      nspt: pr.requester,                       // khớp cách onPickPr bên ĐMH lấy NSPT = người yêu cầu
      supplier_name: pr.suggested_supplier || '',
      supplier_code: '',                        // PR chỉ có tên NCC đề xuất, không có mã
      vat_rate: Number(pr.vat_rate) || 0.08,
      is_urgent: !!pr.is_urgent,
      note: pr.note || '',
      items,
    }
    navigate('/purchase-orders/new', { state: { fromPr } })
  }

  // Tạo ĐMH từ phiếu đã duyệt: prefill SL theo 'còn thiếu' (yêu cầu − đã đặt), cảnh báo dòng đã đặt đủ/vượt
  function createPO() {
    const whCode = (name: string) => warehouses.find((w) => w.name === name)?.code || ''
    const vatPct = Math.round((Number(pr.vat_rate) || 0.08) * 100)   // PR chỉ có vat_rate ở header → quy về % cho từng dòng ĐMH
    const mk = (it: any, qty: number) => ({
      product_code: it.product_code, product_name: it.product_name,
      item_group: it.item_group, unit: it.unit,
      qty_request: qty, qty_order: qty,
      price: Number(it.price) || 0, vat: vatPct,
      warehouse_code: whCode(it.warehouse), note: it.note || '',
    })
    const lines = (pr.items || []).filter((it: any) => it.product_name && it.line_status !== 'Hủy đơn')
    const normal: any[] = [], exceeded: any[] = [], exceededMsg: string[] = []
    for (const it of lines) {
      const req = Number(it.qty) || 0
      const ordered = Number(orderedMap[it.product_code] || 0)
      const remaining = req - ordered
      if (remaining > 0) normal.push(mk(it, remaining))
      else { exceeded.push(mk(it, req)); exceededMsg.push(`${it.product_name} (đã đặt ${fmt(ordered)}/${fmt(req)})`) }
    }
    if (exceeded.length === 0) { goPO(normal); return }
    // Có dòng đã đặt đủ/vượt → cảnh báo, cho chọn mua thêm hay chỉ SP còn thiếu
    setPoExceed({ msg: exceededMsg.join('; '), normal, all: [...normal, ...exceeded] })
  }

  async function handleDelete() {
    try {
      await api.delete(`${API}?ids=${id}`)
      navigate('/purchase-requests')
    } catch { /* interceptor đã toast lỗi */ }
  }

  // Lưu popup chi tiết dòng khi phiếu KHÔNG còn ở trạng thái sửa (đã gửi duyệt trở đi)
  async function savePopupLine(it: any) {
    try {
      if (canLineStatus(it))
        await api.patch(`${API}/${id}/item-status`, { items: [{ id: it.id, line_status: it.line_status, progress_note: it.progress_note, note: it.note }] })
      if (canAssignPurchaser)
        await api.patch(`${API}/${id}/assign`, { items: [{ id: it.id, assignee: it.assignee || '' }] })
      toast.success('Đã cập nhật dòng'); setEditIdx(null); loadAll()
    } catch { /* interceptor đã toast lỗi */ }
  }

  async function uploadFiles(fl: FileList | null) {
    if (!fl?.length) return
    const fd = new FormData(); fd.append('entity', 'purchase_request'); fd.append('entity_id', String(id))
    Array.from(fl).forEach((f) => fd.append('files', f))
    try { await api.post('/api/attachments', fd); loadAll() }
    catch { /* interceptor đã toast lỗi */ }
  }

  const isLogShown = !isNew && logs.length > 0
  const edit = editIdx != null ? items[editIdx] : null

  if (notFound) return <NotFound backTo="/purchase-requests" message="Không tìm thấy phiếu yêu cầu mua hàng này hoặc bạn không có quyền truy cập." />

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate('/purchase-requests')}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>{isNew ? 'Tạo Yêu cầu Thu mua mới' : (pr.code || '')}</h2>
        {!isNew && prBadge(pr.status)}
        <span style={{ flex: 1 }} />
        {/* ── Nhóm tiện ích + destructive (trái) ── */}
        {!isNew && <button className="btn ghost" onClick={() => window.open(`/print/purchase-request/${id}`, '_blank')}><i className="ti ti-printer" />In phiếu</button>}
        {!isNew && pos && pos.length > 0 && <button className="btn ghost" onClick={() => setShowPoModal(true)}><i className="ti ti-shopping-cart" />ĐMH liên quan ({pos.length})</button>}
        {!isNew && can('purchase_request', 'create') && <button className="btn ghost" onClick={() => setConfirmAction({ type: 'copy', title: 'Nhân bản', message: 'Nhân bản phiếu này thành phiếu Nháp mới?', confirmText: 'Nhân bản' })}><i className="ti ti-copy" />Nhân bản</button>}
        {!isNew && pr.status === 'draft' && can('purchase_request', 'delete') && (
          <button className="btn ghost err" onClick={() => setConfirmDelete(true)}><i className="ti ti-trash" />Xóa phiếu</button>
        )}
        {!isNew && <span style={{ width: 1, alignSelf: 'stretch', background: 'var(--border)', margin: '2px 4px' }} />}
        {/* ── Nhóm workflow + chính (phải): Duyệt · Trả về · Từ chối cùng nhóm ── */}
        {editable && (
          <button className="btn secondary" onClick={() => save(false)}><i className="ti ti-device-floppy" />Lưu</button>
        )}
        {editable && (
          <button className="btn" onClick={() => save(true)}><i className="ti ti-send" />Gửi duyệt</button>
        )}
        {!isNew && pr.status === 'submitted' && can('purchase_request', 'approve') && (
          <button className="btn" onClick={() => action('approve')}><i className="ti ti-check" />Duyệt</button>
        )}
        {!isNew && (canManage || (pr.status === 'submitted' && can('purchase_request', 'approve'))) && !['draft', 'rejected', 'cancelled', 'completed', 'done'].includes(pr.status) && (
          <button className="btn ghost" style={{ color: '#d97706', borderColor: '#fcd34d' }} onClick={() => setPromptAction({ type: 'return', title: 'Trả về', message: 'Lý do trả về (để người yêu cầu sửa & gửi duyệt lại):' })}><i className="ti ti-corner-up-left" />Trả về</button>
        )}
        {!isNew && pr.status === 'submitted' && can('purchase_request', 'approve') && (
          <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={() => setPromptAction({ type: 'cancel', title: 'Từ chối phiếu', message: 'Lý do từ chối (khóa phiếu, không sửa lại được):' })}><i className="ti ti-ban" />Từ chối</button>
        )}
        {!isNew && canCreatePO && ['approved', 'processing'].includes(pr.status) && hasUnorderedItem && (
          <button className="btn" onClick={createPO}><i className="ti ti-shopping-cart" />Tạo đơn mua hàng</button>
        )}
        {!isNew && canManage && ['approved', 'processing'].includes(pr.status) && (
          <button className="btn secondary" onClick={() => setConfirmAction({ type: 'complete', title: 'Hoàn thành', message: 'Đánh dấu phiếu HOÀN THÀNH?', confirmText: 'Đồng ý' })}><i className="ti ti-checks" />Hoàn thành</button>
        )}
        {/* ── Từ chối (khóa phiếu) ở giai đoạn đã duyệt/đang xử lý ── */}
        {!isNew && canManage && !['draft', 'submitted', 'rejected', 'cancelled', 'completed', 'done'].includes(pr.status) && (
          <>
            <span style={{ width: 1, alignSelf: 'stretch', background: 'var(--border)', margin: '2px 4px' }} />
            <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={() => setPromptAction({ type: 'cancel', title: 'Từ chối phiếu', message: 'Lý do từ chối (khóa phiếu):' })}><i className="ti ti-ban" />Từ chối</button>
          </>
        )}
      </div>

      <PromptModal
        open={!!promptAction}
        title={promptAction?.title}
        message={promptAction?.message || ''}
        placeholder={promptAction?.placeholder}
        confirmText="Xác nhận"
        cancelText="Đóng"
        variant="danger"
        onConfirm={(reason) => {
          if (promptAction && reason !== null) {
            action(promptAction.type, { reason })
          }
          setPromptAction(null)
        }}
        onCancel={() => setPromptAction(null)}
      />

      <ConfirmModal
        open={!!confirmAction}
        title={confirmAction?.title}
        message={confirmAction?.message || ''}
        confirmText={confirmAction?.confirmText || "Xác nhận"}
        cancelText="Đóng"
        variant={confirmAction?.type === 'complete' ? 'info' : 'warn'}
        onConfirm={() => {
          if (confirmAction?.type === 'complete') action('complete')
          if (confirmAction?.type === 'cancel_draft') action('cancel', { reason: '' })
          if (confirmAction?.type === 'copy') copyDoc()
          setConfirmAction(null)
        }}
        onCancel={() => setConfirmAction(null)}
      />

      <ConfirmModal
        open={!!poExceed}
        title="Số lượng đã đặt đủ/vượt"
        message={`Các sản phẩm sau đã đặt đủ hoặc vượt số lượng yêu cầu: ${poExceed?.msg || ''}. Bạn vẫn muốn tạo đơn mua hàng?`}
        confirmText="Vẫn mua thêm"
        cancelText="Chỉ SP còn thiếu"
        variant="warn"
        onConfirm={() => { const p = poExceed; setPoExceed(null); if (p) goPO(p.all) }}
        onCancel={() => { const p = poExceed; setPoExceed(null); if (p) { if (p.normal.length) goPO(p.normal); else toast.info('Không còn sản phẩm cần đặt') } }}
      />

      <ConfirmModal
        open={confirmDelete}
        title="Xác nhận xóa"
        message="Bạn có chắc chắn muốn xóa phiếu mua hàng này không?"
        confirmText="Xóa"
        cancelText="Hủy"
        variant="danger"
        onConfirm={() => { setConfirmDelete(false); handleDelete(); }}
        onCancel={() => setConfirmDelete(false)}
      />

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
              {!isNew && (
                <div className="form-row">
                  <label>Ngày tạo</label>
                  <input value={fmtDateTime(pr.created_at) || '—'} disabled />
                </div>
              )}
              <div className="form-row">
                <label>Ngày tiếp nhận <span className="req">*</span></label>
                <input type="date" value={pr.request_date || ''} disabled={!editable} onChange={(e) => setH('request_date', e.target.value)} />
              </div>
              <div className="form-row">
                <label>Công ty nhận hóa đơn <span className="req">*</span></label>
                <SearchSelect value={String(pr.company_id || '')}
                  onChange={(v) => setH('company_id', Number(v) || 0)} options={companyOptions}
                  disabled={!editable} placeholder="Chọn công ty" />
              </div>
              <div className="form-row">
                <label>Nhân sự YC <span className="req">*</span></label>
                <SearchSelect value={pr.requester || ''}
                  onChange={(v) => handleRequesterChange(v)} options={employeeOptions}
                  disabled={!editable || isStaff} placeholder="Chọn nhân sự" />
              </div>
              <div className="form-row">
                <label>Bộ phận YC <span className="req">*</span></label>
                <input value={pr.department || ''} placeholder="Tự động theo Nhân sự" disabled />
              </div>
              <div className="form-row">
                <label>Chức vụ (Nếu có)</label>
                <input value={pr.requester_position || ''} placeholder="Tự động theo Nhân sự" disabled={!editable} onChange={(e) => setH('requester_position', e.target.value)} />
              </div>
              <div className="form-row">
                <label>Trưởng bộ phận (TBP) / Người liên hệ <span className="req">*</span></label>
                <input value={pr.head_of_dept || ''} placeholder="Tự động theo phòng ban của người yêu cầu" disabled />
              </div>
              <div className="form-row">
                <label>Tùy chọn phiếu</label>
                <div style={{ display: 'flex', gap: 20, alignItems: 'center', height: 40 }}>
                  <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', margin: 0, color: 'var(--red)' }}>
                    <input type="checkbox" checked={!!pr.is_urgent} disabled={!editable} onChange={(e) => setH('is_urgent', e.target.checked)} style={{ width: 18, height: 18 }} />
                    Đơn gấp
                  </label>
                </div>
              </div>
              <div className="form-row">
                <label>Mục đích mua hàng <span className="req">*</span></label>
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
              <table className="items-table" style={{ minWidth: showAssigneeCol ? 1220 : 1060, tableLayout: 'fixed' }}>
                <thead>
                  <tr>
                    <th style={{ width: 34, textAlign: 'center' }}>No.</th>
                    <th style={{ width: 150, textAlign: 'left' }}>Mã hàng *</th>
                    <th style={{ width: 230, textAlign: 'left' }}>Tên sản phẩm *</th>
                    <th style={{ width: 130, textAlign: 'left' }}>Kho nhận</th>
                    <th style={{ width: 140, textAlign: 'left' }}>Phân loại</th>
                    <th style={{ width: 80, textAlign: 'left' }}>ĐVT</th>
                    <th style={{ width: 70, textAlign: 'right' }}>SL</th>
                    <th style={{ width: 100, textAlign: 'right' }}>Đơn giá</th>
                    <th style={{ width: 110, textAlign: 'right' }}>Thành tiền</th>
                    <th style={{ width: 150, textAlign: 'center' }}>Trạng thái</th>
                    {showAssigneeCol && <th style={{ width: 160, textAlign: 'left' }}>NSTM phụ trách</th>}
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
                      <td style={{ overflow: 'hidden' }} title={it.product_name}>
                        {editable ? (
                          <input className="cell-input" value={it.product_name || ''} placeholder="Nhập tên sản phẩm" onChange={(e) => setItem(i, 'product_name', e.target.value)} style={{ width: '100%' }} />
                        ) : <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }}>{it.product_name || ''}</span>}
                      </td>
                      <td>
                        {editable ? (
                          <select className="cell-input" value={it.warehouse || ''} onChange={(e) => setItem(i, 'warehouse', e.target.value)} style={{ width: '100%' }}>
                            <option value="">-- Kho --</option>
                            {warehouses.map((w) => <option key={w.name} value={w.name}>{w.code} - {w.name}</option>)}
                          </select>
                        ) : <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }} title={whLabel(it.warehouse)}>{it.warehouse ? whLabel(it.warehouse) : ''}</span>}
                      </td>
                      <td>
                        {editable ? (
                          <select className="cell-input" value={it.item_group || ''} onChange={(e) => { setItem(i, 'item_group', e.target.value); setItem(i, 'group_desc', groupDesc(e.target.value)) }} style={{ width: '100%' }}>
                            <option value="">-- Phân loại --</option>
                            {groups.map((g) => <option key={g} value={g}>{g}</option>)}
                          </select>
                        ) : <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }} title={it.item_group}>{it.item_group || ''}</span>}
                      </td>
                      <td>
                        {editable ? (
                          <select className="cell-input" value={it.unit || ''} onChange={(e) => setItem(i, 'unit', e.target.value)} style={{ width: '100%' }}>
                            <option value="">-- ĐVT --</option>
                            {units.map((u) => <option key={u} value={u}>{u}</option>)}
                          </select>
                        ) : <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }} title={it.unit}>{it.unit || ''}</span>}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        {editable ? (
                          <NumberInput decimals value={it.qty} onChange={(v) => setItem(i, 'qty', v)} className="cell-input" style={{ width: '100%', textAlign: 'right' }} placeholder="0" />
                        ) : fmtBlank(it.qty)}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        {editable ? (
                          <NumberInput value={it.price} onChange={(v) => setItem(i, 'price', v)} className="cell-input" style={{ width: '100%', textAlign: 'right' }} placeholder="0" />
                        ) : fmtBlank(it.price)}
                      </td>
                      <td style={{ textAlign: 'right', fontWeight: 500 }}>{fmtBlank((Number(it.qty) || 0) * (Number(it.price) || 0))}</td>
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
                      {showAssigneeCol && (
                        <td style={{ overflow: 'hidden' }}>
                          {canAssignPurchaser ? (
                            <select className="cell-input" value={it.assignee || ''} onChange={(e) => changeAssignee(i, e.target.value)} style={{ width: '100%' }}>
                              <option value="">-- Chọn NSTM --</option>
                              {purchaserOptions.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                            </select>
                          ) : <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }} title={empName(it.assignee)}>{it.assignee ? empName(it.assignee) : ''}</span>}
                        </td>
                      )}
                      <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                        <button className="icon-btn" title="Chi tiết" onClick={() => setEditIdx(i)}><i className="ti ti-pencil" style={{ color: 'var(--teal)' }} /></button>
                        {editable && <button className="icon-btn" title="Nhân đôi" onClick={() => copyItem(i)}><i className="ti ti-copy" style={{ color: 'var(--muted)' }} /></button>}
                        {editable && <button className="icon-btn" title="Xóa" onClick={() => delItem(i)}><i className="ti ti-trash" style={{ color: 'var(--red)' }} /></button>}
                      </td>
                    </tr>
                  ))}
                  {items.length === 0 && <tr><td colSpan={showAssigneeCol ? 12 : 11} style={{ textAlign: 'center', color: '#999', padding: 20 }}>Chưa có sản phẩm nào</td></tr>}
                </tbody>
              </table>
            </div>
            {editable && items.length > 0 && (
              <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                <button className="btn ghost" onClick={async () => { const n = await askPrompt({ message: 'Thêm bao nhiêu dòng?', defaultValue: '5' }); if (n !== null) addItems(Math.max(1, parseInt(n || '0') || 0)) }} style={{ height: 30, padding: '0 8px', fontSize: 12 }}><i className="ti ti-rows" /> Thêm nhiều dòng</button>
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
                  editable ? (
                    <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                      <input type="file" id="quote-upload" style={{ display: 'none' }} disabled={!editable} onChange={(e) => uploadQuoteFile(e.target.files)} />
                      <label htmlFor="quote-upload" className="btn ghost" style={{ cursor: 'pointer', height: 32, fontSize: 13 }}><i className="ti ti-upload" /> Chọn báo giá</label>
                    </div>
                  ) : <span style={{ color: '#999', fontSize: 13 }}><i>(Chưa có báo giá)</i></span>
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
                {editable && (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 8 }}>
                    <input type="file" id="file-upload" multiple style={{ display: 'none' }} disabled={!editable} onChange={(e) => uploadFiles(e.target.files)} />
                    <label htmlFor="file-upload" className="btn ghost" style={{ cursor: 'pointer', height: 32, fontSize: 13 }}><i className="ti ti-upload" /> Chọn file</label>
                  </div>
                )}
                <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                  {files.map((f) => (
                    <div key={f.id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 13 }}>
                      <i className="ti ti-file" /><a href={f.url} target="_blank" style={{ color: 'var(--teal)', flex: 1, textDecoration: 'underline' }}>{f.filename}</a>
                      {editable && <button className="icon-btn" onClick={async () => { if (await askConfirm({ message: 'Xóa file?' })) { await api.delete(`/api/attachments/${f.id}`); loadAll() } }}><i className="ti ti-trash" style={{ color: 'var(--red)' }} /></button>}
                    </div>
                  ))}
                  {files.length === 0 && <span style={{ color: '#999', fontSize: 13 }}>Chưa có tài liệu.</span>}
                </div>
              </div>
            ) : <span style={{ color: '#999', fontSize: 13 }}><i>(Tạo phiếu để đính kèm tài liệu)</i></span>}
          </div>



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
                    <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>{fmtDateTime(l.at)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Popup danh sách Đơn mua hàng liên quan (cùng mã PYC) */}
      {showPoModal && pos && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(27,37,89,.3)', zIndex: 200, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '4vh 12px', overflowY: 'auto' }}
          onClick={() => setShowPoModal(false)}>
          <div className="card" style={{ width: 860, maxWidth: '100%', padding: 20 }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 className="sec-title" style={{ margin: 0, border: 0, padding: 0 }}>Đơn mua hàng liên quan ({pos.length})</h3>
              <span className="clickable" style={{ color: '#94a3b8', fontSize: 18 }} onClick={() => setShowPoModal(false)}><i className="ti ti-x" /></span>
            </div>
            <div style={{ maxHeight: '70vh', overflowY: 'auto' }}>
              <table className="items-table" style={{ width: '100%' }}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Mã PO</th>
                    <th style={{ textAlign: 'left' }}>NCC</th>
                    <th style={{ textAlign: 'right' }}>Tổng tiền</th>
                    <th style={{ textAlign: 'center', width: 150 }}>Trạng thái</th>
                  </tr>
                </thead>
                <tbody>
                  {pos.map((po: any) => (
                    <tr key={po.id}>
                      <td>
                        <span className="clickable" style={{ color: 'var(--teal)', fontWeight: 500, cursor: 'pointer' }}
                          onClick={() => navigate(`/purchase-orders/${po.id}`)}>{po.code || `#${po.id}`}</span>
                      </td>
                      <td>{po.supplier_name || po.supplier_code || ''}</td>
                      <td style={{ textAlign: 'right' }}>{fmtBlank(po.amount)}</td>
                      <td style={{ textAlign: 'center' }}>{poBadge(po.status)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
              <button className="btn ghost" onClick={() => navigate(`/purchase-orders?pr_code=${encodeURIComponent(pr.code)}`)}><i className="ti ti-external-link" />Mở trang Đơn mua hàng</button>
              <button className="btn" onClick={() => setShowPoModal(false)}>Đóng</button>
            </div>
          </div>
        </div>
      )}

      {/* Popup chi tiết dòng */}
      {edit && editIdx != null && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(27,37,89,.3)', zIndex: 200, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '4vh 12px', overflowY: 'auto' }}>
          <div className="card" style={{ width: 760, maxWidth: '100%', padding: 20 }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 className="sec-title" style={{ margin: 0, border: 0, padding: 0 }}>Chi tiết dòng #{editIdx + 1}</h3>
              <span className="clickable" style={{ color: '#94a3b8', fontSize: 18 }} onClick={() => setEditIdx(null)}><i className="ti ti-x" /></span>
            </div>
            <div className="form-grid">
              <div className="form-row">
                <label>Mã vật tư <span className="req">*</span></label>
                <ProductPicker code={edit.product_code} name={edit.product_name} disabled={!editable} onPick={(prod) => applyProduct(editIdx, prod)} />
              </div>
              <div className="form-row">
                <label>Tên vật tư <span className="req">*</span></label>
                <input value={edit.product_name || ''} disabled={!editable} onChange={(e) => setItem(editIdx, 'product_name', e.target.value)} />
              </div>
              <div className="form-row">
                <label>Phân loại</label>
                <SearchSelect value={edit.item_group || ''} options={groups} disabled={!editable} placeholder="Chọn/tìm phân loại…"
                  onChange={(v) => { setItem(editIdx, 'item_group', v); setItem(editIdx, 'group_desc', groupDesc(v)) }} />
              </div>
              <div className="form-row">
                <label>Mô tả phân loại</label>
                <input value={edit.group_desc || ''} disabled placeholder="Tự động theo phân loại" />
              </div>
              <div className="form-row">
                <label>Số lượng mua <span className="req">*</span></label>
                <NumberInput decimals value={edit.qty} onChange={(v) => setItem(editIdx, 'qty', v)} disabled={!editable} placeholder="Nhập số lượng" />
              </div>
              <div className="form-row">
                <label>Giá đề xuất</label>
                <NumberInput value={edit.price} onChange={(v) => setItem(editIdx, 'price', v)} disabled={!editable} placeholder="Để trống nếu chưa có giá" />
              </div>
              <div className="form-row">
                <label>ĐVT</label>
                <SearchSelect value={edit.unit || ''} options={units} disabled={!editable} placeholder="Chọn/tìm ĐVT…" onChange={(v) => setItem(editIdx, 'unit', v)} />
              </div>
              <div className="form-row">
                <label>Thành tiền</label>
                <input value={(() => { const v = (Number(edit.qty) || 0) * (Number(edit.price) || 0); return v ? fmt(v) + ' đ' : '' })()} placeholder="—" disabled />
              </div>
              <div className="form-row">
                <label>Kho nhận <span className="req">*</span></label>
                <SearchSelect value={edit.warehouse || ''} options={warehouseOptions} disabled={!editable} placeholder="Chọn/tìm kho…" onChange={(v) => setItem(editIdx, 'warehouse', v)} />
              </div>
              <div className="form-row">
                <label>Ngày cần hàng <span className="req">*</span></label>
                <input type="date" value={edit.required_date || ''} disabled={!editable} onChange={(e) => setItem(editIdx, 'required_date', e.target.value)} />
              </div>
              {showAssigneeCol && (
                <div className="form-row">
                  <label>Nhân sự phụ trách</label>
                  <SearchSelect value={edit.assignee || ''} disabled={!canAssignPurchaser}
                    onChange={(v) => setItem(editIdx, 'assignee', v)} options={purchaserOptions}
                    placeholder={canAssignPurchaser ? 'Chọn NSTM...' : ''} />
                </div>
              )}
              <div className="form-row">
                <label>Trạng thái xử lý</label>
                <select value={edit.line_status || 'Chưa đặt hàng'} disabled={!canLineStatus(edit)} onChange={(e) => setItem(editIdx, 'line_status', e.target.value)}>
                  {LINE_STATUS.map((s) => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
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
              {editable && <button className="btn" onClick={async () => { const ok = await save(false); if (ok) setEditIdx(null) }}><i className="ti ti-device-floppy" />Xong</button>}
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
