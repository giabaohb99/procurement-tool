import { Fragment, useEffect, useState } from 'react'
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
        if ((f as any).default !== undefined) {
          init[f.key] = (f as any).default
        } else if (f.key === 'is_active') {
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

  // Tiêu đề trang lấy TÊN bản ghi thay vì "#id" vô nghĩa; mã + id đẩy xuống dòng phụ.
  const recordName = form.full_name || form.name || form.title || form.code || ''
  const heading = isNew ? `Thêm ${cfg.title}` : recordName || `${cfg.title} #${id}`
  // Chip mô tả dưới tên (mã, chức vụ, trạng thái…) — entity nào khai báo thì mới có,
  // còn lại hiện dòng phụ "Loại · Mã · #id" như mặc định.
  const chips: { icon?: string; text: string; cls?: string }[] =
    (!isNew && cfg.detailChips ? cfg.detailChips(form) : []) || []
  const twoCols = !!cfg.detailTwoCols && !isNew

  let lastGroup = ''   // theo dõi nhóm field đang render để chèn tiêu đề nhóm

  return (
    <div>
      {/* Thanh thao tác trên cùng: quay lại bên trái, Lưu/Xóa bên phải — tách khỏi thẻ danh tính
          để luôn ở vị trí quen thuộc và form dài không phải cuộn xuống cuối mới Lưu được. */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => navigate(`/${cfg.slug}`)} title={`Về danh sách ${cfg.title}`}>
          <i className="ti ti-arrow-left" />
        </button>
        <div style={{ marginLeft: 'auto', display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {canSave && <button className="btn" onClick={save}>{isNew ? 'Tạo' : 'Lưu'}</button>}
          {!isNew && can(cfg.entity, 'delete') && (
            <button className="btn ghost" style={{ color: 'var(--red)', borderColor: 'var(--red)' }} onClick={remove}>
              <i className="ti ti-trash" />Xóa
            </button>
          )}
        </div>
      </div>

      {/* Thẻ danh tính (cùng kiểu Trang cá nhân): ảnh + tên + chip mô tả */}
      <div className="card hero-card" style={{ marginBottom: 16 }}>
        <div className="hero-body">
          {!isNew && cfg.detailHeader && cfg.detailHeader(form)}
          <div style={{ minWidth: 0 }}>
            <div className="hero-name">{heading}</div>
            {!isNew && (
              chips.length > 0 ? (
                <div className="hero-chips">
                  {chips.map((c: any, i: number) => (
                    <span key={i} className={'hero-chip ' + (c.cls || '')}>
                      {c.icon && <i className={'ti ' + c.icon} />}{c.text}
                    </span>
                  ))}
                </div>
              ) : (
                <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 6 }}>
                  {cfg.title}
                  {form.code && recordName !== form.code ? ` · ${form.code}` : ''} · #{id}
                </div>
              )
            )}
          </div>
        </div>
      </div>

      {/* twoCols: form bên trái, các thẻ phụ (tài khoản, lịch sử…) bên phải — kiểu Trang cá nhân.
          Mặc định vẫn 1 cột để các màn danh mục cũ (ảnh sản phẩm, thành viên phòng ban) không bị bóp hẹp. */}
      <div className={twoCols ? 'detail-2cols' : 'detail-grid'}>
        <div className="card" style={{ padding: 18 }}>
          <div className="form-grid">
            {cfg.fields.map((f) => {
              const ro = (!isNew && f.readonlyOnEdit) || !canSave   // không có quyền lưu → khóa field
              const newGroup = f.group && f.group !== lastGroup ? f.group : ''
              if (f.group) lastGroup = f.group
              return (
                <Fragment key={f.key}>
                {/* Tiêu đề nhóm chiếm trọn 1 dòng của lưới, field vẫn xếp 2 cột như cũ */}
                {newGroup && <div className="form-group-title">{newGroup}</div>}
                <div className="form-row">
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
                  {f.hint && <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4, fontWeight: 'normal' }}>{f.hint}</div>}
                </div>
                </Fragment>
              )
            })}
          </div>
          {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}
          {msg && (
            <div style={{ marginTop: 12, fontSize: 13, fontWeight: 600, color: 'var(--green)', display: 'flex', alignItems: 'center', gap: 6 }}>
              <i className="ti ti-circle-check" />{msg}
            </div>
          )}
        </div>

        {!isNew && (
         <div className="detail-col">
          {cfg.detailExtra && cfg.detailExtra(form)}
          <div className="card" style={{ padding: 18 }}>
            <h3 className="sec-title" style={{ marginTop: 0 }}>
              <i className="ti ti-history" style={{ marginRight: 8, color: '#b6c2d9' }} />Lịch sử thao tác
            </h3>
            {logs.length === 0 && (
              <div style={{ color: 'var(--muted)', fontSize: 13 }}>
                Chưa có thao tác nào được ghi nhận. Mọi lần sửa/xóa sẽ hiện ở đây kèm người thực hiện và thời điểm.
              </div>
            )}
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
