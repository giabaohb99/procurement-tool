import { useEffect, useRef, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { toast } from '../components/toast'
import Pagination from '../components/Pagination'
import SearchSelect from '../components/SearchSelect'
import { useAuth } from '../auth/AuthContext'
import { pushSupported, isPushSubscribed, subscribePush, unsubscribePush } from '../push'
import { TICKET_ENABLED } from '../config/features'
import TicketCreateModal from '../components/TicketCreateModal'
import { PriorityBadge, StatusBadge, Ticket, TICKET_STATUS_TABS } from '../config/ticketMeta'
import { fmtDateTime } from '../utils/datetime'

// Nhãn + màu + icon cho từng loại việc cần làm (cố định, không phụ thuộc dữ liệu đang lọc)
const TASK_LABEL: Record<string, string> = {
  pr: 'YCMH chờ duyệt', sr: 'Khảo sát chờ duyệt', po: 'ĐMH chờ duyệt',
  late: 'Giao hàng trễ', payable: 'Công nợ quá hạn',
}
const TASK_META: Record<string, { color: string; icon: string }> = {
  pr: { color: '#2563eb', icon: 'ti-file-invoice' },
  sr: { color: '#0891b2', icon: 'ti-clipboard-search' },
  po: { color: '#7c3aed', icon: 'ti-shopping-cart' },
  late: { color: '#d97706', icon: 'ti-truck-delivery' },
  payable: { color: '#dc2626', icon: 'ti-cash' },
}

type MeTab = 'info' | 'tasks' | 'tickets'

export default function Me() {
  const nav = useNavigate()
  const [sp, setSp] = useSearchParams()
  const TABS: { key: MeTab; label: string }[] = [
    { key: 'info', label: 'Thông tin cá nhân' },
    { key: 'tasks', label: 'Việc cần làm' },
    ...(TICKET_ENABLED ? [{ key: 'tickets' as MeTab, label: 'Yêu cầu hỗ trợ của tôi' }] : []),
  ]
  const raw = sp.get('tab') || ''
  const tab: MeTab = TABS.some((t) => t.key === raw) ? (raw as MeTab) : 'info'
  const setTab = (t: MeTab) => setSp(t === 'info' ? {} : { tab: t })

  const [me, setMe] = useState<any>(null)
  useEffect(() => { api.get('/api/auth/me').then((r) => setMe(r.data.data)).catch(() => {}) }, [])

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <h2 className="page-title" style={{ margin: 0 }}>Trang cá nhân</h2>
        <span style={{ flex: 1 }} />
        <button className="btn ghost" onClick={() => nav('/notifications')}><i className="ti ti-bell" />Thông báo</button>
      </div>

      <div style={{ display: 'flex', gap: 6, background: '#f1f5f9', borderRadius: 10, padding: 4, marginBottom: 16, width: 'fit-content' }}>
        {TABS.map((t) => (
          <button key={t.key} onClick={() => setTab(t.key)}
            style={{ border: 'none', cursor: 'pointer', fontFamily: 'inherit', fontSize: 13.5, fontWeight: 700, padding: '8px 18px', borderRadius: 8,
              background: tab === t.key ? '#fff' : 'transparent', color: tab === t.key ? 'var(--navy)' : 'var(--muted)',
              boxShadow: tab === t.key ? '0 1px 3px rgba(15,23,42,.14)' : 'none' }}>
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'info' && <InfoTab me={me} />}
      {tab === 'tasks' && <TasksTab />}
      {tab === 'tickets' && <MyTicketsTab />}
    </div>
  )
}

function InfoTab({ me }: { me: any }) {
  if (!me) return <div style={{ padding: 30, color: 'var(--muted)' }}>Đang tải…</div>
  const rows: [string, any][] = [
    ['Họ và tên', me.full_name], ['Mã nhân viên', me.emp_code || '—'], ['Email', me.email],
    ['Số điện thoại', me.phone || '—'], ['Phòng ban', me.department_name || '—'],
    ['Chức vụ', me.position || me.role_name || '—'],
  ]

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16, alignItems: 'start' }}>
      <div className="card" style={{ padding: 20 }}>
        <h3 className="sec-title">Thông tin tài khoản</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginTop: 6 }}>
          {rows.map(([k, v]) => (
            <div key={k} style={{ display: 'flex', gap: 10 }}>
              <div style={{ width: 130, color: 'var(--muted)', fontSize: 13 }}>{k}</div>
              <div style={{ fontWeight: 600, color: 'var(--navy)', fontSize: 13.5 }}>{v}</div>
            </div>
          ))}
        </div>
      </div>

      <div className="card" style={{ padding: 20 }}>
        <ChangePassword />
      </div>

      <PushToggle />
    </div>
  )
}

