import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import Select from 'react-select'
import { api } from '../api/client'
import { toast } from '../components/toast'
import AuditTimeline from '../components/AuditTimeline'

type Opt = { value: number; label: string }
const selStyle = {
  control: (b: any) => ({ ...b, minHeight: 40, borderRadius: 12, borderColor: '#E9EDF7' }),
  menuPortal: (b: any) => ({ ...b, zIndex: 9999 }),
}
const portal = typeof document !== 'undefined' ? document.body : undefined

export default function CategoryAssigneeNew() {
  const navigate = useNavigate()
  const [sp] = useSearchParams()

  const [cats, setCats] = useState<Opt[]>([])
  const [emps, setEmps] = useState<Opt[]>([])
  const [configured, setConfigured] = useState<Set<number>>(new Set())
  const [rowByCat, setRowByCat] = useState<Record<number, number>>({})   // item_group_id → id dòng phân công
  const [selCats, setSelCats] = useState<Opt[]>([])
  const [primary, setPrimary] = useState<Opt | null>(null)
  const [backup, setBackup] = useState<Opt | null>(null)
  const [logs, setLogs] = useState<any[]>([])
  const [err, setErr] = useState(''); const [saving, setSaving] = useState(false)

  // Tải danh sách phân công → cập nhật set "đã cấu hình" + map item_group_id→id dòng
  async function loadAssignees() {
    const r = await api.get('/api/category-assignees', { params: { page_size: 1000 } })
    const items = r.data.data.items || []
    setConfigured(new Set(items.map((x: any) => x.item_group_id)))
    setRowByCat(Object.fromEntries(items.map((x: any) => [x.item_group_id, x.id])))
  }

  useEffect(() => {
    api.get('/api/item-groups', { params: { page_size: 1000 } }).then(r => setCats((r.data.data.items || []).map((x: any) => ({ value: x.id, label: x.name }))))
    api.get('/api/employees', { params: { page_size: 1000 } }).then(r => setEmps((r.data.data.items || []).map((x: any) => ({ value: x.id, label: x.full_name + (x.code ? ` · ${x.code}` : '') }))))
    loadAssignees()
  }, [])

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
    setSaving(true)
    try {
      await api.post('/api/category-assignees/bulk', {
        item_group_ids: selCats.map(c => c.value),
        primary_employee_id: primary.value,
        backup_employee_id: backup?.value || 0,
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
              <Select classNamePrefix="rs" value={primary} options={emps} onChange={(v: any) => setPrimary(v)} isClearable placeholder="Chọn/tìm NSTM…" styles={selStyle} menuPortalTarget={portal} menuPosition="fixed" />
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4, fontWeight: 'normal' }}>
                Người nhận yêu cầu mua hàng thuộc các phân loại này.
              </div>
            </div>
            <div className="form-row">
              <label>NSTM dự phòng</label>
              <Select classNamePrefix="rs" value={backup} options={emps} onChange={(v: any) => setBackup(v)} isClearable placeholder="Chọn/tìm NSTM…" styles={selStyle} menuPortalTarget={portal} menuPosition="fixed" />
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4, fontWeight: 'normal' }}>
                Người thay thế khi NSTM chính vắng mặt. Có thể bỏ trống.
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
