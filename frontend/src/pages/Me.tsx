import { useEffect, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { TICKET_ENABLED } from '../config/features'
import ProfileHero, { MeProfile } from './me/profile-hero'
import InfoTab from './me/info-tab'
import TasksTab, { sumTaskCounts } from './me/tasks-tab'
import MyTicketsTab from './me/my-tickets-tab'

type MeTab = 'info' | 'tasks' | 'tickets'

/**
 * Trang cá nhân: thẻ danh tính + dải tab dính liền, bên dưới là nội dung của tab.
 * Tab đang chọn lưu ở query `?tab=` để chia sẻ/F5 vẫn giữ đúng chỗ.
 */
export default function Me() {
  const [sp, setSp] = useSearchParams()
  const { can } = useAuth()
  // Chỉ hiện tab hỗ trợ khi tài khoản thực sự đọc được phiếu — trước đây tab luôn hiện
  // nên người không có quyền bấm vào chỉ nhận lỗi 403 và một bảng rỗng.
  const showTickets = TICKET_ENABLED && can('ticket', 'read')
  const TABS: { key: MeTab; label: string; icon: string }[] = [
    { key: 'info', label: 'Thông tin cá nhân', icon: 'ti-user-circle' },
    { key: 'tasks', label: 'Việc cần làm', icon: 'ti-checklist' },
    ...(showTickets
      ? [{ key: 'tickets' as MeTab, label: 'Yêu cầu hỗ trợ của tôi', icon: 'ti-headset' }]
      : []),
  ]
  const raw = sp.get('tab') || ''
  const tab: MeTab = TABS.some((t) => t.key === raw) ? (raw as MeTab) : 'info'
  const setTab = (t: MeTab) => setSp(t === 'info' ? {} : { tab: t })

  const [me, setMe] = useState<MeProfile | null>(null)
  useEffect(() => { api.get('/api/auth/me').then((r) => setMe(r.data.data)).catch(() => {}) }, [])

  // Số trên tab: nạp sẵn để thấy ngay còn việc/phiếu mà không phải bấm vào từng tab.
  // Bỏ qua tab đang mở — chính tab đó đã tải dữ liệu và tự báo số về qua onCount.
  const [counts, setCounts] = useState<{ tasks?: number; tickets?: number }>({})
  useEffect(() => {
    if (tab !== 'tasks') {
      api.get('/api/dashboard/tasks', { params: { page: 1, page_size: 1 }, _silent: true } as any)
        .then((r) => setCounts((c) => ({ ...c, tasks: sumTaskCounts(r.data.data?.by_type) })))
        .catch(() => {})
    }
    if (showTickets && tab !== 'tickets') {
      api.get('/api/tickets', { params: { page: 1, page_size: 1, mine: 1 }, _silent: true } as any)
        .then((r) => setCounts((c) => ({ ...c, tickets: r.data.data?.total || 0 })))
        .catch(() => {})
    }
    // Chỉ nạp 1 lần lúc mở trang; đổi tab thì chính tab đó cập nhật số của nó
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  const countOf = (k: MeTab) => (k === 'tasks' ? counts.tasks : k === 'tickets' ? counts.tickets : undefined)

  return (
    <div>
      <h2 className="page-title">Trang cá nhân</h2>

      <ProfileHero me={me}>
        <div className="me-tabs">
          {TABS.map((t) => {
            const n = countOf(t.key)
            return (
              <button
                key={t.key}
                onClick={() => setTab(t.key)}
                className={'me-tab' + (tab === t.key ? ' active' : '')}
              >
                <i className={'ti ' + t.icon} />
                {t.label}
                {n != null && n > 0 && (
                  <span className={'me-tab-count' + (t.key === 'tasks' ? ' alert' : '')}>{n}</span>
                )}
              </button>
            )
          })}
        </div>
      </ProfileHero>

      {tab === 'info' && <InfoTab me={me} />}
      {tab === 'tasks' && <TasksTab onCount={(n) => setCounts((c) => ({ ...c, tasks: n }))} />}
      {tab === 'tickets' && <MyTicketsTab onCount={(n) => setCounts((c) => ({ ...c, tickets: n }))} />}
    </div>
  )
}
