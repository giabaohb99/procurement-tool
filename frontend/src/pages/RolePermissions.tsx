import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'

type Opt = { key: string; label: string }
type Meta = { entities: Opt[]; actions: Opt[]; scopes: Opt[] }
type Row = { scope: string; [k: string]: any }

export default function RolePermissions() {
  const navigate = useNavigate()
  const [meta, setMeta] = useState<Meta | null>(null)
  const [roles, setRoles] = useState<any[]>([])
  const [sel, setSel] = useState<number | null>(null)
  const [perm, setPerm] = useState<Record<string, Row>>({})
  const [msg, setMsg] = useState(''); const [err, setErr] = useState('')
  const [adding, setAdding] = useState(false); const [nc, setNc] = useState({ code: '', name: '' })
  const [tab, setTab] = useState<'roles' | 'users'>('roles')
  const [roleSearch, setRoleSearch] = useState('')
  const [users, setUsers] = useState<any[]>([])
  const [uTotal, setUTotal] = useState(0)
  const [uPage, setUPage] = useState(1)
  const [uSearch, setUSearch] = useState('')
  const PAGE = 20

  useEffect(() => { api.get('/api/roles/meta').then((r) => setMeta(r.data.data)); loadRoles() }, [])
  function loadRoles() { api.get('/api/roles').then((r) => setRoles(r.data.data)) }
  function loadUsers() {
    api.get('/api/users', { params: { search: uSearch, page: uPage, page_size: PAGE } })
      .then((r) => { setUsers(r.data.data.items); setUTotal(r.data.data.total) })
  }
  useEffect(() => { if (tab !== 'users') return; const t = setTimeout(loadUsers, 300); return () => clearTimeout(t) }, [tab, uPage, uSearch])
  const uPages = Math.max(1, Math.ceil(uTotal / PAGE))
  const roleName = (id: number) => roles.find((r) => r.id === id)?.name || String(id)

  const actionKeys = meta ? meta.actions.map((a) => a.key) : []
  const row = (e: string): Row => perm[e] || { scope: 'own', ...Object.fromEntries(actionKeys.map((a) => ['can_' + a, false])) }

  async function selectRole(id: number) {
    setSel(id); setMsg(''); setErr('')
    const r = await api.get(`/api/roles/${id}/permissions`)
    const map: Record<string, Row> = {}
    r.data.data.forEach((p: any) => { map[p.entity] = p })
    setPerm(map)
  }
  const toggle = (e: string, a: string) => setPerm((p) => ({ ...p, [e]: { ...row(e), ['can_' + a]: !row(e)['can_' + a] } }))
  const setScope = (e: string, s: string) => setPerm((p) => ({ ...p, [e]: { ...row(e), scope: s } }))
  const rowAll = (e: string) => {
    const on = !actionKeys.every((a) => row(e)['can_' + a])
    setPerm((p) => { const cur = { ...row(e) }; actionKeys.forEach((a) => (cur['can_' + a] = on)); return { ...p, [e]: cur } })
  }

  async function save() {
    if (!sel) return
    setMsg(''); setErr('')
    const permissions = (meta?.entities || []).map((e) => ({
      entity: e.key, scope: row(e.key).scope || 'own',
      ...Object.fromEntries(actionKeys.map((a) => ['can_' + a, !!row(e.key)['can_' + a]])),
    })).filter((x) => actionKeys.some((a) => (x as any)['can_' + a]))
    try { await api.put(`/api/roles/${sel}/permissions`, { permissions }); setMsg('Đã lưu quyền') }
    catch (e: any) { setErr(e?.response?.data?.error?.message || 'Lỗi khi lưu') }
  }
  async function createRole() {
    setErr('')
    try {
      const r = await api.post('/api/roles', { code: nc.code || 'role_' + Math.random().toString(36).slice(2, 8), name: nc.name || nc.code })
      setAdding(false); setNc({ code: '', name: '' }); loadRoles(); selectRole(r.data.data.id)
    } catch (e: any) { setErr(e?.response?.data?.error?.message || 'Lỗi tạo vai trò') }
  }
  async function delRole() {
    if (!sel || !confirm('Xóa vai trò này?')) return
    try { await api.delete(`/api/roles/${sel}`); setSel(null); setPerm({}); loadRoles() }
    catch (e: any) { setErr(e?.response?.data?.error?.message || 'Lỗi khi xóa') }
  }

  const selRole = roles.find((r) => r.id === sel)

  return (
    <div>
      <h2 className="page-title">Phân quyền</h2>
      <div style={{ display: 'flex', gap: 6, marginBottom: 16 }}>
        <button className={'btn ' + (tab === 'roles' ? '' : 'ghost')} onClick={() => setTab('roles')}>Vai trò &amp; quyền</button>
        <button className={'btn ' + (tab === 'users' ? '' : 'ghost')} onClick={() => setTab('users')}>Người dùng</button>
      </div>

      {tab === 'users' ? (
        <div className="hz-card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '12px 16px', display: 'flex', gap: 10, alignItems: 'center', borderBottom: '1px solid var(--border)' }}>
            <input placeholder="Tìm theo tên / email / mã NV…" value={uSearch}
              onChange={(e) => { setUSearch(e.target.value); setUPage(1) }} style={{ flex: 1, maxWidth: 340 }} />
            <span style={{ fontSize: 12.5, color: 'var(--muted)' }}>{uTotal} tài khoản</span>
          </div>
          <table>
            <thead><tr><th>Người dùng</th><th>Phòng ban</th><th>Vai trò</th><th style={{ width: 90 }}></th></tr></thead>
            <tbody>
              {users.map((u) => (
                <tr key={u.id} className="clickable" onClick={() => navigate(`/users/${u.id}`)}>
                  <td>{u.full_name || u.email}<div style={{ fontSize: 11, color: 'var(--muted)' }}>{u.email}</div></td>
                  <td>{u.department_name || '—'}</td>
                  <td>
                    {(u.role_ids || []).length ? (
                      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
                        {u.role_ids.slice(0, 3).map((id: number) => <span key={id} className="badge gray">{roleName(id)}</span>)}
                        {u.role_ids.length > 3 && <span className="badge gray" title={u.role_ids.slice(3).map(roleName).join(', ')}>+{u.role_ids.length - 3}</span>}
                      </div>
                    ) : <span style={{ color: 'var(--muted)' }}>Chưa gán</span>}
                  </td>
                  <td style={{ textAlign: 'right' }}>
                    <button className="btn ghost" style={{ height: 28, padding: '0 10px' }} onClick={(e) => { e.stopPropagation(); navigate(`/users/${u.id}`) }}>Sửa</button>
                  </td>
                </tr>
              ))}
              {users.length === 0 && <tr><td colSpan={4} style={{ textAlign: 'center', color: 'var(--muted)', padding: 20 }}>Chưa có tài khoản</td></tr>}
            </tbody>
          </table>
          <div className="pager" style={{ padding: '10px 16px' }}>
            <button className="btn ghost" disabled={uPage <= 1} onClick={() => setUPage((p) => Math.max(1, p - 1))}>Trước</button>
            <span>Trang {uPage} / {uPages}</span>
            <button className="btn ghost" disabled={uPage >= uPages} onClick={() => setUPage((p) => Math.min(uPages, p + 1))}>Sau</button>
          </div>
        </div>
      ) : (
        <div className="grid-1-2" style={{ gridTemplateColumns: '260px 1fr' }}>
          <div className="hz-card" style={{ padding: 14 }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 }}>
              <b style={{ fontSize: 14 }}>Vai trò</b>
              <button className="btn" style={{ height: 30, padding: '0 10px' }} onClick={() => setAdding(true)}><i className="ti ti-plus" />Thêm</button>
            </div>
            {adding && (
              <div style={{ border: '1px dashed var(--border)', borderRadius: 8, padding: 10, marginBottom: 10, display: 'flex', flexDirection: 'column', gap: 6 }}>
                <input placeholder="Mã (vd pur_staff)" value={nc.code} onChange={(e) => setNc({ ...nc, code: e.target.value })} style={{ height: 32 }} />
                <input placeholder="Tên vai trò" value={nc.name} onChange={(e) => setNc({ ...nc, name: e.target.value })} style={{ height: 32 }} />
                <div style={{ display: 'flex', gap: 6 }}>
                  <button className="btn" style={{ height: 30 }} onClick={createRole}>Tạo</button>
                  <button className="btn ghost" style={{ height: 30 }} onClick={() => setAdding(false)}>Hủy</button>
                </div>
              </div>
            )}
            <input placeholder="Tìm vai trò…" value={roleSearch} onChange={(e) => setRoleSearch(e.target.value)} style={{ height: 32, marginBottom: 8 }} />
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2, maxHeight: '62vh', overflowY: 'auto' }}>
              {roles.filter((r) => !roleSearch || (r.name + ' ' + r.code).toLowerCase().includes(roleSearch.toLowerCase())).map((r) => (
                <div key={r.id} onClick={() => selectRole(r.id)} className="clickable"
                  style={{ padding: '8px 10px', borderRadius: 8, fontSize: 13, background: sel === r.id ? 'var(--info-bg)' : 'transparent', color: sel === r.id ? 'var(--teal)' : 'var(--ink)', fontWeight: sel === r.id ? 600 : 400 }}>
                  {r.name}<div style={{ fontSize: 11, color: 'var(--muted)' }}>{r.code}</div>
                </div>
              ))}
            </div>
          </div>

          <div className="hz-card" style={{ padding: 16 }}>
            {!selRole ? <div style={{ color: 'var(--muted)', fontSize: 13, padding: 20 }}>Chọn một vai trò để xem/chỉnh ma trận quyền.</div> : (
              <>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 12, flexWrap: 'wrap', gap: 8 }}>
                  <div><b style={{ fontSize: 15 }}>{selRole.name}</b> <span style={{ color: 'var(--muted)', fontSize: 12 }}>({selRole.code})</span></div>
                  <div style={{ display: 'flex', gap: 8 }}>
                    {msg && <span style={{ color: 'var(--green)', fontSize: 13, alignSelf: 'center' }}>{msg}</span>}
                    <button className="btn" onClick={save}><i className="ti ti-device-floppy" />Lưu quyền</button>
                    <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={delRole}><i className="ti ti-trash" /></button>
                  </div>
                </div>
                {err && <div className="err">{err}</div>}
                <div className="items-scroll">
                  <table className="items-table" style={{ minWidth: 780 }}>
                    <thead>
                      <tr>
                        <th style={{ textAlign: 'left', minWidth: 150 }}>Chức năng</th>
                        {meta?.actions.map((a) => <th key={a.key}>{a.label}</th>)}
                        <th style={{ minWidth: 120 }}>Phạm vi</th>
                      </tr>
                    </thead>
                    <tbody>
                      {meta?.entities.map((e) => (
                        <tr key={e.key}>
                          <td style={{ textAlign: 'left' }}>
                            {e.label}
                            <span onClick={() => rowAll(e.key)} className="clickable" style={{ marginLeft: 6, fontSize: 10.5, color: 'var(--teal)' }}>tất cả</span>
                          </td>
                          {actionKeys.map((a) => (
                            <td key={a} style={{ textAlign: 'center' }}>
                              <input type="checkbox" checked={!!row(e.key)['can_' + a]} onChange={() => toggle(e.key, a)} style={{ width: 16, height: 16 }} />
                            </td>
                          ))}
                          <td>
                            <select value={row(e.key).scope || 'own'} onChange={(ev) => setScope(e.key, ev.target.value)} style={{ height: 30, fontSize: 12.5 }}>
                              {meta?.scopes.map((s) => <option key={s.key} value={s.key}>{s.label}</option>)}
                            </select>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <div style={{ fontSize: 11.5, color: 'var(--muted)', marginTop: 10 }}>
                  Phạm vi mặc định của vai trò (Của mình / Phòng ban / Công ty / Tất cả). Phạm vi RIÊNG theo từng nhân viên chỉnh ở trang chi tiết Người dùng.
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
