import { useEffect, useState } from 'react'
import Select from 'react-select'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'

type Opt = { value: number; label: string }
type Row = {
  id: number; item_group_id: number; item_group_name: string
  primary_employee_id: number; primary_name: string
  backup_employee_id: number; backup_name: string
}

const selStyle = { control: (b: any) => ({ ...b, minHeight: 40, borderRadius: 12, borderColor: '#E9EDF7' }) }

export default function CategoryAssignees() {
  const { can } = useAuth()
  const canCreate = can('category_assignee', 'create')
  const canDelete = can('category_assignee', 'delete')

  const [cats, setCats] = useState<Opt[]>([])
  const [emps, setEmps] = useState<Opt[]>([])
  const [rows, setRows] = useState<Row[]>([])
  const [selCats, setSelCats] = useState<Opt[]>([])
  const [primary, setPrimary] = useState<Opt | null>(null)
  const [backup, setBackup] = useState<Opt | null>(null)
  const [msg, setMsg] = useState(''); const [err, setErr] = useState('')

  async function loadRows() {
    const r = await api.get('/api/category-assignees')
    setRows(r.data.data.items || [])
  }
  useEffect(() => {
    api.get('/api/item-groups', { params: { page_size: 1000 } }).then(r => setCats((r.data.data.items || []).map((x: any) => ({ value: x.id, label: x.name }))))
    api.get('/api/employees', { params: { page_size: 1000 } }).then(r => setEmps((r.data.data.items || []).map((x: any) => ({ value: x.id, label: x.full_name }))))
    loadRows()
  }, [])

  const configuredIds = new Set(rows.map(r => r.item_group_id))
  const empOpt = (id: number) => emps.find(e => e.value === id) || null

  async function addBulk() {
    setErr(''); setMsg('')
    if (selCats.length === 0) { setErr('Chọn ít nhất 1 phân loại'); return }
    if (!primary) { setErr('Chọn NSTM chính'); return }
    try {
      const r = await api.post('/api/category-assignees/bulk', {
        item_group_ids: selCats.map(c => c.value),
        primary_employee_id: primary.value,
        backup_employee_id: backup?.value || 0,
      })
      setMsg(r.data.message || 'Đã lưu'); setSelCats([])
      await loadRows()
    } catch (e: any) { setErr(e.response?.data?.message || 'Lỗi lưu') }
  }
  function copyRow(row: Row) {
    setPrimary(empOpt(row.primary_employee_id))
    setBackup(empOpt(row.backup_employee_id))
    setSelCats([])
    setMsg('Đã copy NSTM — chọn phân loại khác rồi bấm "Thêm hàng loạt"'); setErr('')
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
  async function del(id: number) {
    if (!confirm('Xóa phân công này?')) return
    try { await api.delete(`/api/category-assignees/${id}`); await loadRows() }
    catch (e: any) { setErr(e.response?.data?.message || 'Lỗi xóa') }
  }

  return (
    <div>
      <h2 className="page-title" style={{ marginBottom: 12 }}>Phân công phụ trách (theo phân loại)</h2>

      {canCreate && (
        <div className="card" style={{ padding: 18, marginBottom: 16 }}>
          <h3 className="sec-title">Gán hàng loạt</h3>
          <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr 1fr auto', gap: 12, alignItems: 'end' }}>
            <div>
              <label>Phân loại VTBB (chọn nhiều)</label>
              <Select isMulti value={selCats} options={cats} onChange={(v: any) => setSelCats(v || [])}
                placeholder="Chọn/tìm phân loại…" styles={selStyle} closeMenuOnSelect={false}
                formatOptionLabel={(o: any) => <span>{o.label}{configuredIds.has(o.value) ? <span style={{ color: '#d97706', fontSize: 11 }}> · đã có, sẽ ghi đè</span> : ''}</span>} />
            </div>
            <div><label>NSTM chính</label>
              <Select value={primary} options={emps} onChange={(v: any) => setPrimary(v)} isClearable placeholder="Chọn…" styles={selStyle} /></div>
            <div><label>NSTM dự phòng</label>
              <Select value={backup} options={emps} onChange={(v: any) => setBackup(v)} isClearable placeholder="Chọn…" styles={selStyle} /></div>
            <button className="btn" style={{ height: 40 }} onClick={addBulk}><i className="ti ti-plus" />Thêm hàng loạt</button>
          </div>
          {msg && <div style={{ color: 'var(--green)', marginTop: 10, fontSize: 13 }}>{msg}</div>}
          {err && <div className="err" style={{ marginTop: 10 }}>{err}</div>}
        </div>
      )}

      <div className="card">
        <table>
          <thead><tr><th>Phân loại</th><th>NSTM chính</th><th>NSTM dự phòng</th><th style={{ width: 130, textAlign: 'center' }}>Thao tác</th></tr></thead>
          <tbody>
            {rows.map(r => (
              <tr key={r.id}>
                <td><b>{r.item_group_name || '—'}</b></td>
                <td>{r.primary_name || '—'}</td>
                <td>{r.backup_name || <span style={{ color: '#94a3b8' }}>—</span>}</td>
                <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                  {canCreate && <button className="btn ghost" style={{ height: 30, padding: '0 8px', marginRight: 6 }} title="Copy NSTM sang phân loại khác" onClick={() => copyRow(r)}><i className="ti ti-copy" />Copy</button>}
                  {canDelete && <button className="btn err" style={{ height: 30, padding: '0 8px' }} onClick={() => del(r.id)}><i className="ti ti-trash" /></button>}
                </td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={4} style={{ textAlign: 'center', color: '#999', padding: 20 }}>Chưa có phân công nào</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