function PushToggle() {
  const [supported, setSupported] = useState(true)
  const [subscribed, setSubscribed] = useState(false)
  const [busy, setBusy] = useState(false)
  useEffect(() => {
    if (!pushSupported()) { setSupported(false); return }
    isPushSubscribed().then(setSubscribed).catch(() => {})
  }, [])
  async function toggle() {
    setBusy(true)
    try {
      if (subscribed) { await unsubscribePush(); setSubscribed(false); toast.success('Đã tắt thông báo trên thiết bị này') }
      else { await subscribePush(); setSubscribed(true); toast.success('Đã bật thông báo trên thiết bị này') }
    } catch (e: any) { toast.error(e?.message || 'Không bật được thông báo') }
    finally { setBusy(false) }
  }
  return (
    <div className="card" style={{ padding: 20 }}>
      <h3 className="sec-title" style={{ marginTop: 0 }}>Thông báo đẩy (điện thoại / máy tính)</h3>
      <div style={{ fontSize: 13, color: 'var(--muted)', marginBottom: 12 }}>
        Bật để nhận thông báo (gửi duyệt, được phân công phụ trách…) đẩy về máy/điện thoại kể cả khi không mở app.
        {' '}<b>Trên iPhone</b> cần "Thêm vào màn hình chính" trước khi bật.
      </div>
      {!supported ? (
        <div style={{ fontSize: 13, color: 'var(--muted)' }}>Trình duyệt này không hỗ trợ thông báo đẩy.</div>
      ) : (
        <button className={subscribed ? 'btn ghost' : 'btn'} disabled={busy} onClick={toggle}>
          <i className={subscribed ? 'ti ti-bell-off' : 'ti ti-bell'} />
          {busy ? 'Đang xử lý…' : (subscribed ? 'Tắt thông báo trên thiết bị này' : 'Bật thông báo trên thiết bị này')}
        </button>
      )}
    </div>
  )
}

function ChangePassword() {
  const { logout } = useAuth()
  const nav = useNavigate()
  const [oldP, setOldP] = useState(''); const [newP, setNewP] = useState(''); const [conf, setConf] = useState('')
  const [busy, setBusy] = useState(false)
  async function submit() {
    if (newP.length < 6) { toast.error('Mật khẩu mới phải từ 6 ký tự'); return }
    if (newP !== conf) { toast.error('Xác nhận mật khẩu không khớp'); return }
    setBusy(true)
    try {
      await api.post('/api/auth/change-password', { old_password: oldP, new_password: newP })
      setOldP(''); setNewP(''); setConf('')
      toast.success('Đã đổi mật khẩu — vui lòng đăng nhập lại')
      // Đổi mật khẩu xong → đăng xuất để đăng nhập lại bằng mật khẩu mới
      setTimeout(() => { logout(); nav('/login') }, 1000)
    } catch (e: any) { toast.error(e?.response?.data?.error?.message || 'Lỗi đổi mật khẩu'); setBusy(false) }
  }
  const inp = { marginTop: 4 } as const
  return (
    <div>
      <h3 className="sec-title" style={{ marginTop: 0 }}>Đổi mật khẩu</h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxWidth: 340 }}>
        <div><label style={{ fontSize: 12, color: 'var(--muted)' }}>Mật khẩu hiện tại</label>
          <input style={inp} type="password" value={oldP} onChange={(e) => setOldP(e.target.value)} /></div>
        <div><label style={{ fontSize: 12, color: 'var(--muted)' }}>Mật khẩu mới</label>
          <input style={inp} type="password" value={newP} onChange={(e) => setNewP(e.target.value)} /></div>
        <div><label style={{ fontSize: 12, color: 'var(--muted)' }}>Xác nhận mật khẩu mới</label>
          <input style={inp} type="password" value={conf} onChange={(e) => setConf(e.target.value)} /></div>
        <button className="btn" disabled={busy || !oldP || !newP} onClick={submit} style={{ marginTop: 4, alignSelf: 'flex-start' }}>
          <i className="ti ti-lock" />Đổi mật khẩu
        </button>
      </div>
    </div>
  )
}

