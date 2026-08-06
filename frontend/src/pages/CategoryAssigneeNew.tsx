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

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16 }}>
        <button className="btn ghost" style={{ height: 36 }} onClick={() => navigate('/category-assignees')}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>Gán phân công phụ trách</h2>
      </div>

      <div className="card" style={{ padding: 22, maxWidth: 760 }}>
        <div className="form-row" style={{ marginBottom: 16 }}>
          <label>Phân loại VTBB <span style={{ color: '#94a3b8', fontWeight: 400 }}>(chọn nhiều)</span></label>
          <Select isMulti classNamePrefix="rs" value={selCats} options={cats} onChange={(v: any) => setSelCats(v || [])}
            placeholder="Chọn/tìm phân loại…" styles={selStyle} menuPortalTarget={portal} menuPosition="fixed" closeMenuOnSelect={false}
            formatOptionLabel={(o: any) => <span>{o.label}{configured.has(o.value) ? <span style={{ color: '#d97706', fontSize: 11 }}> · đã có, sẽ ghi đè</span> : ''}</span>} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 18 }}>
          <div className="form-row">
            <label>NSTM chính <span className="req" style={{ color: '#dc2626' }}>*</span></label>
            <Select classNamePrefix="rs" value={primary} options={emps} onChange={(v: any) => setPrimary(v)} isClearable placeholder="Chọn/tìm NSTM…" styles={selStyle} menuPortalTarget={portal} menuPosition="fixed" />
          </div>
          <div className="form-row">
            <label>NSTM dự phòng</label>
            <Select classNamePrefix="rs" value={backup} options={emps} onChange={(v: any) => setBackup(v)} isClearable placeholder="Chọn/tìm NSTM…" styles={selStyle} menuPortalTarget={portal} menuPosition="fixed" />
          </div>
        </div>

        {err && <div className="err" style={{ marginBottom: 12 }}>{err}</div>}
        <div style={{ display: 'flex', gap: 10 }}>
          <button className="btn" disabled={saving} onClick={save}><i className="ti ti-check" />{saving ? 'Đang lưu…' : 'Lưu phân công'}</button>
          <button className="btn ghost" onClick={() => navigate('/category-assignees')}>Hủy</button>
        </div>
        <p style={{ color: 'var(--muted)', fontSize: 12.5, marginTop: 14 }}>
          Cặp NSTM (chính + dự phòng) sẽ được gán cho <b>tất cả phân loại đã chọn</b>. Phân loại đã có sẽ được <b>ghi đè</b>.
        </p>
      </div>

      {/* Lịch sử thao tác — chỉ hiện khi đang sửa 1 phân loại đã cấu hình */}
      {editRowId && (
        <div className="card" style={{ padding: 18, maxWidth: 760, marginTop: 14 }}>
          <h3 style={{ fontSize: 14, color: 'var(--navy)', marginBottom: 12 }}><i className="ti ti-history" /> Lịch sử thao tác</h3>
          {logs.length === 0 ? (
            <div style={{ color: '#999', fontSize: 13 }}>Chưa có log.</div>
          ) : (
            <AuditTimeline logs={logs} />
          )}
        </div>
      )}
    </div>
  )
}
