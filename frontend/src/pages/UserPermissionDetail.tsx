import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'

const EMPTY = { companies: [], departments: [], employees: [], exclude_companies: [], exclude_departments: [], exclude_employees: [] }

export default function UserPermissionDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [u, setU] = useState<any>(null)
  const [roles, setRoles] = useState<any[]>([])
  const [roleSel, setRoleSel] = useState<number[]>([])
  const [companies, setCompanies] = useState<any[]>([])
  const [depts, setDepts] = useState<any[]>([])
  const [emps, setEmps] = useState<any[]>([])
  const [msg, setMsg] = useState(''); const [err, setErr] = useState('')

  // popup phạm vi theo vai trò
  const [popRole, setPopRole] = useState<number | null>(null)
  const [sc, setSc] = useState<any>({ ...EMPTY })
  const [empQ, setEmpQ] = useState('')
  const [empExclQ, setEmpExclQ] = useState('')
  const [empMode, setEmpMode] = useState(false)       // chỉ xem chứng từ của nhân sự: tùy chỉnh?
  const [empExclMode, setEmpExclMode] = useState(false) // loại trừ nhân sự: tùy chỉnh?

  useEffect(() => { load() }, [id])
  function load() {
    api.get(`/api/users/${id}`).then((r) => { setU(r.data.data); setRoleSel(r.data.data.role_ids || []) })
    api.get('/api/roles').then((r) => setRoles(r.data.data))
    api.get('/api/companies', { params: { page_size: 1000 } }).then((r) => setCompanies(r.data.data.items)).catch(() => {})
    api.get('/api/departments', { params: { page_size: 1000 } }).then((r) => setDepts(r.data.data.items)).catch(() => {})
    api.get('/api/employees', { params: { page_size: 2000 } }).then((r) => setEmps(r.data.data.items)).catch(() => {})
  }
  const empName = (eid: number) => { const e = emps.find((x) => x.id === eid); return e ? `${e.code} — ${e.full_name}` : String(eid) }
  const toggleRole = (rid: number) => setRoleSel((s) => s.includes(rid) ? s.filter((x) => x !== rid) : [...s, rid])

  async function saveRoles() {
    setMsg(''); setErr('')
    try { await api.put(`/api/users/${id}/roles`, { role_ids: roleSel }); setMsg('Đã lưu vai trò'); load() }
    catch (e: any) { setErr(e?.response?.data?.error?.message || 'Lỗi khi lưu vai trò') }
  }
  async function openScope(rid: number) {
    setPopRole(rid); setEmpQ(''); setEmpExclQ(''); setErr('')
    try {
      const r = await api.get(`/api/users/${id}/roles/${rid}/scope`)
      const data = { ...EMPTY, ...r.data.data }
      setSc(data)
      setEmpMode((data.employees || []).length > 0)
      setEmpExclMode((data.exclude_employees || []).length > 0)
    } catch { setSc({ ...EMPTY }); setEmpMode(false); setEmpExclMode(false) }
  }
  async function saveScope() {
    if (popRole == null) return
    try { await api.put(`/api/users/${id}/roles/${popRole}/scope`, sc); setPopRole(null); setMsg('Đã lưu phạm vi') }
    catch (e: any) { setErr(e?.response?.data?.error?.message || 'Lỗi khi lưu phạm vi') }
  }
  const tog = (key: string, v: any) => setSc((s: any) => ({ ...s, [key]: s[key].includes(v) ? s[key].filter((x: any) => x !== v) : [...s[key], v] }))

  const chip = (active: boolean, label: string, onClick: () => void, danger = false) => (
    <span onClick={onClick} className="clickable" title={label}
      style={{ fontSize: 12, padding: '4px 10px', borderRadius: 8, whiteSpace: 'nowrap',
        border: '1px solid ' + (active ? (danger ? '#e24b4a' : 'var(--teal)') : '#e2e8f0'),
        background: active ? (danger ? '#fdecea' : 'var(--info-bg)') : '#fff',
        color: active ? (danger ? '#a32d2d' : 'var(--teal)') : 'var(--ink)' }}>{label}</span>
  )
  const box = (title: string, children: any, danger = false) => (
    <div style={{ border: '1px solid #eef1f8', borderRadius: 10, padding: 12 }}>
      <div style={{ fontSize: 12, fontWeight: 700, color: danger ? '#a32d2d' : 'var(--navy)', marginBottom: 8 }}>{title}</div>
      {children}
    </div>
  )
  const matchEmp = (q: string) => q ? emps.filter((e) => (e.code + ' ' + e.full_name).toLowerCase().includes(q.toLowerCase())).slice(0, 40) : []
  const popRoleName = roles.find((r) => r.id === popRole)?.name || ''

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate('/roles')}><i className="ti ti-arrow-left" /></button>
        <div>
          <h2 className="page-title" style={{ margin: 0 }}>{u?.full_name || u?.email || 'Người dùng'}</h2>
          <div style={{ fontSize: 12.5, color: 'var(--muted)' }}>{u?.email} · {u?.department_name || 'Chưa có phòng ban'}</div>
        </div>
        <span style={{ flex: 1 }} />
        {msg && <span style={{ color: 'var(--green)', fontSize: 13 }}>{msg}</span>}
        <button className="btn" onClick={saveRoles}><i className="ti ti-device-floppy" />Lưu vai trò</button>
      </div>
      {err && <div className="err">{err}</div>}

      <div className="hz-card" style={{ padding: 18 }}>
        <h3 className="hz-title" style={{ marginBottom: 4 }}>Vai trò &amp; phạm vi</h3>
        <div className="hz-sub" style={{ display: 'block', marginBottom: 14 }}>Tick vai trò để gán. Mỗi vai trò đã gán bấm "Phạm vi" để giới hạn công ty / phòng ban / nhân sự riêng.</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {roles.map((r) => {
            const on = roleSel.includes(r.id)
            const saved = (u?.role_ids || []).includes(r.id)
            return (
              <div key={r.id} style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 10px', border: '1px solid #eef1f8', borderRadius: 10, background: on ? 'var(--info-bg)' : '#fff' }}>
                <label style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', flex: 1 }}>
                  <input type="checkbox" checked={on} onChange={() => toggleRole(r.id)} style={{ width: 16, height: 16 }} />
                  <span style={{ fontWeight: 600, color: 'var(--navy)' }}>{r.name}</span>
                  <span style={{ fontSize: 11, color: 'var(--muted)' }}>{r.code}</span>
                </label>
                {saved && <button className="btn ghost" style={{ height: 30, padding: '0 12px' }} onClick={() => openScope(r.id)}><i className="ti ti-filter" />Phạm vi</button>}
                {on && !saved && <span style={{ fontSize: 11, color: 'var(--amber)' }}>Lưu vai trò trước để đặt phạm vi</span>}
              </div>
            )
          })}
        </div>
      </div>

      {popRole != null && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(27,37,89,.3)', zIndex: 200, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '5vh 12px', overflowY: 'auto' }}
          onClick={() => setPopRole(null)}>
          <div className="hz-card" style={{ width: 720, maxWidth: '100%', padding: 20 }} onClick={(e) => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
              <h3 className="hz-title" style={{ margin: 0 }}>Phạm vi — {popRoleName}</h3>
              <span className="clickable" style={{ color: '#94a3b8', fontSize: 18 }} onClick={() => setPopRole(null)}><i className="ti ti-x" /></span>
            </div>
            <div className="hz-sub" style={{ display: 'block', marginBottom: 14 }}>Để trống = không giới hạn chiều đó. Chỉ áp cho vai trò này.</div>

            <div className="grid-2" style={{ gap: 12, marginBottom: 12 }}>
              {box('Công ty được xem', (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, maxHeight: 140, overflowY: 'auto' }}>
                  {companies.map((c) => chip(sc.companies.includes(c.id), c.code || c.name, () => tog('companies', c.id)))}
                </div>
              ))}
              {box('Phòng ban được xem', (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, maxHeight: 140, overflowY: 'auto' }}>
                  {depts.map((d) => chip(sc.departments.includes(d.name), d.name, () => tog('departments', d.name)))}
                </div>
              ))}
            </div>

            {box('Chỉ xem chứng từ do nhân sự tạo', (
              !empMode ? (
                <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                  <span style={{ fontSize: 12.5, color: 'var(--muted)' }}>Mặc định: không giới hạn theo nhân sự.</span>
                  <button className="btn ghost" style={{ height: 28, padding: '0 12px' }} onClick={() => setEmpMode(true)}>Tùy chỉnh</button>
                </div>
              ) : (
                <>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                    <span style={{ fontSize: 11.5, color: 'var(--muted)' }}>Chọn nhân sự — chỉ xem chứng từ của họ</span>
                    <span className="clickable" style={{ fontSize: 11.5, color: 'var(--red)' }} onClick={() => { setEmpMode(false); setSc((s: any) => ({ ...s, employees: [] })) }}>Bỏ giới hạn</span>
                  </div>
                  {sc.employees.length > 0 && <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>{sc.employees.map((eid: number) => chip(true, empName(eid), () => tog('employees', eid)))}</div>}
                  <input placeholder="Gõ mã / tên để tìm nhân sự…" value={empQ} onChange={(e) => setEmpQ(e.target.value)} style={{ height: 32, marginBottom: 8, width: '100%' }} />
                  {empQ
                    ? <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, maxHeight: 150, overflowY: 'auto' }}>{matchEmp(empQ).map((e) => chip(sc.employees.includes(e.id), `${e.code} — ${e.full_name}`, () => tog('employees', e.id)))}</div>
                    : <span style={{ fontSize: 11.5, color: 'var(--hz-muted)' }}>Gõ để tìm và chọn nhân sự.</span>}
                </>
              )
            ))}

            <div style={{ marginTop: 12 }}>
              {box('Loại trừ phòng ban', (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, maxHeight: 110, overflowY: 'auto' }}>
                  {depts.map((d) => chip(sc.exclude_departments.includes(d.name), d.name, () => tog('exclude_departments', d.name), true))}
                </div>
              ), true)}
            </div>

            <div style={{ marginTop: 12 }}>
              {box('Loại trừ nhân sự', (
                !empExclMode ? (
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontSize: 12.5, color: 'var(--muted)' }}>Không loại trừ nhân sự.</span>
                    <button className="btn ghost" style={{ height: 28, padding: '0 12px' }} onClick={() => setEmpExclMode(true)}>Tùy chỉnh</button>
                  </div>
                ) : (
                  <>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 6 }}>
                      <span style={{ fontSize: 11.5, color: 'var(--muted)' }}>Chọn nhân sự để ẩn chứng từ của họ</span>
                      <span className="clickable" style={{ fontSize: 11.5, color: 'var(--red)' }} onClick={() => { setEmpExclMode(false); setSc((s: any) => ({ ...s, exclude_employees: [] })) }}>Bỏ</span>
                    </div>
                    {sc.exclude_employees.length > 0 && <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, marginBottom: 8 }}>{sc.exclude_employees.map((eid: number) => chip(true, empName(eid), () => tog('exclude_employees', eid), true))}</div>}
                    <input placeholder="Gõ mã / tên để tìm nhân sự…" value={empExclQ} onChange={(e) => setEmpExclQ(e.target.value)} style={{ height: 32, marginBottom: 8, width: '100%' }} />
                    {empExclQ
                      ? <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, maxHeight: 150, overflowY: 'auto' }}>{matchEmp(empExclQ).map((e) => chip(sc.exclude_employees.includes(e.id), `${e.code} — ${e.full_name}`, () => tog('exclude_employees', e.id), true))}</div>
                      : <span style={{ fontSize: 11.5, color: 'var(--hz-muted)' }}>Gõ để tìm và chọn nhân sự.</span>}
                  </>
                )
              ), true)}
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
              <button className="btn ghost" onClick={() => setPopRole(null)}>Hủy</button>
              <button className="btn" onClick={saveScope}><i className="ti ti-device-floppy" />Lưu phạm vi</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