// Tab "Yêu cầu hỗ trợ của tôi" — CHỈ phiếu do chính mình gửi (mine=1),
// kể cả người thuộc nhóm Hỗ trợ (họ xem phiếu cả công ty ở màn quản lý /tickets).
function MyTicketsTab() {
  const nav = useNavigate()
  const [items, setItems] = useState<Ticket[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [status, setStatus] = useState('')
  const [openForm, setOpenForm] = useState(false)

  async function load(p = page, s = pageSize, st = status) {
    const params: any = { page: p, page_size: s, mine: 1 }
    if (st) params.status = st
    const r = await api.get('/api/tickets', { params })
    const d = r.data.data
    setItems(d.items || []); setTotal(d.total || 0)
  }
  useEffect(() => { setPage(1); load(1, pageSize, status) /* eslint-disable-next-line */ }, [status])
  function changePage(p: number, s: number) { setPage(p); setPageSize(s); load(p, s, status) }

  return (
    <div>
      <div className="card" style={{ padding: 14, marginBottom: 12, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{ display: 'flex', gap: 6, background: '#f1f5f9', borderRadius: 8, padding: 3, flexWrap: 'wrap' }}>
          {TICKET_STATUS_TABS.map((t) => (
            <button key={t.key} onClick={() => setStatus(t.key)}
              style={{ border: 'none', cursor: 'pointer', fontFamily: 'inherit', fontSize: 13, fontWeight: 600, padding: '6px 14px', borderRadius: 6,
                background: status === t.key ? '#fff' : 'transparent', color: status === t.key ? 'var(--navy)' : 'var(--muted)',
                boxShadow: status === t.key ? '0 1px 2px rgba(15,23,42,.12)' : 'none' }}>
              {t.label}
            </button>
          ))}
        </div>
        <button className="btn" onClick={() => setOpenForm(true)}><i className="ti ti-plus" /> Gửi yêu cầu hỗ trợ</button>
      </div>

      <div className="card" style={{ overflowX: 'auto' }}>
        <table className="table">
          <thead>
            <tr>
              <th style={{ minWidth: 240 }}>Chủ đề</th>
              <th>Bộ phận</th>
              <th>Ưu tiên</th>
              <th>Trạng thái</th>
              <th>Người xử lý</th>
              <th>Cập nhật</th>
            </tr>
          </thead>
          <tbody>
            {items.map((t) => (
              <tr key={t.id} className="clickable" style={{ cursor: 'pointer' }} onClick={() => nav(`/tickets/${t.id}`)}>
                <td>
                  <div style={{ fontWeight: 600, color: 'var(--navy)' }}>{t.subject || '(Không có chủ đề)'}</div>
                  <div style={{ fontSize: 11.5, color: '#94a3b8', marginTop: 2 }}>{t.code}</div>
                </td>
                <td style={{ fontSize: 13, color: 'var(--muted)' }}>{t.department || '—'}</td>
                <td><PriorityBadge priority={t.priority} /></td>
                <td><StatusBadge status={t.status} /></td>
                <td style={{ fontSize: 13, color: t.assignee_name ? 'var(--navy)' : 'var(--muted)' }}>{t.assignee_name || 'Chưa nhận'}</td>
                <td style={{ fontSize: 12.5, color: 'var(--muted)', whiteSpace: 'nowrap' }}>{fmtDateTime(t.updated_at)}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td colSpan={6} style={{ padding: 30, textAlign: 'center', color: '#94a3b8', fontSize: 13.5 }}>
                Bạn chưa gửi yêu cầu hỗ trợ nào. Bấm <b>Gửi yêu cầu hỗ trợ</b> khi cần trợ giúp.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>

      <Pagination page={page} pageSize={pageSize} total={total} onChange={changePage} />

      <TicketCreateModal open={openForm} onClose={() => setOpenForm(false)} originUrl="/me?tab=tickets" />
    </div>
  )
}

function TasksTab() {
  const nav = useNavigate()
  const [items, setItems] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [byType, setByType] = useState<Record<string, number>>({})
  const [type, setType] = useState('')
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  const [q, setQ] = useState('')
  const timer = useRef<any>(null)

  async function load(p = page, s = pageSize, t = type, qq = q) {
    const params: any = { page: p, page_size: s }
    if (t) params.type = t
    if (qq.trim()) params.q = qq.trim()
    const r = await api.get('/api/dashboard/tasks', { params })
    const d = r.data.data
    setItems(d.items || []); setTotal(d.total || 0); setByType(d.by_type || {})
  }
  // Đổi loại → lọc lại (chủ động chọn, không tự lọc trước)
  useEffect(() => { setPage(1); load(1, pageSize, type, q) /* eslint-disable-next-line */ }, [type])
  // Tìm kiếm: debounce 350ms
  useEffect(() => {
    clearTimeout(timer.current)
    timer.current = setTimeout(() => { setPage(1); load(1, pageSize, type, q) }, 350)
    return () => clearTimeout(timer.current)
    // eslint-disable-next-line
  }, [q])
  useEffect(() => { load(1, pageSize, '', '') /* eslint-disable-next-line */ }, [])
  function changePage(p: number, s: number) { setPage(p); setPageSize(s); load(p, s, type, q) }

  const allCount = Object.values(byType).reduce((a, b) => a + b, 0)
  const typeOpts = [
    { value: '', label: `Tất cả (${allCount})` },
    ...['pr', 'sr', 'po', 'late', 'payable'].map((k) => ({ value: k, label: `${TASK_LABEL[k]}${byType[k] ? ` (${byType[k]})` : ''}` })),
  ]

  return (
    <div>
      <div className="card" style={{ padding: 14, marginBottom: 12, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div style={{ minWidth: 220 }}>
          <label style={{ fontSize: 12, color: 'var(--muted)' }}>Loại việc</label>
          <SearchSelect value={type} placeholder="Tất cả" options={typeOpts} onChange={(v) => setType(v)} />
        </div>
        <div style={{ flex: '1 1 260px', maxWidth: 380 }}>
          <label style={{ fontSize: 12, color: 'var(--muted)' }}>Tìm kiếm</label>
          <input value={q} placeholder="Tìm theo mã / tên / nội dung…" onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>

      <div className="card">
        {items.length === 0 && (
          <div style={{ padding: 30, textAlign: 'center', color: '#94a3b8', fontSize: 13.5 }}>
            🎉 Không có việc nào cần xử lý.
          </div>
        )}
        {items.map((t, i) => {
          const m = TASK_META[t.type] || { color: '#64748b', icon: 'ti-point' }
          return (
            <div key={i} onClick={() => t.link && nav(t.link)} className="clickable"
              style={{ display: 'flex', gap: 12, alignItems: 'center', padding: '12px 16px', borderBottom: '1px solid #f1f5f9', cursor: 'pointer' }}>
              <i className={'ti ' + m.icon} style={{ color: m.color, fontSize: 20 }} />
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--navy)' }}>
                  <span style={{ fontSize: 11, fontWeight: 700, color: m.color, marginRight: 8 }}>{t.label}</span>
                  {t.code} {t.title ? <span style={{ color: 'var(--muted)', fontWeight: 500 }}>· {t.title}</span> : null}
                </div>
                {t.subtitle && <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 2 }}>{t.subtitle}</div>}
              </div>
              <div style={{ fontSize: 12, color: '#94a3b8' }}>{t.date}</div>
              <i className="ti ti-chevron-right" style={{ color: '#cbd5e1' }} />
            </div>
          )
        })}
      </div>

      <Pagination page={page} pageSize={pageSize} total={total} onChange={changePage} />
    </div>
  )
}
