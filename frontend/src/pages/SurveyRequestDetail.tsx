import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { prBadge } from '../config/cruds'
import Select from 'react-select'
import SearchSelect from '../components/SearchSelect'

const API = '/api/survey-requests'

// Hiển thị số: để TRỐNG nếu chưa nhập (0/rỗng)
const fmtBlank = (n: any) => { const v = Number(n || 0); return v ? v.toLocaleString('vi-VN') : '' }

const SR_STATUS: Record<string, { label: string; cls: string }> = {
  draft:       { label: 'Nháp',         cls: 'gray' },
  submitted:   { label: 'Chờ duyệt',    cls: 'warn' },
  approved:    { label: 'Đã duyệt',     cls: 'ok'   },
  rejected:    { label: 'Từ chối',      cls: 'err'  },
  processing:  { label: 'Đang xử lý',   cls: 'warn' },
  survey_done: { label: 'Đã khảo sát',  cls: 'ok'   },
}

const srBadge = (st: string) => {
  const s = SR_STATUS[String(st || '').toLowerCase()] || { label: st, cls: 'gray' }
  return <span className={'badge ' + s.cls}>{s.label}</span>
}

const emptyLine = {
  received_date: '',
  result_due_date: '',
  department_requester: '',
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
  const [itemGroups, setItemGroups] = useState<string[]>([])
  const [units, setUnits]           = useState<string[]>([])
  const [logs, setLogs]             = useState<any[]>([])
  const [err, setErr]               = useState('')
  const [msg, setMsg]               = useState('')
  const [editIdx, setEditIdx]       = useState<number | null>(null)

  // --- load lookups once ---
  useEffect(() => {
    api.get('/api/companies',   { params: { page_size: 200 } }).then((r) => setCompanies(r.data.data.items)).catch(() => {})
    api.get('/api/departments', { params: { page_size: 500 } }).then((r) => setDepartments(r.data.data.items)).catch(() => {})
    api.get('/api/employees',   { params: { page_size: 1000 } }).then((r) => setEmployees(r.data.data.items)).catch(() => {})
    api.get('/api/item-groups', { params: { page_size: 500 } }).then((r) => setItemGroups(r.data.data.items.map((x: any) => x.name))).catch(() => {})
    api.get('/api/units',       { params: { page_size: 200 } }).then((r) => setUnits(r.data.data.items.map((x: any) => x.name))).catch(() => {})
  }, [])

  // --- load document ---
  async function loadAll() {
    const r = await api.get(`${API}/${id}`)
    setSv(r.data.data)
    api.get('/api/audit-logs', { params: { entity: 'survey_request', entity_id: id } })
      .then((x) => setLogs(x.data.data)).catch(() => {})
  }
  useEffect(() => { if (!isNew) loadAll() }, [id])

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
  // NSTM phụ trách: value = MÃ NV (khớp cột assignee), label = tên
  const purchaserOptions = employees.map((e) => ({ value: e.code, label: e.full_name }))
  const canAssign = can('survey_request', 'write')   // Admin / Admin TM gán NSTM cho dòng
  const empName = (code: string) => employees.find((e) => e.code === code)?.full_name || code || ''

  async function assignPurchaser(lineId: number, code: string) {
    try { await api.patch(`${API}/${id}/lines/${lineId}/assignee`, { assignee: code }); await loadAll() }
    catch (e: any) { setErr(e.response?.data?.message || 'Lỗi gán nhân sự') }
  }

  const setH = (k: string, v: any) => setSv((s: any) => ({ ...s, [k]: v }))
  const lines: any[] = sv.lines || []

  const setLine = (i: number, k: string, v: any) =>
    setSv((s: any) => ({
      ...s,
      lines: s.lines.map((l: any, idx: number) => idx === i ? { ...l, [k]: v } : l),
    }))

  const addLine = () => setSv((s: any) => ({ ...s, lines: [...(s.lines || []), { ...emptyLine }] }))
  const delLine = (i: number) => setSv((s: any) => ({ ...s, lines: s.lines.filter((_: any, idx: number) => idx !== i) }))
  const copyLine = (i: number) => setSv((s: any) => {
    const src = { ...s.lines[i] }; delete src.id
    const arr = [...s.lines]; arr.splice(i + 1, 0, src); return { ...s, lines: arr }
  })

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
        requester_position: isAutoFill && s.requester_position ? s.requester_position : (emp.position || emp.role_name || ''),
        department:         isAutoFill && s.department ? s.department : deptName,
        head_of_dept:       isAutoFill && s.head_of_dept ? s.head_of_dept : (head ? head.full_name : s.head_of_dept || ''),
        company_id:         (isAutoFill && s.company_id) ? s.company_id : (emp.company_id || s.company_id),
      }))
    } else {
      setSv((s: any) => ({ ...s, requester: empName }))
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
    setErr(''); setMsg('')
    const v = validate()
    if (v) { setErr(v); return }
    const body = {
      company_id:         Number(sv.company_id) || 0,
      requester:          sv.requester,
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
        const nid = r.data.data.id
        if (submitAfterSave) await api.post(`${API}/${nid}/submit`)
        navigate(`/survey-requests/${nid}`)
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

  async function deleteSv() {
    if (!confirm('Xóa phiếu này?')) return
    setErr('')
    try { await api.delete(`${API}/${id}`); navigate('/survey-requests') }
    catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi xóa') }
  }

  const isLogShown = !isNew && logs.length > 0
  const edit = editIdx != null ? lines[editIdx] : null

  return (
    <div>
      {/* Header */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate('/survey-requests')}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>
          {isNew ? 'Tạo Phiếu Yêu cầu Khảo sát mới' : (sv.purpose || sv.code || 'Phiếu Yêu cầu Khảo sát')}
        </h2>
        {!isNew && srBadge(sv.status)}
        <span style={{ flex: 1 }} />

        {/* Nút Duyệt / Trả lại (khi chờ duyệt + có quyền approve) */}
        {!isNew && sv.status === 'submitted' && can('survey_request', 'approve') && (
          <>
            <button className="btn" onClick={() => action('approve')}>
              <i className="ti ti-check" />Duyệt
            </button>
            <button
              className="btn ghost"
              style={{ color: 'var(--red)', borderColor: 'var(--red)' }}
              onClick={() => {
                const r = prompt('Lý do từ chối:')
                if (r !== null) action('reject', { reason: r })
              }}
            >
              <i className="ti ti-x" />Trả lại
            </button>
          </>
        )}

        {/* Nút Xóa */}
        {!isNew && editable && can('survey_request', 'delete') && (
          <button
            className="btn ghost"
            style={{ color: 'var(--red)', borderColor: 'var(--red)' }}
            onClick={deleteSv}
          >
            <i className="ti ti-trash" />Xóa
          </button>
        )}
      </div>

      {/* Lý do từ chối */}
      {!isNew && sv.reject_reason && (
        <div className="err" style={{ marginBottom: 12 }}>
          <b>Lý do từ chối:</b> {sv.reject_reason}
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
                <label>Ngày tạo <span className="req">*</span></label>
                <input type="date" value={sv.request_date || ''} disabled={!editable}
                  onChange={(e) => setH('request_date', e.target.value)} />
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
            </div>

            <div className="items-scroll">
              <table className="items-table" style={{ minWidth: 860, tableLayout: 'fixed' }}>
                <thead>
                  <tr>
                    <th style={{ width: 34, textAlign: 'center' }}>No.</th>
                    <th style={{ width: 110, textAlign: 'left' }}>Ngày tiếp nhận</th>
                    <th style={{ width: 110, textAlign: 'left' }}>Ngày YC trả KQ</th>
                    <th style={{ width: 130, textAlign: 'left' }}>BP/Người YC</th>
                    <th style={{ width: 140, textAlign: 'left' }}>Phân loại</th>
                    <th style={{ width: 200, textAlign: 'left' }}>Chi tiết thông số</th>
                    <th style={{ width: 70, textAlign: 'right' }}>SL dự kiến</th>
                    <th style={{ width: 80, textAlign: 'left' }}>ĐVT</th>
                    <th style={{ width: 100, textAlign: 'right' }}>Giá đề xuất</th>
                    <th style={{ width: 150, textAlign: 'left' }}>Nhân sự phụ trách</th>
                    <th style={{ width: 80, textAlign: 'center' }}>Thao tác</th>
                  </tr>
                </thead>
                <tbody>
                  {lines.map((l: any, i: number) => (
                    <tr key={i}>
                      <td style={{ textAlign: 'center' }}>{i + 1}</td>
                      <td>
                        {editable ? (
                          <input type="date" className="cell-input" value={l.received_date || ''}
                            onChange={(e) => setLine(i, 'received_date', e.target.value)} style={{ width: '100%' }} />
                        ) : <span>{l.received_date || '—'}</span>}
                      </td>
                      <td>
                        {editable ? (
                          <input type="date" className="cell-input" value={l.result_due_date || ''}
                            onChange={(e) => setLine(i, 'result_due_date', e.target.value)} style={{ width: '100%' }} />
                        ) : <span>{l.result_due_date || '—'}</span>}
                      </td>
                      <td style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                          title={l.department_requester}>
                        {editable ? (
                          <SearchSelect
                            value={l.department_requester || ''}
                            options={deptOptions}
                            variant="table"
                            placeholder="—"
                            onChange={(v) => setLine(i, 'department_requester', v)}
                          />
                        ) : <span>{l.department_requester || '—'}</span>}
                      </td>
                      <td style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                          title={l.item_group}>
                        {editable ? (
                          <SearchSelect
                            value={l.item_group || ''}
                            options={itemGroups}
                            variant="table"
                            placeholder="—"
                            onChange={(v) => setLine(i, 'item_group', v)}
                          />
                        ) : <span>{l.item_group || '—'}</span>}
                      </td>
                      <td style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}
                          title={l.requirement_detail}>
                        {l.requirement_detail || <span style={{ color: '#bbb' }}>(mở chi tiết)</span>}
                      </td>
                      <td style={{ textAlign: 'right' }}>{fmtBlank(l.request_qty)}</td>
                      <td>{l.uom || '—'}</td>
                      <td style={{ textAlign: 'right' }}>{fmtBlank(l.proposed_price)}</td>
                      <td style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={l.assignee_name || l.assignee}>
                        {canAssign && !isNew && l.id ? (
                          <SearchSelect value={l.assignee || ''} options={purchaserOptions} variant="table" placeholder="— Gán —"
                            onChange={(v) => assignPurchaser(l.id, v)} />
                        ) : <span>{l.assignee_name || empName(l.assignee) || <span style={{ color: '#bbb' }}>—</span>}</span>}
                      </td>
                      <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                        <button className="icon-btn" title="Chi tiết" onClick={() => setEditIdx(i)}>
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
                      <td colSpan={11} style={{ textAlign: 'center', color: '#999', padding: 20 }}>
                        Chưa có dòng nào — nhấn "Thêm dòng" để bắt đầu
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}
          {msg && <div style={{ color: 'var(--green)', fontSize: 13, marginTop: 8 }}>{msg}</div>}

          {/* Nút hành động cuối trang */}
          {editable && (
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 20 }}>
              <button className="btn ghost" onClick={() => navigate('/survey-requests')}>Hủy</button>
              <button className="btn secondary" onClick={() => save(false)}>Lưu nháp</button>
              <button className="btn" onClick={() => save(true)}>Lưu &amp; Gửi Duyệt</button>
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
                      {new Date(l.at).toLocaleString('vi-VN')}
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
                <label>Ngày tiếp nhận</label>
                <input type="date" value={edit.received_date || ''} disabled={!editable}
                  onChange={(e) => setLine(editIdx, 'received_date', e.target.value)} />
              </div>

              <div className="form-row">
                <label>Ngày YC trả KQ</label>
                <input type="date" value={edit.result_due_date || ''} disabled={!editable}
                  onChange={(e) => setLine(editIdx, 'result_due_date', e.target.value)} />
              </div>

              <div className="form-row">
                <label>BP/Người YC</label>
                <SearchSelect
                  value={edit.department_requester || ''}
                  options={deptOptions}
                  disabled={!editable}
                  placeholder="Chọn bộ phận…"
                  onChange={(v) => setLine(editIdx, 'department_requester', v)}
                />
              </div>

              <div className="form-row">
                <label>Phân loại <span className="req">*</span></label>
                <SearchSelect
                  value={edit.item_group || ''}
                  options={itemGroups}
                  disabled={!editable}
                  placeholder="Chọn/tìm phân loại…"
                  onChange={(v) => setLine(editIdx, 'item_group', v)}
                />
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
                <input
                  type="number"
                  value={edit.request_qty || ''}
                  placeholder="0"
                  disabled={!editable}
                  onChange={(e) => setLine(editIdx, 'request_qty', Number(e.target.value))}
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
                <input
                  type="number"
                  value={edit.proposed_price || ''}
                  placeholder="Để trống nếu chưa có"
                  disabled={!editable}
                  onChange={(e) => setLine(editIdx, 'proposed_price', Number(e.target.value))}
                />
              </div>

              {/* Thông tin chỉ đọc (từ server khi phiếu đã được xử lý) */}
              {!isNew && (edit.pr_code || edit.assignee) && (
                <>
                  {edit.assignee && (
                    <div className="form-row">
                      <label>Người phụ trách</label>
                      <input value={edit.assignee_name || empName(edit.assignee) || ''} disabled />
                    </div>
                  )}
                  {edit.pr_code && (
                    <div className="form-row">
                      <label>Mã PYC liên kết</label>
                      <input value={edit.pr_code || ''} disabled />
                    </div>
                  )}
                  {edit.is_completed !== undefined && (
                    <div className="form-row">
                      <label>Đã hoàn thành</label>
                      <input value={edit.is_completed ? 'Đã hoàn thành' : 'Chưa hoàn thành'} disabled />
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
    </div>
  )
}
