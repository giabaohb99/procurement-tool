import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { fmtDateTime } from '../utils/datetime'
import { askConfirm, askPrompt } from '../components/confirm'
import { useAuth } from '../auth/AuthContext'
import { prBadge } from '../config/cruds'
import Select from 'react-select'
import SearchSelect from '../components/SearchSelect'
import { toast } from '../components/toast'
import NotFound from '../components/NotFound'

const API = '/api/survey-requests'

// Hiển thị số: để TRỐNG nếu chưa nhập (0/rỗng)
const fmtBlank = (n: any) => { const v = Number(n || 0); return v ? v.toLocaleString('vi-VN') : '' }

// Parse chuỗi số kiểu VN (bỏ dấu chấm ngăn nghìn, dấu phẩy = thập phân)
const parseVN = (s: string) => {
  const c = String(s).replace(/\./g, '').replace(/\s/g, '').replace(',', '.').replace(/[^\d.]/g, '')
  return c === '' ? 0 : Number(c)
}
// Ô nhập số: hiển thị 3.000 khi không focus, cho gõ tự do khi focus
function NumberInput({ value, onChange, disabled, placeholder, className, style }: any) {
  const [foc, setFoc] = useState(false)
  const [raw, setRaw] = useState('')
  const shown = foc ? raw : (Number(value) ? Number(value).toLocaleString('vi-VN') : '')
  return (
    <input type="text" inputMode="decimal" disabled={disabled} placeholder={placeholder} value={shown}
      className={className} style={style}
      onFocus={() => { setRaw(value ? String(value).replace('.', ',') : ''); setFoc(true) }}
      onBlur={() => setFoc(false)}
      onChange={(e) => { setRaw(e.target.value); onChange(parseVN(e.target.value)) }} />
  )
}

// Đính kèm là ảnh? (theo content_type hoặc đuôi file)
const isImageAtt = (a: any) =>
  (a?.content_type || '').startsWith('image/') || /\.(png|jpe?g|webp|gif)$/i.test(a?.filename || '')

// Cặp nhãn:giá trị nhỏ gọn cho thẻ option
function Field({ label, value, strong }: any) {
  return (
    <div>
      <span style={{ color: 'var(--muted)' }}>{label}: </span>
      <span style={{ fontWeight: strong ? 700 : 400 }}>{(value ?? '') === '' ? '—' : value}</span>
    </div>
  )
}

const SR_STATUS: Record<string, { label: string; cls: string }> = {
  draft:       { label: 'Nháp',         cls: 'gray' },
  submitted:   { label: 'Chờ duyệt',    cls: 'warn' },
  approved:    { label: 'Đã duyệt',     cls: 'ok'   },
  rejected:    { label: 'Bị trả lại',   cls: 'warn' },
  cancelled:   { label: 'Đã từ chối',   cls: 'err'  },
  processing:  { label: 'Đang xử lý',   cls: 'warn' },
  survey_done: { label: 'Đã khảo sát',  cls: 'ok'   },
  pr_created:  { label: 'Đã tạo YCMH',  cls: 'warn' },
  done:        { label: 'Hoàn thành',   cls: 'ok'   },
}

const srBadge = (st: string) => {
  const s = SR_STATUS[String(st || '').toLowerCase()] || { label: st, cls: 'gray' }
  return <span className={'badge ' + s.cls}>{s.label}</span>
}

// Tình trạng DÒNG — tự suy theo tiến trình (không chỉnh tay)
const srLineStatus = (l: any): { label: string; cls: string } => {
  if (l.is_completed) return { label: 'Hoàn thành', cls: 'ok' }
  if (l.has_chosen)   return { label: 'Đã chọn PA', cls: 'ok' }
  if ((l.option_count || 0) > 0) return { label: 'Đã khảo sát', cls: 'warn' }
  return { label: 'Chưa xong', cls: 'gray' }
}

const emptyLine = {
  received_date: '',
  result_due_date: '',
  item_group: '',
  requirement_detail: '',
  other_requirement: '',
  request_qty: 0,
  uom: '',
  proposed_price: 0,
}

