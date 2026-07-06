import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'

type Row = {
  id: number; item_group_id: number; item_group_name: string
  primary_employee_id: number; primary_name: string; primary_code: string
  backup_employee_id: number; backup_name: string; backup_code: string
}

export default function CategoryAssignees() {
  const { can } = useAuth()
  const navigate = useNavigate()
  const canCreate = can('category_assignee', 'create')
  const canDelete = can('category_assignee', 'delete')

  const [rows, setRows] = useState<Row[]>([])
  const [cats, setCats] = useState<{ id: number; name: string }[]>([])
  const [fCat, setFCat] = useState('')     // filter phân loại (id)
  const [fName, setFName] = useState('')   // filter tên NSTM
  const [fCode, setFCode] = useState('')   // filter mã NV

  async function load() {
    const r = await api.get('/api/category-assignees')
    setRows(r.data.data.items || [])
  }
  useEffect(() => {
    api.get('/api/item-groups', { params: { page_size: 1000 } }).then(r => setCats(r.data.data.items || []))
    load()
  }, [])

  async function del(id: number) {
    if (!confirm('Xóa phân công này?')) return
    await api.delete(`/api/category-assignees/${id}`); await load()
  }

  const filtered = rows.filter(r =>
    (!fCat || String(r.item_group_id) === fCat) &&
    (!fName || `${r.primary_name || ''} ${r.backup_name || ''}`.toLowerCase().includes(fName.trim().toLowerCase())) &&
    (!fCode || `${r.primary_code || ''} ${r.backup_code || ''}`.toLowerCase().includes(fCode.trim().toLowerCase()))
  )

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 }}>
        <h2 className="page-title" style={{ margin: 0 }}>Phân công phụ trách (theo phân loại)</h2>
        {canCreate && <button className="btn" onClick={() => navigate('/category-assignees/new')}><i className="ti ti-plus" />Gán phân công</button>}
      </div>

      <div className="toolbar">
        <div className="toolbar-filter-item" style={{ maxWidth: 260 }}>
          <select value={fCat} onChange={e => setFCat(e.target.value)}>
            <option value="">— Tất cả phân loại —</option>
            {cats.map(c => <option key={c.id} value={c.id}>{c.name}</option>)}
          </select>
        </div>
        <div className="toolbar-filter-item"><input value={fName} onChange={e => setFName(e.target.value)} placeholder="Tìm theo tên NSTM…" /></div>
        <div className="toolbar-filter-item"><input value={fCode} onChange={e => setFCode(e.target.value)} placeholder="Tìm theo mã NV…" /></div>
        {(fCat || fName || fCode) && <button className="btn ghost" onClick={() => { setFCat(''); setFName(''); setFCode('') }}>Xóa lọc</button>}
      </div>

      <div className="card">
        <table>
          <thead><tr><th>Phân loại</th><th>NSTM chính</th><th>NSTM dự phòng</th><th style={{ width: 100, textAlign: 'center' }}>Thao tác</th></tr></thead>
          <tbody>
            {filtered.map(r => (
              <tr key={r.id}>
                <td><b>{r.item_group_name || '—'}</b></td>
                <td>{r.primary_name || '—'}{r.primary_code ? <span style={{ color: '#94a3b8', fontSize: 12 }}> · {r.primary_code}</span> : ''}</td>
                <td>{r.backup_name ? <>{r.backup_name}{r.backup_code ? <span style={{ color: '#94a3b8', fontSize: 12 }}> · {r.backup_code}</span> : ''}</> : <span style={{ color: '#94a3b8' }}>—</span>}</td>
                <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                  {canDelete && <button className="btn err" style={{ height: 30, padding: '0 8px' }} onClick={() => del(r.id)}><i className="ti ti-trash" />Xóa</button>}
                </td>
              </tr>
            ))}
            {filtered.length === 0 && <tr><td colSpan={4} style={{ textAlign: 'center', color: '#999', padding: 20 }}>Không có phân công nào khớp bộ lọc</td></tr>}
          </tbody>
        </table>
      </div>
    </div>
  )
}
