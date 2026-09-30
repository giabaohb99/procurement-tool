import { useEffect, useMemo, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import Select from 'react-select'
import { api } from '../api/client'
import { toast } from '../components/toast'
import AuditTimeline from '../components/AuditTimeline'

type Opt = { value: number; label: string }
type AssigneeRow = { id: number; item_group_id: number; department_id?: number }
/** bao-CR-527: nhân sự kèm tình trạng để ô chọn chỉ mời người «Chính thức» đang hoạt động. */
type EmpOpt = Opt & { official: boolean; statusText: string }
/** bao-CR-524: KHÔNG còn mục ảo «Thu mua chung». Để trống = backend ghi phòng thu mua mặc định. */
const DEFAULT_DEPT_LABEL = 'Phòng thu mua mặc định'
const selStyle = {
  control: (b: any) => ({ ...b, minHeight: 40, borderRadius: 12, borderColor: '#E9EDF7' }),
  menuPortal: (b: any) => ({ ...b, zIndex: 9999 }),
}
const portal = typeof document !== 'undefined' ? document.body : undefined

export default function CategoryAssigneeNew() {
  const navigate = useNavigate()
  const [sp] = useSearchParams()

  const [cats, setCats] = useState<Opt[]>([])
  const [emps, setEmps] = useState<EmpOpt[]>([])
  const [depts, setDepts] = useState<Opt[]>([])
  const [rows, setRows] = useState<AssigneeRow[]>([])   // toàn bộ dòng phân công (mọi phòng)
  const [selCats, setSelCats] = useState<Opt[]>([])
  const [primary, setPrimary] = useState<EmpOpt | null>(null)
  const [backup, setBackup] = useState<EmpOpt | null>(null)
  // Phòng áp dụng: mặc định lấy từ URL (?dept=); null = để trống → backend ghi phòng thu mua mặc
  // định (bao-CR-524, id thật của «Sản xuất -Thu mua»).
  const [dept, setDept] = useState<Opt | null>(() => {
    const id = Number(sp.get('dept')) || 0
    return id ? { value: id, label: `#${id}` } : null
  })
  const deptId = dept?.value || 0
  const [logs, setLogs] = useState<any[]>([])
  const [err, setErr] = useState(''); const [saving, setSaving] = useState(false)

  // Tải danh sách phân công của MỌI phòng; set "đã cấu hình" + map item_group_id→id dòng
  // tính theo phòng đang chọn (cùng phân loại có thể có một dòng chung và một dòng riêng từng phòng)
  async function loadAssignees() {
    const r = await api.get('/api/category-assignees', { params: { page_size: 1000 } })
    setRows(r.data.data.items || [])
  }
  const deptRows = useMemo(() => rows.filter(x => (x.department_id || 0) === deptId), [rows, deptId])
  const configured = useMemo(() => new Set(deptRows.map(x => x.item_group_id)), [deptRows])
  const rowByCat = useMemo<Record<number, number>>(
    () => Object.fromEntries(deptRows.map(x => [x.item_group_id, x.id])), [deptRows])

  useEffect(() => {
    api.get('/api/item-groups', { params: { page_size: 1000 } }).then(r => setCats((r.data.data.items || []).map((x: any) => ({ value: x.id, label: x.name }))))
    api.get('/api/employees', { params: { page_size: 1000 } }).then(r => setEmps((r.data.data.items || []).map((x: any) => ({
      value: x.id, label: x.full_name + (x.code ? ` · ${x.code}` : ''),
      // bao-CR-527: «Chính thức» + đang hoạt động mới nhận việc được
      official: x.status === 'official' && x.is_active !== false,
      statusText: x.is_active === false ? 'ngừng hoạt động' : (x.status_label || x.status || 'chưa rõ'),
    }))))
    // Không có quyền đọc phòng ban thì ô Phòng trống — phân công rơi về phòng thu mua mặc định
    api.get('/api/departments', { params: { page_size: 500 }, _silent: true } as any)
      .then(r => setDepts((r.data.data.items || []).map((x: any) => ({ value: x.id, label: x.name }))))
      .catch(() => setDepts([]))
    loadAssignees()
  }, [])
  const deptOptions = depts
  // Có danh sách phòng rồi thì gắn đúng tên phòng cho giá trị đọc từ URL
  useEffect(() => {
    if (!dept) return
    const found = depts.find(d => d.value === dept.value)
    if (found && found.label !== dept.label) setDept(found)
  }, [depts])
  // bao-CR-527: ô chọn chỉ mời người «Chính thức»; người ĐANG được gán mà nay không còn đạt thì vẫn
  // hiện kèm tình trạng để người sửa thấy phải đổi.
  const empOptions = useMemo(() => emps
    .filter(e => e.official || e.value === primary?.value || e.value === backup?.value)
    .map(e => (e.official ? e : { ...e, label: `${e.label} (${e.statusText})` })), [emps, primary, backup])

  // Sửa 1 phân loại đã cấu hình (?cats=) → tải lịch sử thao tác của dòng phân công đó
  const editCat = Number(sp.get('cats'))
  const editRowId = editCat ? rowByCat[editCat] : undefined
  useEffect(() => {
    if (!editRowId) { setLogs([]); return }
    api.get('/api/audit-logs', { params: { entity: 'category_assignee', entity_id: editRowId }, _silent: true } as any)
      .then(r => setLogs(r.data.data || [])).catch(() => setLogs([]))
  }, [editRowId])

  // Prefill khi Sửa/Copy từ danh sách (?cats=&primary=&backup=)
  useEffect(() => {
    if (!emps.length) return
    const p = Number(sp.get('primary')); const b = Number(sp.get('backup'))
    if (p && !primary) setPrimary(emps.find(e => e.value === p) || null)
    if (b && !backup) setBackup(emps.find(e => e.value === b) || null)
  }, [emps])
  useEffect(() => {
    if (!cats.length) return
    const c = Number(sp.get('cats'))
    if (c && selCats.length === 0) {
      const opt = cats.find(x => x.value === c)
      if (opt) setSelCats([opt])
    }
  }, [cats])

  async function save() {
    setErr('')
    if (selCats.length === 0) { setErr('Chọn ít nhất 1 phân loại'); return }
    if (!primary) { setErr('Chọn NSTM chính'); return }
    // bao-CR-527: dự phòng khác người chính; cả hai phải «Chính thức» (backend chặn lại lần nữa)
    if (backup && backup.value === primary.value) { setErr('NSTM dự phòng phải là người khác NSTM chính'); return }
    for (const [who, role] of [[primary, 'NSTM chính'], [backup, 'NSTM dự phòng']] as const) {
      if (who && !who.official) {
        setErr(`${role} ${who.label} đang ở tình trạng «${who.statusText}» — chỉ phân công được nhân sự «Chính thức» đang hoạt động`)
        return
      }
    }
    setSaving(true)
    try {
      await api.post('/api/category-assignees/bulk', {
        item_group_ids: selCats.map(c => c.value),
        primary_employee_id: primary.value,
        backup_employee_id: backup?.value || 0,
        department_id: deptId,   // 0 = phòng thu mua mặc định (bao-CR-524, backend ghi id thật)
      })
      toast.success('Đã lưu phân công')
      await loadAssignees()   // ở lại trang, cập nhật map (phân loại mới tạo có id)
      // Sửa phân loại đã có: editRowId không đổi nên effect không tự chạy → refetch log ngay
      if (editRowId) {
        const lg = await api.get('/api/audit-logs', { params: { entity: 'category_assignee', entity_id: editRowId }, _silent: true } as any)
        setLogs(lg.data.data || [])
      }
    } catch (e: any) { setErr(e.response?.data?.message || 'Lỗi lưu') }
    finally { setSaving(false) }
  }

  // Sửa 1 phân loại đã có -> tên phân loại làm tiêu đề; thêm mới thì dùng tên chức năng.
  const editCatLabel = editCat ? cats.find(c => c.value === editCat)?.label : ''
  const heading = editCatLabel || 'Gán phân công phụ trách'

  return (
    <div>
      {/* Thanh thao tác trên cùng — cùng bố cục trang chi tiết Phòng ban:
          quay lại bên trái, Lưu/Hủy bên phải để form dài không phải cuộn xuống cuối. */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate('/category-assignees')} title="Về danh sách Phân công phụ trách">
          <i className="ti ti-arrow-left" />
        </button>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          <button className="btn" disabled={saving} onClick={save}>{saving ? 'Đang lưu…' : 'Lưu'}</button>
          <button className="btn ghost" onClick={() => navigate('/category-assignees')}>Hủy</button>
        </div>
      </div>

      {/* Thẻ danh tính: KHÔNG có ảnh (phân công không gắn với người/logo cụ thể),
          chỉ tên + chip mô tả — giống trang chi tiết Phòng ban. */}
      <div className="card hero-card" style={{ marginBottom: 16 }}>
        <div className="hero-body">
          <div style={{ minWidth: 0 }}>
            <div className="hero-name">{heading}</div>
            {/* Tên phân loại đã làm tiêu đề nên chip chỉ mô tả phần còn lại: ai đang phụ trách */}
            {editCatLabel ? (
              <div className="hero-chips">
                <span className="hero-chip">
                  <i className="ti ti-building" />Phòng: {dept ? dept.label : DEFAULT_DEPT_LABEL}
                </span>
                <span className="hero-chip code">
                  <i className="ti ti-user-star" />NSTM chính: {primary ? primary.label : 'chưa có'}
                </span>
                <span className="hero-chip">
                  <i className="ti ti-user-shield" />NSTM dự phòng: {backup ? backup.label : 'chưa có'}
                </span>
              </div>
            ) : (
              <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 6 }}>
                Phân công phụ trách (theo phân loại) · Thêm mới
              </div>
            )}
          </div>
        </div>
      </div>

      <div className="detail-grid">
        <div className="card" style={{ padding: 18 }}>
          <div className="form-grid">
            <div className="form-group-title">Phạm vi áp dụng</div>
            <div className="form-row" style={{ gridColumn: '1 / -1' }}>
              <label>Phòng</label>
              <Select classNamePrefix="rs" value={dept} options={deptOptions} onChange={(v: any) => setDept(v || null)} isClearable
                placeholder="Để trống = phòng thu mua mặc định" styles={selStyle} menuPortalTarget={portal} menuPosition="fixed" />
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4, fontWeight: 'normal' }}>
                Bộ của <b>phòng thu mua mặc định (Sản xuất -Thu mua)</b> áp cho mọi phiếu chưa có dòng riêng của phòng xử lý.
                Chọn một phòng khác thì cặp NSTM bên dưới chỉ nhận phiếu do phòng đó xử lý (kể cả phiếu phòng khác nhờ phòng này xử lý).
              </div>
            </div>

            <div className="form-group-title">Phân loại</div>
            {/* Ô chọn nhiều cần trọn chiều ngang, không bó trong 1 nửa lưới 2 cột */}
            <div className="form-row" style={{ gridColumn: '1 / -1' }}>
              <label>Phân loại VTBB <span style={{ color: '#94a3b8', fontWeight: 400 }}>(chọn nhiều)</span></label>
              <Select isMulti classNamePrefix="rs" value={selCats} options={cats} onChange={(v: any) => setSelCats(v || [])}
                placeholder="Chọn/tìm phân loại…" styles={selStyle} menuPortalTarget={portal} menuPosition="fixed" closeMenuOnSelect={false}
                formatOptionLabel={(o: any) => <span>{o.label}{configured.has(o.value) ? <span style={{ color: '#d97706', fontSize: 11 }}> · đã có, sẽ ghi đè</span> : ''}</span>} />
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4, fontWeight: 'normal' }}>
                Cặp NSTM bên dưới sẽ được gán cho <b>tất cả phân loại đã chọn</b>. Phân loại đã có sẽ được <b>ghi đè</b>.
              </div>
            </div>

            <div className="form-group-title">Người phụ trách</div>
            <div className="form-row">
              <label>NSTM chính <span className="req" style={{ color: '#dc2626' }}>*</span></label>
              <Select classNamePrefix="rs" value={primary} options={empOptions} onChange={(v: any) => setPrimary(v)} isClearable placeholder="Chọn/tìm NSTM…" styles={selStyle} menuPortalTarget={portal} menuPosition="fixed" />
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4, fontWeight: 'normal' }}>
                Bắt buộc, chỉ nhân sự «Chính thức» đang hoạt động. Người nhận yêu cầu mua hàng thuộc các phân loại này.
              </div>
            </div>
            <div className="form-row">
              <label>NSTM dự phòng</label>
              <Select classNamePrefix="rs" value={backup} options={empOptions.filter(e => e.value !== primary?.value)} onChange={(v: any) => setBackup(v)} isClearable placeholder="Chọn/tìm NSTM…" styles={selStyle} menuPortalTarget={portal} menuPosition="fixed" />
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4, fontWeight: 'normal' }}>
                Tối đa một người, khác NSTM chính, cũng phải «Chính thức». Nhận việc khi NSTM chính không còn «Chính thức». Có thể bỏ trống.
              </div>
            </div>
          </div>
          {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}
        </div>

        {/* Lịch sử thao tác — chỉ hiện khi đang sửa 1 phân loại đã cấu hình */}
        {editRowId && (
          <div className="detail-col">
            <div className="card" style={{ padding: 18 }}>
              <h3 className="sec-title" style={{ marginTop: 0 }}>
                <i className="ti ti-history" style={{ marginRight: 8, color: '#b6c2d9' }} />Lịch sử thao tác
              </h3>
              {logs.length === 0 ? (
                <div style={{ color: 'var(--muted)', fontSize: 13 }}>
                  Chưa có thao tác nào được ghi nhận. Mọi lần sửa/xóa sẽ hiện ở đây kèm người thực hiện và thời điểm.
                </div>
              ) : (
                <AuditTimeline logs={logs} showMessage={false} />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
