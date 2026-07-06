import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import Select from 'react-select'
import { api } from '../api/client'

type Opt = { value: number; label: string }
const selStyle = { control: (b: any) => ({ ...b, minHeight: 40, borderRadius: 12, borderColor: '#E9EDF7' }) }

export default function CategoryAssigneeNew() {
  const navigate = useNavigate()
  const [sp] = useSearchParams()

  const [cats, setCats] = useState<Opt[]>([])
  const [emps, setEmps] = useState<Opt[]>([])
  const [configured, setConfigured] = useState<Set<number>>(new Set())
  const [selCats, setSelCats] = useState<Opt[]>([])
  const [primary, setPrimary] = useState<Opt | null>(null)
  const [backup, setBackup] = useState<Opt | null>(null)
  const [err, setErr] = useState(''); const [saving, setSaving] = useState(false)

  useEffect(() => {
    api.get('/api/item-groups', { params: { page_size: 1000 } }).then(r => setCats((r.data.data.items || []).map((x: any) => ({ value: x.id, label: x.name }))))
    api.get('/api/employees', { params: { page_size: 1000 } }).then(r => setEmps((r.data.data.items || []).map((x: any) => ({ value: x.id, label: x.full_name + (x.code ? ` · ${x.code}` : '') }))))
    api.get('/api/category-assignees').then(r => setConfigured(new Set((r.data.data.items || []).map((x: any) => x.item_group_id))))
  }, [])

  // Prefill NSTM khi bấm Copy từ danh sách (?primary=&backup=)
  useEffect(() => {
    if (!emps.length) return
    const p = Number(sp.get('primary')); const b = Number(sp.get('backup'))
    if (p && !primary) setPrimary(emps.find(e => e.value === p) || null)
    if (b && !backup) setBackup(emps.find(e => e.value === b) || null)
  }, [emps])

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
      navigate('/category-assignees')
    } catch (e: any) { setErr(e.response?.data?.message || 'Lỗi lưu'); setSaving(false) }
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
            placeholder="Chọn/tìm phân loại…" styles={selStyle} closeMenuOnSelect={false}
            formatOptionLabel={(o: any) => <span>{o.label}{configured.has(o.value) ? <span style={{ color: '#d97706', fontSize: 11 }}> · đã có, sẽ ghi đè</span> : ''}</span>} />
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, marginBottom: 18 }}>
          <div className="form-row">
            <label>NSTM chính <span className="req" style={{ color: '#dc2626' }}>*</span></label>
            <Select classNamePrefix="rs" value={primary} options={emps} onChange={(v: any) => setPrimary(v)} isClearable placeholder="Chọn/tìm NSTM…" styles={selStyle} />
          </div>
          <div className="form-row">
            <label>NSTM dự phòng</label>
            <Select classNamePrefix="rs" value={backup} options={emps} onChange={(v: any) => setBackup(v)} isClearable placeholder="Chọn/tìm NSTM…" styles={selStyle} />
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
    </div>
  )
}
