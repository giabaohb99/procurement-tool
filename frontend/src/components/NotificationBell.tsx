import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { fmtDateTime } from '../utils/datetime'

type Notif = { id: number; title: string; body: string; link: string; is_read: boolean; at: string }
type Alert = { type: string; level: string; title: string; link: string }

const LV_COLOR: Record<string, string> = { danger: '#b91c1c', warn: '#d97706' }
// Dùng chung fmtDateTime (chuỗi UTC naive → +7 giờ VN), đồng bộ với Lịch sử thao tác
const fmtTime = (s: string) => fmtDateTime(s)

// Tiếng "tin-tin" khi có thông báo mới (Web Audio, không cần file)
function playDing() {
  try {
    const AC = (window as any).AudioContext || (window as any).webkitAudioContext
    if (!AC) return
    const ctx = new AC()
    const beep = (t: number, freq: number) => {
      const o = ctx.createOscillator(); const g = ctx.createGain()
      o.type = 'sine'; o.frequency.value = freq
      o.connect(g); g.connect(ctx.destination)
      g.gain.setValueAtTime(0.0001, ctx.currentTime + t)
      g.gain.exponentialRampToValueAtTime(0.22, ctx.currentTime + t + 0.02)
      g.gain.exponentialRampToValueAtTime(0.0001, ctx.currentTime + t + 0.18)
      o.start(ctx.currentTime + t); o.stop(ctx.currentTime + t + 0.2)
    }
    beep(0, 880); beep(0.19, 1175)
    setTimeout(() => { try { ctx.close() } catch { /* noop */ } }, 700)
  } catch { /* noop */ }
}

export default function NotificationBell() {
  const nav = useNavigate()
  const [open, setOpen] = useState(false)
  const [notifs, setNotifs] = useState<Notif[]>([])
  const [unread, setUnread] = useState(0)
  const [alerts, setAlerts] = useState<Alert[]>([])
  const [danger, setDanger] = useState(0)
  const ref = useRef<HTMLDivElement>(null)
  const prevBadge = useRef<number | null>(null)   // để phát tiếng khi badge tăng

  async function load() {
    try {
      const [n, a] = await Promise.all([
        api.get('/api/notifications'),
        api.get('/api/alerts').catch(() => ({ data: { data: { items: [], danger: 0 } } })),
      ])
      const newUnread = n.data.data.unread || 0
      const newDanger = a.data.data.danger || 0
      const newBadge = newUnread + newDanger
      // Chỉ kêu khi có thông báo MỚI (badge tăng), bỏ qua lần load đầu
      if (prevBadge.current !== null && newBadge > prevBadge.current) playDing()
      prevBadge.current = newBadge
      setNotifs(n.data.data.items || []); setUnread(newUnread)
      setAlerts(a.data.data.items || []); setDanger(newDanger)
    } catch { /* im lặng */ }
  }

  useEffect(() => {
    load()
    const t = setInterval(load, 20000)
    const onClick = (e: MouseEvent) => { if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false) }
    document.addEventListener('mousedown', onClick)
    return () => { clearInterval(t); document.removeEventListener('mousedown', onClick) }
  }, [])

  const badge = unread + danger

  async function openNotif(n: Notif) {
    setOpen(false)
    if (!n.is_read) { try { await api.post(`/api/notifications/${n.id}/read`) } catch { /* noop */ }; setUnread((u) => Math.max(0, u - 1)); setNotifs((s) => s.map((x) => x.id === n.id ? { ...x, is_read: true } : x)) }
    if (n.link) nav(n.link)
  }
  async function readAll() {
    try { await api.post('/api/notifications/read-all') } catch { /* noop */ }
    setUnread(0); setNotifs((s) => s.map((x) => ({ ...x, is_read: true })))
  }

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button className="icon-btn" onClick={() => { setOpen((o) => !o); if (!open) load() }} aria-label="Thông báo" style={{ position: 'relative' }}>
        <i className="ti ti-bell" />
        {badge > 0 && (
          <span style={{ position: 'absolute', top: -2, right: -2, minWidth: 16, height: 16, padding: '0 4px', borderRadius: 8, background: '#ef4444', color: '#fff', fontSize: 10, fontWeight: 700, display: 'flex', alignItems: 'center', justifyContent: 'center', lineHeight: 1 }}>
            {badge > 99 ? '99+' : badge}
          </span>
        )}
      </button>

      {open && (
        <div style={{ position: 'absolute', right: 0, top: 'calc(100% + 8px)', width: 360, maxWidth: '92vw', background: '#fff', border: '1px solid var(--border)', borderRadius: 12, boxShadow: '0 12px 30px rgba(15,23,42,.15)', zIndex: 300, overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 14px', borderBottom: '1px solid var(--border)' }}>
            <b style={{ color: 'var(--navy)', fontSize: 14 }}>Thông báo</b>
            {unread > 0 && <button className="clickable" style={{ background: 'none', border: 'none', color: 'var(--teal)', fontSize: 12.5, cursor: 'pointer' }} onClick={readAll}>Đánh dấu đã đọc tất cả</button>}
          </div>

          <div style={{ maxHeight: '60vh', overflowY: 'auto' }}>
            {/* Thông báo cá nhân */}
            {notifs.length === 0 && alerts.length === 0 && (
              <div style={{ padding: 24, textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>Không có thông báo nào.</div>
            )}
            {notifs.map((n) => (
              <div key={n.id} onClick={() => openNotif(n)} className="clickable"
                style={{ display: 'flex', gap: 10, padding: '10px 14px', borderBottom: '1px solid #f1f5f9', cursor: 'pointer', background: n.is_read ? '#fff' : '#eff6ff' }}>
                <i className="ti ti-bell" style={{ color: n.is_read ? '#94a3b8' : 'var(--teal)', marginTop: 2 }} />
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: 13, fontWeight: n.is_read ? 500 : 700, color: 'var(--navy)' }}>{n.title}</div>
                  <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 2 }}>{n.body}</div>
                  <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 2 }}>{fmtTime(n.at)}</div>
                </div>
              </div>
            ))}

            {/* Cảnh báo hệ thống (chuông) */}
            {alerts.length > 0 && (
              <div style={{ padding: '8px 14px', fontSize: 11.5, fontWeight: 700, color: 'var(--muted)', textTransform: 'uppercase', background: '#f8fafc' }}>Cảnh báo</div>
            )}
            {alerts.map((a, i) => (
              <div key={i} onClick={() => { setOpen(false); if (a.link) nav(a.link) }} className="clickable"
                style={{ display: 'flex', gap: 10, padding: '9px 14px', borderBottom: '1px solid #f1f5f9', cursor: 'pointer' }}>
                <i className="ti ti-alert-triangle" style={{ color: LV_COLOR[a.level] || '#64748b', marginTop: 2 }} />
                <div style={{ fontSize: 12.5, color: 'var(--ink)' }}>{a.title}</div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