export default function SurveyRequestDetail() {
  const { id } = useParams()
  const isNew = id === 'new'
  const { user, can } = useAuth()
  const navigate = useNavigate()

  const [sv, setSv] = useState<any>({
    code: '', company_id: 0, requester: '', requester_position: '',
    department: '', head_of_dept: '', purpose: '',
    request_date: new Date().toISOString().slice(0, 10),
    note: '', status: 'draft', reject_reason: '', lines: [],
  })
  const [companies, setCompanies]   = useState<any[]>([])
  const [departments, setDepartments] = useState<any[]>([])
  const [employees, setEmployees]   = useState<any[]>([])
  const [itemGroups, setItemGroups] = useState<any[]>([])
  const [units, setUnits]           = useState<string[]>([])
  const [logs, setLogs]             = useState<any[]>([])
  const [editIdx, setEditIdx]       = useState<number | null>(null)
  const [notFound, setNotFound]     = useState(false)

  // --- load lookups once ---
  useEffect(() => {
    api.get('/api/companies',   { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items)).catch(() => {})
    api.get('/api/departments', { params: { page_size: 500 } }).then((r) => setDepartments(r.data.data.items)).catch(() => {})
    api.get('/api/employees',   { params: { page_size: 1000 } }).then((r) => setEmployees(r.data.data.items)).catch(() => {})
    api.get('/api/item-groups', { params: { page_size: 500 } }).then((r) => setItemGroups(r.data.data.items)).catch(() => {})
    api.get('/api/units',       { params: { page_size: 200 } }).then((r) => setUnits(r.data.data.items.map((x: any) => x.name))).catch(() => {})
  }, [])

  // --- load document ---
  async function loadAll() {
    try {
      const r = await api.get(`${API}/${id}`)
      setSv(r.data.data)
      api.get('/api/audit-logs', { params: { entity: 'survey_request', entity_id: id } })
        .then((x) => setLogs(x.data.data)).catch(() => {})
    } catch (ex: any) {
      const status = ex?.response?.status
      if (status === 403 || status === 404) { setNotFound(true); return }
      throw ex
    }
  }
  useEffect(() => { if (!isNew) { setNotFound(false); loadAll() } }, [id])

  // Nạp hình đính kèm khi mở popup chi tiết dòng
  useEffect(() => {
    const ln = editIdx != null ? (sv.lines || [])[editIdx] : null
    if (ln && ln.id) loadLineFiles(ln.id); else setLineFiles([])
  }, [editIdx])

  // --- auto-fill người yêu cầu từ user đăng nhập (chỉ khi tạo mới) ---
  useEffect(() => {
    if (!isNew || !user || sv.requester) return
    if (employees.length > 0) {
      const matchEmp = employees.find((e) => e.email === user.email || e.full_name === user.full_name)
      if (matchEmp) { handleRequesterChange(matchEmp.full_name, true); return }
    }
    if (isStaff) {
      setSv((s: any) => ({
        ...s,
        requester: (user as any).full_name || '',
        requester_id: (user as any).employee_id || 0,
        requester_position: user.role_name || user.position || s.requester_position,
        department: (user as any).department_name || s.department,
        company_id: (user as any).company_id || s.company_id,
      }))
    }
  }, [isNew, employees, user])

  // --- auto-fill trưởng bộ phận khi đổi phòng ban (tạo mới) ---
  useEffect(() => {
    if (!isNew || !sv.department || sv.head_of_dept) return
    api.get(`${API}/meta/dept-head`, { params: { department: sv.department } })
      .then((r) => { const h = r.data.data.head_of_dept; if (h) setH('head_of_dept', h) })
      .catch(() => {})
  }, [isNew, sv.department])

  const isStaff = !can('survey_request', 'approve') && !can('survey_request', 'delete')
  const editable = (isNew || sv.status === 'draft' || sv.status === 'rejected') &&
    (isNew || can('survey_request', 'write') || String((sv as any).created_by) === String(user?.id))

  const companyOptions  = companies.map((c) => ({ value: c.id, label: c.name }))
  const employeeOptions = employees.map((e) => ({ value: e.full_name, label: e.full_name }))
  const deptOptions     = departments.map((d) => ({ value: d.name, label: d.name }))
  // NSTM phụ trách: value = MÃ NV (khớp cột assignee), label = tên.
  // Bổ sung NSTM đã gán ở các dòng (dù không nằm trong ds nhân viên tải về do scope) → luôn hiện đúng tên.
  const purchaserOptions = (() => {
    const opts = employees.map((e) => ({ value: e.code, label: e.full_name }))
    for (const l of (sv.lines || [])) {
      if (l.assignee && !opts.some((o) => o.value === l.assignee))
        opts.push({ value: l.assignee, label: l.assignee_name || l.assignee })
    }
    return opts
  })()
  const canViewNstm = can('survey_request', 'process') // Ai xử lý được thì xem được cột NSTM
  const srLocked = sv.status === 'cancelled' || sv.status === 'done'   // Đã từ chối / Hoàn thành → khóa, không sửa
  const canAssignNstm = can('survey_request', 'approve') && !srLocked // Chỉ QL/Admin mới được gán NSTM (và phiếu chưa khóa)
  // Cột NSTM (Ngày tiếp nhận, Nhân sự phụ trách): CHỈ hiện với quản lý/thu mua, KHÔNG hiện với người YC & lúc tạo
  const showNstmCols = canViewNstm && !isNew
  // Trạng thái dòng: ẩn khi TẠO mới (mọi dòng đều "Chưa xong" → rối mắt)
  const showStatus = !isNew
  const empName = (code: string) => employees.find((e) => e.code === code)?.full_name || code || ''
  const itemGroupNames = itemGroups.map((g: any) => g.name)
  // Mô tả phân loại = số ngày quy định (hàng NCC có sẵn / không sẵn)
  const groupDesc = (name: string) => {
    const g = itemGroups.find((x: any) => x.name === name)
    if (!g) return ''
    const p: string[] = []
    if (g.std_days) p.push(`NCC có sẵn: ${g.std_days} ngày`)
    if (g.std_days_unavail) p.push(`không sẵn: ${g.std_days_unavail} ngày`)
    if (g.note) p.push(g.note)
    return p.join(' · ')
  }

  async function assignPurchaser(lineId: number, code: string) {
    try { await api.patch(`${API}/${id}/lines/${lineId}/assignee`, { assignee: code }); toast.success('Đã cập nhật NSTM phụ trách'); await loadAll() }
    catch (e: any) { toast.error(e.response?.data?.message || 'Lỗi gán nhân sự') }
  }

  // --- Phase 5C/5D: kết quả khảo sát (ẩn NCC) + sinh PYC ---
  const [result, setResult] = useState<any>(null)
  const [viewImg, setViewImg] = useState<string | null>(null)   // lightbox ảnh đính kèm
  const [showPrModal, setShowPrModal] = useState(false)         // popup DS phiếu YCMH đã sinh

  // Esc để đóng popup DS phiếu YCMH
  useEffect(() => {
    if (!showPrModal) return
    const h = (e: KeyboardEvent) => { if (e.key === 'Escape') setShowPrModal(false) }
    window.addEventListener('keydown', h)
    return () => window.removeEventListener('keydown', h)
  }, [showPrModal])

  // Đính kèm không phải ảnh → hỏi trước khi tải về
  async function openAtt(a: any) {
    if (!(await askConfirm({ title: 'Tải tài liệu', message: `Tải file "${a.filename}" về máy?`, confirmText: 'Tải về', danger: false }))) return
    const el = document.createElement('a')
    el.href = a.url; el.download = a.filename || ''; el.target = '_blank'; el.rel = 'noopener'
    document.body.appendChild(el); el.click(); el.remove()
  }
  useEffect(() => {
    if (!isNew && ['survey_done', 'pr_created', 'done'].includes(sv.status)) {
      api.get(`${API}/${id}/result`).then((r) => setResult(r.data.data)).catch(() => setResult(null))
    }
  }, [sv.status])
  async function chooseOption(lineId: number, oid: number) {
    try {
      await api.patch(`${API}/${id}/lines/${lineId}/options/${oid}/choose`)
      await loadAll()                                     // refresh badge bảng + trạng thái phiếu
      const r = await api.get(`${API}/${id}/result`)      // refresh thẻ Kết quả (đánh dấu đã chọn)
      setResult(r.data.data)
      toast.success('Đã chọn phương án')
    } catch { /* lỗi đã hiện popup từ interceptor */ }
  }
  // 5D: người YC sinh Yêu cầu mua hàng từ phương án đã chọn
  async function createPrs() {
    if (!allChosen) { toast.error('Vui lòng chọn phương án đề xuất mua hàng'); return }
    if (!(await askConfirm({ title: 'Tạo Yêu cầu mua hàng', message: 'Tạo Yêu cầu mua hàng từ các phương án đã chọn?', confirmText: 'Tạo YCMH', danger: false }))) return
    try {
      const r = await api.post(`${API}/${id}/create-prs`)
      const codes = (r.data.data.created_prs || []).map((p: any) => p.code).join(', ')
      toast.success(`Đã tạo ${(r.data.data.created_prs || []).length} phiếu yêu cầu mua: ${codes}`)
      await loadAll()
      const rr = await api.get(`${API}/${id}/result`); setResult(rr.data.data)
    } catch { /* interceptor toast */ }
  }
  // 5D: Admin/QL chốt Hoàn thành
  async function finalizeSr() {
    if (!(await askConfirm({ title: 'Hoàn thành phiếu', message: 'Chuyển phiếu sang Hoàn thành? Sau đó không chỉnh sửa được nữa.', confirmText: 'Hoàn thành', danger: false }))) return
    try { await api.post(`${API}/${id}/finalize`); toast.success('Đã chuyển Hoàn thành'); await loadAll() }
    catch { /* interceptor toast */ }
  }
  // PYC đã sinh (duy nhất theo pr_id) để hiện link
  const createdPrs = (() => {
    const prMap = new Map<number, { code: string; items: string[] }>()
    ;(result?.lines || []).forEach((l: any, i: number) => {
      if (l.pr_id) {
        if (!prMap.has(l.pr_id)) prMap.set(l.pr_id, { code: l.pr_code, items: [] })
        const chosen = (l.options || []).find((o: any) => o.is_chosen)
        const optLabel = chosen ? (chosen.display_label || `Option ${chosen.public_id}`) : ''
        prMap.get(l.pr_id)!.items.push(`SP ${i + 1} (${optLabel})`)
      }
    })
    return Array.from(prMap.entries()).map(([pid, data]) => ({ pid, ...data }))
  })()
  const allChosen = (result?.lines || []).length > 0 && (result?.lines || []).every((l: any) => (l.options || []).some((o: any) => o.is_chosen))
  const canFinalize = can('survey_request', 'process') && can('survey_request', 'approve')
  // Chỉ NGƯỜI YÊU CẦU (người tạo) hoặc Admin TM (delete) được tạo YCMH
  const canCreatePr = String((sv as any).created_by) === String(user?.id) || can('survey_request', 'delete')

  // --- Đính kèm hình/tài liệu theo dòng ---
  const [lineFiles, setLineFiles] = useState<any[]>([])
  async function loadLineFiles(lineId: number) {
    try {
      const r = await api.get('/api/attachments', { params: { entity: 'survey_request_line', entity_id: lineId } })
      setLineFiles(r.data.data || [])
    } catch { setLineFiles([]) }
  }
  async function uploadLineFiles(fl: FileList | null, lineId: number) {
    if (!fl || !fl.length || !lineId) return
    const fd = new FormData(); fd.append('entity', 'survey_request_line'); fd.append('entity_id', String(lineId))
    Array.from(fl).forEach((f) => fd.append('files', f))
    try { await api.post('/api/attachments', fd); await loadLineFiles(lineId) }
    catch (e: any) { toast.error(e?.response?.data?.error?.message || e?.response?.data?.message || 'Lỗi tải file') }
  }
  async function delLineFile(fid: number, lineId: number) {
    if (!(await askConfirm({ message: 'Xóa hình/tài liệu này?' }))) return
    try { await api.delete(`/api/attachments/${fid}`); await loadLineFiles(lineId) } catch {}
  }

  // --- Hình CHỜ TẢI cho dòng CHƯA có id (gắn ngay lúc tạo, upload khi Lưu) ---
  const [pendingFiles, setPendingFiles] = useState<Record<number, File[]>>({})
  const addPending = (idx: number, fl: FileList | null) => {
    if (!fl || !fl.length) return
    const arr = Array.from(fl)   // chụp NGAY — vì input bị clear value sau onChange
    setPendingFiles((p) => ({ ...p, [idx]: [...(p[idx] || []), ...arr] }))
  }
  const removePending = (idx: number, fi: number) =>
    setPendingFiles((p) => ({ ...p, [idx]: (p[idx] || []).filter((_, k) => k !== fi) }))
  async function uploadFilesToLine(lineId: number, files: File[]) {
    const fd = new FormData(); fd.append('entity', 'survey_request_line'); fd.append('entity_id', String(lineId))
    files.forEach((f) => fd.append('files', f))
    await api.post('/api/attachments', fd)
  }
  // Sau khi lưu: đẩy hình chờ lên đúng dòng (khớp theo thứ tự index dòng trả về)
  async function flushPending(returnedLines: any[]) {
    for (const [idxStr, files] of Object.entries(pendingFiles)) {
      const i = Number(idxStr); const lineId = returnedLines?.[i]?.id
      if (lineId && (files as File[]).length) { try { await uploadFilesToLine(lineId, files as File[]) } catch {} }
    }
    setPendingFiles({})
  }

  const setH = (k: string, v: any) => setSv((s: any) => ({ ...s, [k]: v }))
  const lines: any[] = sv.lines || []

  const setLine = (i: number, k: string, v: any) =>
    setSv((s: any) => ({
      ...s,
      lines: s.lines.map((l: any, idx: number) => idx === i ? { ...l, [k]: v } : l),
    }))

  const addLine = () => setSv((s: any) => ({ ...s, lines: [...(s.lines || []), { ...emptyLine }] }))
  const delLine = (i: number) => {
    setSv((s: any) => ({ ...s, lines: s.lines.filter((_: any, idx: number) => idx !== i) }))
    setPendingFiles((p) => {
      const n: Record<number, File[]> = {}
      for (const [k, v] of Object.entries(p)) { const kk = Number(k); if (kk === i) continue; n[kk > i ? kk - 1 : kk] = v }
      return n
    })
  }
  const copyLine = (i: number) => {
    setSv((s: any) => {
      const src = { ...s.lines[i] }; delete src.id
      const arr = [...s.lines]; arr.splice(i + 1, 0, src); return { ...s, lines: arr }
    })
    setPendingFiles((p) => {
      const n: Record<number, File[]> = {}
      for (const [k, v] of Object.entries(p)) { const kk = Number(k); n[kk > i ? kk + 1 : kk] = v }
      return n
    })
  }

  function handleRequesterChange(empName: string, isAutoFill = false) {
    const emp = employees.find((e) => e.full_name === empName)
    if (emp) {
      const dept = departments.find((d) => d.id === emp.department_id)
      const deptName = dept ? dept.name : ''
      const head = employees.find((e) =>
        e.department_id === emp.department_id && e.id !== emp.id && (
          (e.role_name || '').toLowerCase().includes('trưởng') ||
          (e.position  || '').toLowerCase().includes('trưởng') ||
          (e.role_name || '').toLowerCase().includes('manager') ||
          (e.position  || '').toLowerCase().includes('head')
        ))
      setSv((s: any) => ({
        ...s,
        requester:          empName,
        requester_id:       emp.id || 0,
        requester_position: isAutoFill && s.requester_position ? s.requester_position : (emp.position || emp.role_name || ''),
        department:         isAutoFill && s.department ? s.department : deptName,
        head_of_dept:       isAutoFill && s.head_of_dept ? s.head_of_dept : (head ? head.full_name : s.head_of_dept || ''),
        company_id:         (isAutoFill && s.company_id) ? s.company_id : (emp.company_id || s.company_id),
      }))
    } else {
      setSv((s: any) => ({ ...s, requester: empName, requester_id: 0 }))
    }
  }

  function validate(): string {
    if (!sv.company_id) return 'Vui lòng chọn Công ty'
    if (!sv.requester)  return 'Vui lòng nhập Người yêu cầu'
    if (!sv.purpose)    return 'Vui lòng nhập Mục đích khảo sát'
    if (lines.length === 0) return 'Cần ít nhất 1 dòng sản phẩm cần khảo sát'
    for (const l of lines) {
      if (!l.item_group && !l.requirement_detail) return 'Mỗi dòng cần có Phân loại hoặc Chi tiết thông số'
    }
    return ''
  }

  async function save(submitAfterSave = false) {
    const v = validate()
    if (v) { toast.error(v); return }
    const body = {
      company_id:         Number(sv.company_id) || 0,
      requester:          sv.requester,
      requester_id:       Number(sv.requester_id) || 0,
      requester_position: sv.requester_position,
      department:         sv.department,
      head_of_dept:       sv.head_of_dept,
      purpose:            sv.purpose,
      request_date:       sv.request_date,
      note:               sv.note,
      lines:              lines,
    }
    try {
      if (isNew) {
        const r = await api.post(API, body)
        const created = r.data.data
        await flushPending(created.lines || [])          // đẩy hình chờ lên dòng vừa tạo
        if (submitAfterSave) await api.post(`${API}/${created.id}/submit`)
        navigate(`/survey-requests/${created.id}`)
      } else {
        const r = await api.patch(`${API}/${id}`, body)
        await flushPending(r.data?.data?.lines || [])    // dòng mới thêm vào phiếu cũ
        if (submitAfterSave) await api.post(`${API}/${id}/submit`)
        toast.success(submitAfterSave ? 'Đã gửi duyệt' : 'Đã lưu'); loadAll()
      }
    } catch (ex: any) { toast.error(ex?.response?.data?.error?.message || 'Lỗi khi lưu') }
  }

  async function action(path: string, payload: any = {}) {
    try { await api.post(`${API}/${id}/${path}`, payload); loadAll() }
    catch (ex: any) { toast.error(ex?.response?.data?.error?.message || 'Lỗi') }
  }

  async function deleteSv() {
    if (!(await askConfirm({ message: 'Xóa phiếu này?' }))) return
    try { await api.delete(`${API}/${id}`); navigate('/survey-requests') }
    catch (ex: any) { toast.error(ex?.response?.data?.error?.message || 'Lỗi xóa') }
  }

  const isLogShown = !isNew && logs.length > 0
  const edit = editIdx != null ? lines[editIdx] : null

  if (notFound) return <NotFound backTo="/survey-requests" message="Không tìm thấy yêu cầu khảo sát này hoặc bạn không có quyền truy cập." />

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate('/survey-requests')}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>
          {isNew ? 'Tạo Phiếu Yêu cầu Khảo sát mới' : (sv.code || 'Phiếu Yêu cầu Khảo sát')}
        </h2>
        {!isNew && srBadge(sv.status)}
        <span style={{ flex: 1 }} />

        {/* Lưu (riêng) + Gửi duyệt (riêng) — góc trên phải, khi đang soạn/nháp */}
        {editable && (
          <>
            <button className="btn" onClick={() => save(false)}>
              <i className="ti ti-device-floppy" />Lưu
            </button>
            <button className="btn secondary" onClick={() => save(true)}>
              <i className="ti ti-send" />Gửi duyệt
            </button>
          </>
        )}

        {/* Nút Duyệt / Trả lại (khi chờ duyệt + có quyền approve) */}
        {!isNew && sv.status === 'submitted' && can('survey_request', 'approve') && (
          <>
            <button className="btn" onClick={() => action('approve')}>
              <i className="ti ti-check" />Duyệt
            </button>
            <button
              className="btn ghost"
              style={{ color: '#d97706', borderColor: '#fcd34d' }}
              title="Trả về để người YC sửa & gửi lại"
              onClick={async () => {
                const r = await askPrompt({ title: 'Trả về', message: 'Lý do trả về (để người yêu cầu sửa & gửi duyệt lại):', confirmText: 'Trả về' })
                if (r !== null) action('reject', { reason: r })
              }}
            >
              <i className="ti ti-corner-up-left" />Trả về
            </button>
            <button
              className="btn ghost"
              style={{ color: 'var(--red)', borderColor: 'var(--red)' }}
              title="Khóa đơn hẳn — không sửa được, phải làm đơn mới"
              onClick={async () => {
                const r = await askPrompt({ title: 'Từ chối đơn', message: 'Lý do từ chối (khóa đơn, không thể sửa lại):', confirmText: 'Từ chối' })
                if (r !== null) action('cancel', { reason: r })
              }}
            >
              <i className="ti ti-ban" />Từ chối
            </button>
          </>
        )}

        {/* Nút Xử lý khảo sát — chỉ nhân sự thu mua thấy.
            Cờ 'process' được backend bơm vào perms (= survey_request read scope proc|all),
            nên NSTM/Quản lý/Admin TM đều thấy; người YC (own) & trưởng BP (dept) thì không. */}
        {!isNew && (sv.status === 'processing' || sv.status === 'survey_done') &&
          can('survey_request', 'process') && (
          <button className="btn" onClick={() => navigate(`/survey-requests/${id}/process`)}>
            <i className="ti ti-clipboard-list" />Xử lý khảo sát
          </button>
        )}

        {/* Tạo phiếu khảo sát trống đã gắn sẵn YCKS (chỉ khi đang xử lý) */}
        {!isNew && sv.status === 'processing' && can('survey_request', 'process') && (
          <button className="btn secondary" onClick={() => navigate(`/surveys/new?sr=${id}&sr_code=${encodeURIComponent(sv.code || '')}`)}>
            <i className="ti ti-clipboard-plus" />Tạo phiếu khảo sát
          </button>
        )}

        {/* Nút Tạo yêu cầu mua (người YC) — góc phải như Xử lý khảo sát */}
        {!isNew && sv.status === 'survey_done' && canCreatePr && (
          <button className="btn" onClick={createPrs}>
            <i className="ti ti-file-plus" />Tạo yêu cầu mua
          </button>
        )}

        {/* Nút Chuyển Hoàn thành (Quản lý/Admin TM) */}
        {!isNew && sv.status === 'pr_created' && canFinalize && (
          <button className="btn" onClick={finalizeSr}>
            <i className="ti ti-flag-check" />Chuyển Hoàn thành
          </button>
        )}

        {/* Nút mở popup danh sách PYC đã sinh */}
        {createdPrs.length > 0 && (
          <button className="btn ghost" style={{ color: '#15803d', borderColor: '#bbf7d0' }} onClick={() => setShowPrModal(true)}>
            <i className="ti ti-file-check" />Đã tạo {createdPrs.length} phiếu YCMH
          </button>
        )}

        {/* Nút Xóa */}
        {!isNew && ['draft', 'rejected', 'cancelled'].includes(sv.status) && can('survey_request', 'delete') && (
          <button
            className="btn ghost"
            style={{ color: 'var(--red)', borderColor: 'var(--red)' }}
            onClick={deleteSv}
          >
            <i className="ti ti-trash" />Xóa phiếu
          </button>
        )}
      </div>

      {/* Popup PYC đã sinh — mở từ nút "Đã tạo N phiếu YCMH" trên header */}
      {showPrModal && createdPrs.length > 0 && (
        <div className="confirm-modal-overlay" onClick={() => setShowPrModal(false)}>
          <div className="confirm-modal" style={{ position: 'relative', maxWidth: 580, textAlign: 'left', padding: 0, overflow: 'hidden' }} onClick={(e) => e.stopPropagation()}>
            {/* Nút X đóng — góc trên phải */}
            <button
              onClick={() => setShowPrModal(false)}
              title="Đóng"
              style={{ position: 'absolute', top: 12, right: 12, width: 30, height: 30, display: 'grid', placeItems: 'center', border: 'none', borderRadius: 8, background: 'transparent', color: '#94a3b8', cursor: 'pointer', fontSize: 18, lineHeight: 1 }}
              onMouseEnter={(e) => { e.currentTarget.style.background = '#f1f5f9'; e.currentTarget.style.color = '#475569' }}
              onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; e.currentTarget.style.color = '#94a3b8' }}
            >
              <i className="ti ti-x" />
            </button>

            {/* Header xanh */}
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '18px 22px', background: '#f0fdf4', borderBottom: '1px solid #dcfce7' }}>
              <span style={{ width: 38, height: 38, flexShrink: 0, display: 'grid', placeItems: 'center', borderRadius: '50%', background: '#dcfce7', color: '#16a34a', fontSize: 20 }}>
                <i className="ti ti-circle-check" />
              </span>
              <div>
                <div style={{ fontWeight: 700, color: '#15803d', fontSize: 15 }}>Đã tạo {createdPrs.length} phiếu yêu cầu mua hàng</div>
                <div style={{ color: '#64748b', fontSize: 12, marginTop: 1 }}>Bấm mã phiếu để mở chi tiết</div>
              </div>
            </div>

            {/* Danh sách PYC */}
            <ul style={{ listStyle: 'none', margin: 0, padding: '10px 12px', minHeight: 120, maxHeight: '55vh', overflowY: 'auto' }}>
              {createdPrs.map((p) => (
                <li key={p.pid} style={{ padding: '10px 12px', borderRadius: 10, display: 'flex', flexDirection: 'column', gap: 3 }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = '#f8fafc')}
                  onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}>
                  <a className="clickable" style={{ color: 'var(--teal)', fontWeight: 700, fontSize: 14 }} onClick={() => navigate(`/purchase-requests/${p.pid}`)}>
                    <i className="ti ti-file-text" style={{ marginRight: 6 }} />{p.code}
                  </a>
                  <span style={{ color: '#64748b', fontSize: 12.5, paddingLeft: 22 }}>Bao gồm: <b style={{ color: '#334155' }}>{p.items.join(', ')}</b></span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Lý do trả đơn / từ chối — chỉ hiện khi đang ở trạng thái đó */}
      {!isNew && sv.reject_reason && (sv.status === 'rejected' || sv.status === 'cancelled') && (
        <div className="err" style={{ marginBottom: 12 }}>
          <b>{sv.status === 'cancelled' ? 'Lý do từ chối:' : 'Lý do trả đơn:'}</b> {sv.reject_reason}
        </div>
      )}

      <div className={isLogShown ? 'detail-grid' : ''}>
        <div>
          {/* Thông tin chung */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <h3 className="sec-title">Thông tin chung</h3>
            <div className="form-grid">

              {/* Mã phiếu (chỉ hiện khi edit) */}
              {!isNew && (
                <div className="form-row">
                  <label>Mã phiếu</label>
                  <input value={sv.code || ''} disabled />
                </div>
              )}

              <div className="form-row">
                <label>Ngày tạo {isNew && <span className="req">*</span>}</label>
                {isNew ? (
                  <input type="date" value={sv.request_date || ''}
                    onChange={(e) => setH('request_date', e.target.value)} />
                ) : (
                  <input value={fmtDateTime(sv.created_at) || sv.request_date || '—'} disabled />
                )}
              </div>

              <div className="form-row">
                <label>Công ty nhận hóa đơn <span className="req">*</span></label>
                <Select
                  value={companyOptions.find((o) => o.value === sv.company_id) || null}
                  onChange={(o: any) => setH('company_id', o ? o.value : 0)}
                  options={companyOptions}
                  isDisabled={!editable}
                  isClearable
                  placeholder="Chọn công ty"
                  styles={{ control: (b) => ({ ...b, minHeight: 40, borderRadius: 12, borderColor: '#E9EDF7' }) }}
                />
              </div>

              <div className="form-row">
                <label>Người yêu cầu <span className="req">*</span></label>
                <Select
                  value={employeeOptions.find((o) => o.value === sv.requester) ||
                    (sv.requester ? { value: sv.requester, label: sv.requester } : null)}
                  onChange={(o: any) => handleRequesterChange(o ? o.value : '')}
                  options={employeeOptions}
                  isDisabled={!editable || isStaff}
                  isClearable
                  placeholder="Chọn nhân sự"
                  styles={{ control: (b) => ({ ...b, minHeight: 40, borderRadius: 12, borderColor: '#E9EDF7' }) }}
                />
              </div>

              <div className="form-row">
                <label>Chức vụ</label>
                <input value={sv.requester_position || ''} placeholder="Tự động theo Nhân sự"
                  disabled={!editable}
                  onChange={(e) => setH('requester_position', e.target.value)} />
              </div>

              <div className="form-row">
                <label>Bộ phận YC <span className="req">*</span></label>
                {editable ? (
                  <SearchSelect
                    value={sv.department || ''}
                    options={deptOptions}
                    disabled={!editable}
                    placeholder="Chọn bộ phận…"
                    onChange={(v) => setH('department', v)}
                  />
                ) : (
                  <input value={sv.department || ''} disabled />
                )}
              </div>

              <div className="form-row">
                <label>Trưởng bộ phận <span className="req">*</span></label>
                <input value={sv.head_of_dept || ''} placeholder="Tự động theo phòng ban"
                  disabled />
              </div>

              <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                <label>Mục đích khảo sát <span className="req">*</span></label>
                <textarea
                  placeholder="Nhập mục đích khảo sát..."
                  style={{ minHeight: 72 }}
                  value={sv.purpose || ''}
                  disabled={!editable}
                  onChange={(e) => setH('purpose', e.target.value)}
                />
              </div>

              <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                <label>Ghi chú</label>
                <textarea
                  placeholder="Ghi chú thêm..."
                  style={{ minHeight: 60 }}
                  value={sv.note || ''}
                  disabled={!editable}
                  onChange={(e) => setH('note', e.target.value)}
                />
              </div>

            </div>
          </div>

          {/* Danh sách dòng sản phẩm cần khảo sát */}
          <div className="card" style={{ padding: 18, marginBottom: 16 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 className="sec-title" style={{ margin: 0, borderBottom: 'none', paddingBottom: 0 }}>
                Danh sách Sản phẩm cần Khảo sát
              </h3>
              {editable && (
                <button className="btn ghost" onClick={addLine} style={{ height: 30, padding: '0 10px', fontSize: 13 }}>
                  <i className="ti ti-plus" /> Thêm dòng
                </button>
              )}
              {!editable && !isNew && showNstmCols && <span style={{ fontSize: 12, color: 'var(--muted)' }}><i className="ti ti-device-floppy" /> Thay đổi phụ trách được lưu tự động</span>}
            </div>

            <div className="items-scroll">
              <table className="items-table" style={{ width: '100%', minWidth: showNstmCols ? 1160 : 960, tableLayout: 'fixed' }}>
                <thead>
                  <tr>
                    <th style={{ width: 34, textAlign: 'center' }}>No.</th>
                    {showNstmCols && <th style={{ width: 110, textAlign: 'left' }}>Ngày tiếp nhận</th>}
                    <th style={{ width: 120, textAlign: 'left' }}>Ngày YC trả KQ</th>
                    <th style={{ width: 150, textAlign: 'left' }}>Phân loại</th>
                    <th style={{ width: 220, textAlign: 'left' }}>Chi tiết thông số</th>
                    <th style={{ width: 80, textAlign: 'right' }}>SL dự kiến</th>
                    <th style={{ width: 90, textAlign: 'left' }}>ĐVT</th>
                    <th style={{ width: 110, textAlign: 'right' }}>Giá đề xuất</th>
                    {showNstmCols && <th style={{ width: 150, textAlign: 'left' }}>Nhân sự phụ trách</th>}
                    {showStatus && <th style={{ width: 110, textAlign: 'center' }}>Trạng thái</th>}
                    <th style={{ width: 84, textAlign: 'center' }}>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {lines.map((l: any, i: number) => (
                    <tr key={i}>
                      <td style={{ textAlign: 'center' }}>{i + 1}</td>

                      {/* Ngày tiếp nhận — chỉ view NSTM/QL */}
                      {showNstmCols && (
                        <td><span style={{ color: l.received_date ? 'inherit' : '#bbb' }}>{l.received_date ? new Date(l.received_date).toLocaleDateString('vi-VN') : '—'}</span></td>
                      )}

                      {/* Ngày YC trả KQ — sửa inline được */}
                      <td>
                        {editable
                          ? <input type="date" className="cell-input" value={l.result_due_date || ''} onChange={(e) => setLine(i, 'result_due_date', e.target.value)} />
                          : <span style={{ color: l.result_due_date ? 'inherit' : '#bbb' }}>{l.result_due_date ? new Date(l.result_due_date).toLocaleDateString('vi-VN') : '—'}</span>}
                      </td>

                      {/* Phân loại */}
                      <td style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={l.item_group}>
                        {editable
                          ? <SearchSelect value={l.item_group || ''} options={itemGroupNames} variant="table" placeholder="—" onChange={(v) => setLine(i, 'item_group', v)} />
                          : <span>{l.item_group || '—'}</span>}
                      </td>

                      {/* Chi tiết thông số — sửa inline (mô tả dài mở nút chi tiết) */}
                      <td style={{ overflow: 'hidden' }} title={l.requirement_detail}>
                        {editable
                          ? <input className="cell-input" value={l.requirement_detail || ''} placeholder="Mô tả thông số…" onChange={(e) => setLine(i, 'requirement_detail', e.target.value)} />
                          : <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', display: 'block' }}>{l.requirement_detail || <span style={{ color: '#bbb' }}>—</span>}</span>}
                      </td>

                      {/* SL dự kiến */}
                      <td style={{ textAlign: 'right' }}>
                        {editable
                          ? <NumberInput className="cell-input" style={{ textAlign: 'right' }} value={l.request_qty} placeholder="0" onChange={(v: number) => setLine(i, 'request_qty', v)} />
                          : fmtBlank(l.request_qty)}
                      </td>

                      {/* ĐVT */}
                      <td>
                        {editable
                          ? <SearchSelect value={l.uom || ''} options={units} variant="table" placeholder="—" onChange={(v) => setLine(i, 'uom', v)} />
                          : (l.uom || '—')}
                      </td>

                      {/* Giá đề xuất */}
                      <td style={{ textAlign: 'right' }}>
                        {editable
                          ? <NumberInput className="cell-input" style={{ textAlign: 'right' }} value={l.proposed_price} placeholder="—" onChange={(v: number) => setLine(i, 'proposed_price', v)} />
                          : fmtBlank(l.proposed_price)}
                      </td>

                      {/* Nhân sự phụ trách — chỉ view NSTM/QL */}
                      {showNstmCols && (
                        <td style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={l.assignee_name || l.assignee}>
                          {canAssignNstm && l.id
                            ? <SearchSelect value={l.assignee || ''} options={purchaserOptions} variant="table" placeholder="— Gán —" onChange={(v) => assignPurchaser(l.id, v)} />
                            : <span>{l.assignee_name || empName(l.assignee) || <span style={{ color: '#bbb' }}>—</span>}</span>}
                        </td>
                      )}

                      {/* Trạng thái — ẩn khi tạo mới */}
                      {showStatus && (
                        <td style={{ textAlign: 'center' }}>
                          {(() => { const s = srLineStatus(l); return <span className={'badge ' + s.cls}>{s.label}</span> })()}
                        </td>
                      )}

                      {/* Thao tác */}
                      <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                        <button className="icon-btn" title="Chi tiết / hình ảnh" onClick={() => setEditIdx(i)}>
                          <i className="ti ti-pencil" style={{ color: 'var(--teal)' }} />
                        </button>
                        {editable && (
                          <button className="icon-btn" title="Nhân đôi" onClick={() => copyLine(i)}>
                            <i className="ti ti-copy" style={{ color: 'var(--muted)' }} />
                          </button>
                        )}
                        {editable && (
                          <button className="icon-btn" title="Xóa" onClick={() => delLine(i)}>
                            <i className="ti ti-trash" style={{ color: 'var(--red)' }} />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                  {lines.length === 0 && (
                    <tr>
                      <td colSpan={8 + (showNstmCols ? 2 : 0) + (showStatus ? 1 : 0)} style={{ textAlign: 'center', color: '#999', padding: 20 }}>
                        Chưa có dòng nào — nhấn "Thêm dòng" để bắt đầu
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Phase 5C/5D: Kết quả khảo sát (ẩn NCC) — khi đã khảo sát / đã tạo YCMH / hoàn thành */}
          {!isNew && ['survey_done', 'pr_created', 'done'].includes(sv.status) && result && (
            <div className="card" style={{ padding: 18, marginBottom: 16 }}>
              <h3 className="sec-title"><i className="ti ti-clipboard-check" /> Kết quả khảo sát {sv.status === 'survey_done' ? '— chọn phương án' : ''}</h3>

              {sv.status === 'survey_done' && (
                <p style={{ color: 'var(--muted)', fontSize: 12.5, marginTop: -6, marginBottom: 14 }}>
                  Với mỗi sản phẩm, nhấn chọn 1 phương án phù hợp nhất. (Thông tin nhà cung cấp được ẩn theo chính sách.)
                </p>
              )}
              {(result.lines || []).map((ln: any, li: number) => (
                <div key={ln.id} style={{ marginBottom: 22 }}>
                  <div style={{ fontWeight: 700, marginBottom: 3 }}>
                    Sản phẩm {li + 1}: {ln.requirement_detail || ln.item_group || '—'}
                  </div>
                  <div style={{ fontSize: 12.5, color: 'var(--muted)', marginBottom: 10 }}>
                    Phân loại: <b>{ln.item_group || '—'}</b> · SL dự kiến: <b>{fmtBlank(ln.request_qty) || '—'}</b> {ln.uom} · Giá đề xuất của bạn: <b>{fmtBlank(ln.proposed_price) || '—'}</b>
                  </div>
                  {(ln.options || []).length === 0 ? (
                    <div style={{ color: '#999', fontSize: 13 }}>Chưa có phương án nào cho sản phẩm này.</div>
                  ) : (
                    <div className="options-container">
                      {ln.options.map((o: any) => {
                        const canChoose = sv.status === 'survey_done'
                        return (
                        <div key={o.id} onClick={() => { if (canChoose) chooseOption(ln.id, o.id) }}
                          className="option-card"
                          style={{ border: `2px solid ${o.is_chosen ? 'var(--teal)' : '#E9EDF7'}`, borderRadius: 12, padding: 14, cursor: canChoose ? 'pointer' : 'default', opacity: (!canChoose && !o.is_chosen) ? 0.55 : 1, background: o.is_chosen ? 'rgba(20,184,166,.06)' : '#fff' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 }}>
                            <span style={{ fontWeight: 700 }}>
                              <input type="radio" checked={!!o.is_chosen} readOnly style={{ marginRight: 6, verticalAlign: 'middle' }} />
                              {o.display_label || `Option ${o.public_id}`}
                            </span>
                            {o.is_chosen && <span className="badge ok">Đã chọn</span>}
                          </div>
                          <div style={{ fontWeight: 600, marginBottom: 8 }}>{o.snap_product_name || '—'}</div>
                          <div className="option-fields">
                            <Field label="Đơn giá" value={o.snap_price_by_volume ? fmtBlank(o.snap_price_by_volume) + ' đ' : ''} strong />
                            <Field label="ĐVT báo giá" value={o.snap_quote_unit} />
                            <Field label="MOQ" value={fmtBlank(o.snap_moq)} />
                            <Field label="Khoảng SL áp giá" value={o.snap_volume_range} />
                            <Field label="VAT" value={o.snap_vat ? o.snap_vat + '%' : ''} />
                            <Field label="Xuất xứ" value={o.snap_origin} />
                            <Field label="Thời gian giao" value={o.snap_delivery_time} />
                            <Field label="Địa điểm giao" value={o.snap_delivery_place} />
                            <Field label="Phí vận chuyển" value={o.snap_shipping_cost ? fmtBlank(o.snap_shipping_cost) + ' đ' : 'Miễn phí'} />
                            <Field label="Có mẫu" value={o.snap_sample_ready ? 'Có' : 'Không'} />
                            <Field label="Kết quả lab" value={o.snap_lab_result} />
                          </div>
                          {o.snap_spec && (
                            <div style={{ marginTop: 8, fontSize: 12.5, borderTop: '1px dashed #E9EDF7', paddingTop: 8 }}>
                              <span style={{ color: 'var(--muted)' }}>Thông số: </span>{o.snap_spec}
                            </div>
                          )}
                          <div style={{ marginTop: 8, fontSize: 12.5, borderTop: '1px dashed #E9EDF7', paddingTop: 8 }} onClick={(e) => e.stopPropagation()}>
                            <div style={{ color: 'var(--muted)', marginBottom: 6 }}>Tài liệu đính kèm:</div>
                            {(o.attachments || []).length > 0 ? (
                              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
                                {(o.attachments || []).map((a: any) => isImageAtt(a) ? (
                                  <img key={a.file_id} src={a.url} title={a.filename} onClick={() => setViewImg(a.url)}
                                    style={{ width: 54, height: 54, objectFit: 'cover', borderRadius: 8, border: '1px solid #E9EDF7', cursor: 'pointer' }} />
                                ) : (
                                  <button key={a.file_id} type="button" className="btn ghost" style={{ height: 32, fontSize: 12.5 }} onClick={() => openAtt(a)}>
                                    <i className="ti ti-file-download" /> {a.filename}
                                  </button>
                                ))}
                              </div>
                            ) : (
                              <div style={{ color: '#94a3b8', fontStyle: 'italic' }}>Không có file đính kèm</div>
                            )}
                          </div>
                        </div>
                      ) })}
                    </div>
                  )}
                </div>
              ))}

              {/* Ghi chú trạng thái 5D (nút hành động ở góc phải header) */}
              {sv.status === 'survey_done' && !allChosen && (
                <div style={{ color: 'var(--muted)', fontSize: 12.5, marginTop: 4 }}>
                  Hãy chọn phương án cho tất cả sản phẩm, rồi bấm <b>“Tạo yêu cầu mua”</b> ở góc phải trên.
                </div>
              )}
              {sv.status === 'pr_created' && !canFinalize && (
                <div style={{ color: 'var(--muted)', fontSize: 12.5, marginTop: 4 }}>
                  Đã tạo YCMH — chờ Quản lý/Admin thu mua chuyển Hoàn thành.
                </div>
              )}
              {sv.status === 'done' && (
                <div style={{ marginTop: 4 }}><span className="badge ok">Phiếu đã Hoàn thành</span></div>
              )}
            </div>
          )}

        </div>

        {/* Lịch sử thao tác */}
        {isLogShown && (
          <div className="card" style={{ padding: 18 }}>
            <h3 className="sec-title"><i className="ti ti-history" /> Lịch sử thao tác</h3>
            <div className="timeline">
              {logs.map((l, i) => (
                <div key={i} className="tl-item">
                  <span className={'tl-dot ' + (
                    l.action === 'approved' ? 'create' :
                    (l.action === 'rejected') ? 'delete' : 'update'
                  )} />
                  <div>
                    <div style={{ fontSize: 13 }}>
                      <b>{l.by}</b> — {l.action_label}{l.message ? `: ${l.message}` : ''}
                    </div>
                    <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 2 }}>
                      {fmtDateTime(l.at)}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      {/* Popup chi tiết dòng */}
      {edit && editIdx != null && (
        <div
          style={{ position: 'fixed', inset: 0, background: 'rgba(27,37,89,.3)', zIndex: 200, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '4vh 12px', overflowY: 'auto' }}
          onClick={() => setEditIdx(null)}
        >
          <div className="card" style={{ width: 720, maxWidth: '100%', padding: 20 }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12 }}>
              <h3 className="sec-title" style={{ margin: 0, border: 0, padding: 0 }}>
                Chi tiết dòng #{editIdx + 1}
              </h3>
              <span className="clickable" style={{ color: '#94a3b8', fontSize: 18 }} onClick={() => setEditIdx(null)}>
                <i className="ti ti-x" />
              </span>
            </div>

            <div className="form-grid">
              <div className="form-row">
                <label>Phân loại <span className="req">*</span></label>
                <SearchSelect
                  value={edit.item_group || ''}
                  options={itemGroupNames}
                  disabled={!editable}
                  placeholder="Chọn/tìm phân loại…"
                  onChange={(v) => setLine(editIdx, 'item_group', v)}
                />
                {groupDesc(edit.item_group) && (
                  <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4 }}>
                    <i className="ti ti-info-circle" style={{ fontSize: 13, verticalAlign: '-1px' }} /> {groupDesc(edit.item_group)}
                  </div>
                )}
              </div>

              <div className="form-row">
                <label>Ngày yêu cầu trả kết quả</label>
                <input type="date" value={edit.result_due_date || ''} disabled={!editable}
                  onChange={(e) => setLine(editIdx, 'result_due_date', e.target.value)} />
              </div>

              <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                <label>Chi tiết thông số kỹ thuật &amp; chất lượng</label>
                <textarea
                  style={{ minHeight: 80 }}
                  value={edit.requirement_detail || ''}
                  disabled={!editable}
                  placeholder="Mô tả chi tiết yêu cầu kỹ thuật, chất lượng..."
                  onChange={(e) => setLine(editIdx, 'requirement_detail', e.target.value)}
                />
              </div>

              <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                <label>Yêu cầu khác</label>
                <textarea
                  style={{ minHeight: 60 }}
                  value={edit.other_requirement || ''}
                  disabled={!editable}
                  placeholder="Các yêu cầu bổ sung khác (xuất xứ, bảo hành, v.v.)..."
                  onChange={(e) => setLine(editIdx, 'other_requirement', e.target.value)}
                />
              </div>

              <div className="form-row">
                <label>Số lượng dự kiến mua</label>
                <NumberInput
                  value={edit.request_qty}
                  placeholder="0"
                  disabled={!editable}
                  onChange={(v: number) => setLine(editIdx, 'request_qty', v)}
                />
              </div>

              <div className="form-row">
                <label>ĐVT</label>
                <SearchSelect
                  value={edit.uom || ''}
                  options={units}
                  disabled={!editable}
                  placeholder="Chọn/tìm ĐVT…"
                  onChange={(v) => setLine(editIdx, 'uom', v)}
                />
              </div>

              <div className="form-row">
                <label>Giá đề xuất VNĐ</label>
                <NumberInput
                  value={edit.proposed_price}
                  placeholder="Để trống nếu chưa có"
                  disabled={!editable}
                  onChange={(v: number) => setLine(editIdx, 'proposed_price', v)}
                />
              </div>

              {/* Trạng thái dòng — tự suy theo tiến trình (ẩn khi tạo mới) */}
              {showStatus && (
                <div className="form-row">
                  <label>Trạng thái</label>
                  <div style={{ paddingTop: 4 }}>
                    {(() => { const s = srLineStatus(edit); return <span className={'badge ' + s.cls}>{s.label}</span> })()}
                    {edit.id && (
                      <span style={{ color: 'var(--muted)', fontSize: 12, marginLeft: 8 }}>
                        ({edit.option_count || 0} phương án{edit.has_chosen ? ', đã chọn' : ''})
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Đính kèm hình/tài liệu cho dòng (nhiều hình cho người đi khảo sát) */}
              <div className="form-row" style={{ gridColumn: '1 / -1' }}>
                <label>Hình ảnh / tài liệu đính kèm <span style={{ color: '#94a3b8', fontWeight: 400 }}>(có thể nhiều hình)</span></label>
                {edit.id ? (
                  <div>
                    {lineFiles.length > 0 && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 10 }}>
                        {lineFiles.map((f) => {
                          const isImg = /\.(jpg|jpeg|png|webp)$/i.test(f.filename || '')
                          return (
                            <div key={f.id} style={{ position: 'relative', border: '1px solid #E9EDF7', borderRadius: 10, padding: 6, width: isImg ? 96 : 160 }}>
                              <a href={f.url} target="_blank" rel="noreferrer" style={{ textDecoration: 'none', color: 'inherit' }} title={f.filename}>
                                {isImg
                                  ? <img src={f.url} style={{ width: 82, height: 82, objectFit: 'cover', borderRadius: 6, display: 'block' }} />
                                  : <div style={{ fontSize: 12, lineHeight: 1.3, wordBreak: 'break-all' }}><i className="ti ti-file" /> {f.filename}</div>}
                              </a>
                              <button type="button" title="Xóa" onClick={() => delLineFile(f.id, edit.id)}
                                style={{ position: 'absolute', top: -8, right: -8, width: 22, height: 22, borderRadius: '50%', border: '1px solid #E9EDF7', background: '#fff', cursor: 'pointer', lineHeight: 1 }}>
                                <i className="ti ti-x" style={{ color: 'var(--red)', fontSize: 13 }} />
                              </button>
                            </div>
                          )
                        })}
                      </div>
                    )}
                    <input type="file" id="sr-line-upload" multiple accept="image/*,.pdf" style={{ display: 'none' }}
                      onChange={(e) => { uploadLineFiles(e.target.files, edit.id); e.currentTarget.value = '' }} />
                    <label htmlFor="sr-line-upload" className="btn ghost" style={{ cursor: 'pointer', height: 32, fontSize: 13, width: 'fit-content' }}>
                      <i className="ti ti-upload" /> Thêm hình / file
                    </label>
                    {lineFiles.length === 0 && <div style={{ color: '#999', fontSize: 12.5, marginTop: 6 }}>Chưa có hình. Tải nhiều hình (jpg/png/webp/pdf) để người khảo sát tham khảo.</div>}
                  </div>
                ) : (
                  <div>
                    {(pendingFiles[editIdx] || []).length > 0 && (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginBottom: 10 }}>
                        {(pendingFiles[editIdx] || []).map((f, fi) => {
                          const isImg = /\.(jpg|jpeg|png|webp)$/i.test(f.name)
                          return (
                            <div key={fi} style={{ position: 'relative', border: '1px solid #E9EDF7', borderRadius: 10, padding: 6, width: isImg ? 96 : 160 }}>
                              {isImg
                                ? <img src={URL.createObjectURL(f)} style={{ width: 82, height: 82, objectFit: 'cover', borderRadius: 6, display: 'block' }} />
                                : <div style={{ fontSize: 12, lineHeight: 1.3, wordBreak: 'break-all' }}><i className="ti ti-file" /> {f.name}</div>}
                              <button type="button" title="Bỏ" onClick={() => removePending(editIdx, fi)}
                                style={{ position: 'absolute', top: -8, right: -8, width: 22, height: 22, borderRadius: '50%', border: '1px solid #E9EDF7', background: '#fff', cursor: 'pointer', lineHeight: 1 }}>
                                <i className="ti ti-x" style={{ color: 'var(--red)', fontSize: 13 }} />
                              </button>
                            </div>
                          )
                        })}
                      </div>
                    )}
                    <input type="file" id="sr-line-pending" multiple accept="image/*,.pdf" style={{ display: 'none' }}
                      onChange={(e) => { addPending(editIdx, e.target.files); e.currentTarget.value = '' }} />
                    <label htmlFor="sr-line-pending" className="btn ghost" style={{ cursor: 'pointer', height: 32, fontSize: 13, width: 'fit-content' }}>
                      <i className="ti ti-upload" /> Thêm hình / file
                    </label>
                    <div style={{ color: '#0b6bcb', fontSize: 12.5, marginTop: 6 }}>
                      Chọn hình bây giờ — sẽ được <b>lưu cùng khi bạn bấm Lưu</b>.
                    </div>
                  </div>
                )}
              </div>

              {/* Nhân sự phụ trách + PYC (từ server khi phiếu đã xử lý) */}
              {!isNew && (edit.pr_code || (showNstmCols && edit.id)) && (
                <>
                  {/* Nhân sự phụ trách — CHỈ người có quyền gán mới thấy & sửa (đồng bộ cột ngoài bảng); người YC ẩn hẳn */}
                  {showNstmCols && edit.id && (
                    <div className="form-row">
                      <label>Nhân sự phụ trách</label>
                      <SearchSelect value={edit.assignee || ''} options={purchaserOptions} placeholder="— Gán —"
                        disabled={!canAssignNstm}
                        onChange={(v) => assignPurchaser(edit.id, v)} />
                    </div>
                  )}
                  {/* Ngày tiếp nhận — tự tính khi gán NSTM (chỉ đọc) */}
                  {showNstmCols && edit.id && (
                    <div className="form-row">
                      <label>Ngày tiếp nhận <span style={{ color: '#94a3b8', fontWeight: 400, fontSize: 12 }}>(tự tính khi gán NSTM)</span></label>
                      <input value={edit.received_date ? new Date(edit.received_date).toLocaleDateString('vi-VN') : ''} placeholder="Chưa có ngày tiếp nhận" disabled />
                    </div>
                  )}
                  {edit.pr_code && (
                    <div className="form-row">
                      <label>Mã PYC liên kết</label>
                      <input value={edit.pr_code || ''} disabled />
                    </div>
                  )}
                </>
              )}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
              <button className="btn ghost" onClick={() => setEditIdx(null)}>
                {editable ? 'Đóng' : 'Đóng'}
              </button>
              {editable && (
                <button className="btn" onClick={() => setEditIdx(null)}>
                  <i className="ti ti-check" />Xong
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Lightbox xem ảnh đính kèm — click nền hoặc nút X để đóng */}
      {viewImg && (
        <div onClick={() => setViewImg(null)}
          style={{ position: 'fixed', inset: 0, background: 'rgba(0,0,0,.8)', zIndex: 300, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
          <button className="icon-btn" onClick={() => setViewImg(null)}
            style={{ position: 'absolute', top: 16, right: 16, color: '#fff', fontSize: 22 }}>
            <i className="ti ti-x" />
          </button>
          <img src={viewImg} onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: '92vw', maxHeight: '88vh', objectFit: 'contain', borderRadius: 8 }} />
        </div>
      )}
    </div>
  )
}
