import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { cruds } from '../config/cruds'

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
  const [dynOpts, setDynOpts] = useState<Record<string, { value: string; label: string }[]>>({})

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
    setErr(''); setMsg('')
    if (isNew) {
      const init: any = {}
      cfg.fields.forEach((f) => { init[f.key] = f.type === 'checkbox' ? true : f.type === 'number' ? 0 : '' })
      setForm(init); setLogs([])
    } else {
      api.get(`${cfg.apiPath}/${id}`).then((r) => setForm(r.data.data))
      loadLogs()
    }
  }, [cfg?.slug, id])

  if (!cfg) return <div>Không tìm thấy trang.</div>
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
    if (!confirm('Xóa bản ghi này?')) return
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
              const ro = !isNew && f.readonlyOnEdit
              return (
                <div key={f.key} className="form-row">
                  <label>{f.label}</label>
                  {f.type === 'textarea' ? (
                    <textarea value={form[f.key] ?? ''} disabled={ro} onChange={(e) => set(f.key, e.target.value)} />
                  ) : (f.type === 'select' || (f.source && f.type !== 'select-multiple')) ? (
                    <select value={form[f.key] ?? ''} disabled={ro} onChange={(e) => {
                      set(f.key, e.target.value);
                      if (f.onValueChange) f.onValueChange(e.target.value, form, (k: string, v: any) => setForm((s:any) => ({...s, [k]: v})));
                    }}>
                      <option value="">-- Chọn --</option>
                      {(f.options || dynOpts[f.key] || []).map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
                    </select>
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
                    <input type={f.type === 'number' ? 'number' : f.type === 'date' ? 'date' : 'text'} value={form[f.key] ?? ''} disabled={ro}
                           onChange={(e) => set(f.key, f.type === 'number' ? Number(e.target.value) : e.target.value)} />
                  )}
                </div>
              )
            })}
          </div>
          {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}
          {msg && <div style={{ color: 'var(--green)', marginTop: 12, fontSize: 13 }}>{msg}</div>}
          <div style={{ display: 'flex', gap: 8, marginTop: 16 }}>
            {canSave && <button className="btn" onClick={save}>{isNew ? 'Tạo' : 'Lưu'}</button>}
            
            {!isNew && cfg.slug === 'employees' && can(cfg.entity, 'write') && (
              <button className="btn outline" style={{ color: 'var(--teal)', borderColor: 'var(--teal)', background: '#fff' }} 
                      onClick={async () => {
                        if (!confirm('Cấp lại mật khẩu và gửi email cho nhân sự này?')) return
                        setErr(''); setMsg('Đang xử lý...')
                        try {
                          await api.post(`/api/employees/${id}/reset-password`)
                          setMsg('Đã cấp lại mật khẩu và gửi email thành công!')
                        } catch (ex: any) {
                          setErr(ex?.response?.data?.error?.message || 'Lỗi khi reset password')
                          setMsg('')
                        }
                      }}>
                <i className="ti ti-key" />Cấp lại mật khẩu
              </button>
            )}
            
            {!isNew && can(cfg.entity, 'delete') && (
              <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={remove}>
                <i className="ti ti-trash" />Xóa
              </button>
            )}
          </div>
        </div>

        {!isNew && (
          <div className="card" style={{ padding: 18 }}>
            <h3 style={{ fontSize: 14, color: 'var(--navy)', marginBottom: 12 }}><i className="ti ti-history" /> Lịch sử thao tác</h3>
            {logs.length === 0 && <div style={{ color: '#999', fontSize: 13 }}>Chưa có log.</div>}
            <div className="timeline">
              {logs.map((l, i) => (
                <div key={i} className="tl-item">
                  <span className={'tl-dot ' + l.action} />
                  <div>
                    <div style={{ fontSize: 13 }}><b>{l.by}</b> — {l.action_label}</div>
                    <div style={{ fontSize: 12, color: 'var(--muted)' }}>{new Date(l.at).toLocaleString('vi-VN')}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
