import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { askConfirm } from './confirm'
import { fmtDateTime } from '../utils/datetime'
import { useAuth } from '../auth/AuthContext'
import { cruds } from '../config/cruds'
import SearchSelect from './SearchSelect'
import NotFound from './NotFound'

export default function CrudDetail() {
  const { entity, id } = useParams()
  const cfg = cruds[entity || '']
  const { can } = useAuth()
  const navigate = useNavigate()
  const isNew = id === 'new'

  const [form, setForm] = useState<any>({})
  const [logs, setLogs] = useState<any[]>([])
  const [err, setErr] = useState('')
  const [msg, setMsg] = useState('')
  const [notFound, setNotFound] = useState(false)
  const [dynOpts, setDynOpts] = useState<Record<string, { value: string; label: string }[]>>({})
  const [pwOpen, setPwOpen] = useState(false)
  const [pw1, setPw1] = useState(''); const [pw2, setPw2] = useState('')

  async function loadLogs() {
    if (isNew || !cfg) return
    const r = await api.get('/api/audit-logs', { params: { entity: cfg.entity, entity_id: id } })
    setLogs(r.data.data)
  }

  useEffect(() => {
    if (!cfg) return
    cfg.fields.filter(f => f.source).forEach(f => {
      api.get(f.source!.url, { params: { page_size: 1000 } }).then(r => {
        const vk = f.source!.value || 'code'
        const lk = f.source!.label || 'name'
        const data = r.data.data
        const items = Array.isArray(data) ? data : (data.items || [])
        const opts = items.map((it: any) => ({
          value: String(it[vk] ?? ''), label: String(it[lk] ?? it[vk] ?? ''),
        })).filter((o: any) => o.value)
        setDynOpts(s => ({ ...s, [f.key]: opts }))
      }).catch(() => {})
    })
  }, [cfg?.slug])

  useEffect(() => {
    if (!cfg) return
    setErr(''); setMsg(''); setNotFound(false)
    if (isNew) {
      const init: any = {}
      cfg.fields.forEach((f) => {
        if (f.key === 'is_active') {
          init[f.key] = f.type === 'checkbox' ? true : 'true'
        } else {
          init[f.key] = f.type === 'checkbox' ? true : f.type === 'number' ? 0 : ''
        }
      })
      setForm(init); setLogs([])
    } else {
      api.get(`${cfg.apiPath}/${id}`).then((r) => setForm(r.data.data))
        .catch((ex) => { if ([403, 404].includes(ex?.response?.status)) setNotFound(true) })
      loadLogs()
    }
  }, [cfg?.slug, id])

  if (!cfg) return <div>Không tìm thấy trang.</div>
  if (notFound) return <NotFound backTo={`/${cfg.slug}`} message={`Không tìm thấy ${cfg.title.toLowerCase()} này hoặc bạn không có quyền truy cập.`} />

  // Danh mục chỉ dành cho người QUẢN LÝ (write/create/delete); read chỉ để đổ dropdown.
  const canManage = can(cfg.entity, 'write') || can(cfg.entity, 'create') || can(cfg.entity, 'delete')
  if (!canManage) return (
    <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--muted)' }}>
      <i className="ti ti-lock" style={{ fontSize: 34, color: '#cbd5e1' }} />
      <div style={{ marginTop: 12, fontSize: 15, color: 'var(--navy)', fontWeight: 600 }}>Không có quyền quản lý danh mục này</div>
      <button className="btn" style={{ marginTop: 16 }} onClick={() => navigate('/')}><i className="ti ti-home" />Về Trang chủ</button>
    </div>
  )

  const set = (k: string, v: any) => setForm((s: any) => ({ ...s, [k]: v }))
  const canSave = isNew ? can(cfg.entity, 'create') : can(cfg.entity, 'write')

  async function save() {
    setErr(''); setMsg('')
    try {
      if (isNew) {
        const r = await api.post(cfg.apiPath, form)
        navigate(`/${cfg.slug}/${r.data.data.id}`)
      } else {
        await api.patch(`${cfg.apiPath}/${id}`, form)
        setMsg('Đã lưu'); loadLogs()
      }
    } catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi khi lưu') }
  }

  async function remove() {
    if (!(await askConfirm({ message: 'Xóa bản ghi này?' }))) return
    try { await api.delete(`${cfg.apiPath}/${id}`); navigate(`/${cfg.slug}`) }
    catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi khi xóa') }
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
        <button className="btn ghost" onClick={() => navigate(`/${cfg.slug}`)}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>{isNew ? `Thêm ${cfg.title}` : `${cfg.title} #${id}`}</h2>
      </div>

      <div className="detail-grid">
        <div className="card" style={{ padding: 18 }}>
          <div className="form-grid">
            {cfg.fields.map((f) => {
              const ro = (!isNew && f.readonlyOnEdit) || !canSave   // không có quyền lưu → khóa field
              return (
                <div key={f.key} className="form-row">
                  <label>{f.label}</label>
                  {f.type === 'textarea' ? (
                    <textarea value={form[f.key] ?? ''} disabled={ro} onChange={(e) => set(f.key, e.target.value)} />
                  ) : (f.type === 'select' || (f.source && f.type !== 'select-multiple')) ? (
                    <SearchSelect value={form[f.key] ?? ''} disabled={ro} placeholder="Chọn…"
                      colorMap={f.colorMap}
                      options={(f.options || dynOpts[f.key] || [])}
                      onChange={(v) => {
                        set(f.key, v);
                        if (f.onValueChange) f.onValueChange(v, form, (k: string, val: any) => setForm((s: any) => ({ ...s, [k]: val })));
                      }} />
                  ) : f.type === 'select-multiple' ? (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 6, marginTop: 4 }}>
                      {(f.options || dynOpts[f.key] || []).map((o) => {
                        const checked = Array.isArray(form[f.key]) && form[f.key].includes(Number(o.value))
                        return (
                          <label key={o.value} style={{ display: 'flex', alignItems: 'center', gap: 8, fontWeight: 'normal' }}>
                            <input type="checkbox" checked={checked} disabled={ro} onChange={(e) => {
                              const curr = Array.isArray(form[f.key]) ? [...form[f.key]] : []
                              if (e.target.checked) curr.push(Number(o.value))
                              else {
                                const idx = curr.indexOf(Number(o.value))
                                if (idx > -1) curr.splice(idx, 1)
                              }
                              set(f.key, curr)
                            }} /> {o.label}
                          </label>
                        )
                      })}
                    </div>
                  ) : f.type === 'checkbox' ? (
                    <input type="checkbox" checked={!!form[f.key]} disabled={ro} onChange={(e) => set(f.key, e.target.checked)} />
                  ) : (
                    <input type={f.type === 'number' ? 'number' : f.type === 'date' ? 'date' : 'text'}
                           value={f.zeroAsBlank && form[f.key] === 0 ? '' : (form[f.key] ?? '')} disabled={ro}
                           onChange={(e) => set(f.key, f.type === 'number' ? Number(e.target.value) : e.target.value)} />
                  )}
                </div>
              )
            })}
          </div>
          {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}
          {msg && <div style={{ color: 'var(--green)', marginTop: 12, fontSize: 13 }}>{msg}</div>}
          <div style={{ display: 'flex', gap: 8, marginTop: 16, flexWrap: 'wrap' }}>
            {canSave && <button className="btn" onClick={save}>{isNew ? 'Tạo' : 'Lưu'}</button>}

            {!isNew && cfg.slug === 'employees' && can(cfg.entity, 'write') && (
              <button className="btn outline" style={{ color: 'var(--teal)', borderColor: 'var(--teal)', background: '#fff' }}
                onClick={() => { setPwOpen((o) => !o); setErr(''); setMsg('') }}>
                <i className="ti ti-key" />Đặt lại mật khẩu
              </button>
            )}
            {!isNew && cfg.slug === 'employees' && can('user', 'read') && (
              <button className="btn ghost" onClick={async () => {
                setErr('')
                try {
                  const r = await api.get('/api/users', { params: { search: form.code || form.email || form.full_name, page_size: 20 } })
                  const u = (r.data.data.items || []).find((x: any) => x.employee_id === Number(id))
                  if (u) navigate(`/users/${u.id}`); else setErr('Nhân sự này chưa có tài khoản để phân quyền')
                } catch { setErr('Không mở được phân quyền') }
              }}><i className="ti ti-shield" />Phân quyền tài khoản</button>
            )}

            {!isNew && can(cfg.entity, 'delete') && (
              <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={remove}>
                <i className="ti ti-trash" />Xóa
              </button>
            )}
          </div>

          {/* Ô đặt lại mật khẩu trực tiếp (pass1/pass2) */}
          {pwOpen && !isNew && cfg.slug === 'employees' && (
            <div style={{ marginTop: 14, padding: 14, border: '1px solid var(--border)', borderRadius: 10, background: '#f8fafc' }}>
              <div style={{ fontWeight: 600, color: 'var(--navy)', marginBottom: 10 }}>Đặt lại mật khẩu tài khoản</div>
              <div className="form-grid">
                <div className="form-row"><label>Mật khẩu mới</label><input type="password" autoComplete="new-password" value={pw1} onChange={(e) => setPw1(e.target.value)} /></div>
                <div className="form-row"><label>Nhập lại mật khẩu</label><input type="password" autoComplete="new-password" value={pw2} onChange={(e) => setPw2(e.target.value)} /></div>
              </div>
              <div style={{ display: 'flex', gap: 8, marginTop: 10 }}>
                <button className="btn" onClick={async () => {
                  setErr(''); setMsg('')
                  if (pw1.length < 4) { setErr('Mật khẩu tối thiểu 4 ký tự'); return }
                  if (pw1 !== pw2) { setErr('Hai mật khẩu không khớp'); return }
                  try { await api.post(`/api/employees/${id}/set-password`, { password: pw1 }); setMsg('Đã đặt lại mật khẩu'); setPw1(''); setPw2(''); setPwOpen(false) }
                  catch (ex: any) { setErr(ex?.response?.data?.error?.message || 'Lỗi đặt lại mật khẩu') }
                }}><i className="ti ti-check" />Xác nhận</button>
                <button className="btn ghost" onClick={() => { setPwOpen(false); setPw1(''); setPw2('') }}>Hủy</button>
              </div>
            </div>
          )}
        </div>

        {!isNew && (
         <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {cfg.detailExtra && cfg.detailExtra(form)}
          <div className="card" style={{ padding: 18 }}>
            <h3 style={{ fontSize: 14, color: 'var(--navy)', marginBottom: 12 }}><i className="ti ti-history" /> Lịch sử thao tác</h3>
            {logs.length === 0 && <div style={{ color: '#999', fontSize: 13 }}>Chưa có log.</div>}
            <div className="timeline">
              {logs.map((l, i) => (
                <div key={i} className="tl-item">
                  <span className={'tl-dot ' + l.action} />
                  <div>
                    <div style={{ fontSize: 13 }}><b>{l.by}</b> — {l.action_label}</div>
                    <div style={{ fontSize: 12, color: 'var(--muted)' }}>{fmtDateTime(l.at)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
         </div>
        )}
      </div>
    </div>
  )
}
