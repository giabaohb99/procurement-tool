import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { useUrlFilters } from '../hooks/use-url-filters'
import { fmtDateTime } from '../utils/datetime'
import { toast } from '../components/toast'
import Pagination from '../components/Pagination'
import {
  PriorityBadge, StatusBadge, TICKET_PRIORITY, TICKET_STATUS_TABS, Ticket,
} from '../config/ticketMeta'

// Màn QUẢN LÝ phiếu hỗ trợ — chỉ nhóm Hỗ trợ vào (menu "Hỗ trợ" ở sidebar).
// Người dùng thường xem phiếu của mình ở Trang cá nhân > tab "Yêu cầu hỗ trợ của tôi".

const ASSIGNEE_TABS: { key: string; label: string }[] = [
  { key: '', label: 'Tất cả' },
  { key: 'unassigned', label: 'Chưa ai nhận' },
  { key: 'me', label: 'Tôi đang xử lý' },
]

export default function TicketList() {
  const nav = useNavigate()
  const { user } = useAuth()
  const [items, setItems] = useState<Ticket[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  // Bộ lọc lưu trên URL (?status=&priority=&assignee=&q=) → F5 không mất bộ lọc
  const [f, setF] = useUrlFilters({ status: '', priority: '', assignee: '', q: '' })
  const { status, priority, assignee, q } = f
  const setStatus = (v: string) => setF((s) => ({ ...s, status: v }))
  const setPriority = (v: string) => setF((s) => ({ ...s, priority: v }))
  const setAssignee = (v: string) => setF((s) => ({ ...s, assignee: v }))
  const setQ = (v: string) => setF((s) => ({ ...s, q: v }))
  const [busyId, setBusyId] = useState(0)
  const timer = useRef<any>(null)

  async function load(p = page, s = pageSize) {
    const params: any = { page: p, page_size: s }
    if (status) params.status = status
    if (priority) params.priority = priority
    if (assignee) params.assignee = assignee
    const qq = q.trim(); if (qq) params.subject = qq
    const r = await api.get('/api/tickets', { params })
    const d = r.data.data
    setItems(d.items || []); setTotal(d.total || 0)
  }

  useEffect(() => { setPage(1); load(1, pageSize) /* eslint-disable-next-line */ }, [status, priority, assignee])
  useEffect(() => {
    clearTimeout(timer.current)
    timer.current = setTimeout(() => { setPage(1); load(1, pageSize) }, 350)
    return () => clearTimeout(timer.current)
    // eslint-disable-next-line
  }, [q])
  useEffect(() => { load(1, pageSize) /* eslint-disable-next-line */ }, [])

  function changePage(p: number, s: number) { setPage(p); setPageSize(s); load(p, s) }

  async function take(t: Ticket) {
    setBusyId(t.id)
    try {
      await api.post(`/api/tickets/${t.id}/assign`, { assignee_id: user?.id || 0 })
      toast.success(`Bạn đã nhận phiếu ${t.code}`)
      load()
    } catch {
      // interceptor toast
    } finally {
      setBusyId(0)
    }
  }

  const lbl = { fontSize: 12, color: 'var(--muted)' } as const
  const pills = (opts: { key: string; label: string }[], val: string, set: (v: string) => void) => (
    <div style={{ display: 'flex', gap: 6, background: '#f1f5f9', borderRadius: 8, padding: 3, marginTop: 4, flexWrap: 'wrap' }}>
      {opts.map((t) => (
        <button key={t.key} onClick={() => set(t.key)}
          style={{ border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600, padding: '6px 14px', borderRadius: 6,
            fontFamily: 'inherit',
            background: val === t.key ? '#fff' : 'transparent', color: val === t.key ? 'var(--navy)' : 'var(--muted)',
            boxShadow: val === t.key ? '0 1px 2px rgba(15,23,42,.12)' : 'none' }}>
          {t.label}
        </button>
      ))}
    </div>
  )

  return (
    <div>
      <div style={{ marginBottom: 14 }}>
        <h2 className="page-title" style={{ margin: 0 }}>Quản lý phiếu hỗ trợ</h2>
        <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 4 }}>
          Toàn bộ phiếu người dùng gửi lên. Bấm <b>Nhận</b> để tự gán mình làm người xử lý.
        </div>
      </div>

      <div className="card" style={{ padding: 14, marginBottom: 12, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div>
          <label style={lbl}>Trạng thái</label>
          {pills(TICKET_STATUS_TABS, status, setStatus)}
        </div>
        <div>
          <label style={lbl}>Người xử lý</label>
          {pills(ASSIGNEE_TABS, assignee, setAssignee)}
        </div>
        <div>
          <label style={lbl}>Ưu tiên</label>
          <select value={priority} onChange={(e) => setPriority(e.target.value)} style={{ marginTop: 4 }}>
            <option value="">Tất cả</option>
            {Object.entries(TICKET_PRIORITY).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
          </select>
        </div>
        <div style={{ flex: '1 1 240px', maxWidth: 340 }}>
          <label style={lbl}>Tìm kiếm</label>
          <input value={q} placeholder="Tìm theo chủ đề…" onChange={(e) => setQ(e.target.value)} />
        </div>
      </div>

      <div className="card" style={{ overflowX: 'auto' }}>
        <table className="table" style={{ minWidth: 980 }}>
          <thead>
            <tr>
              <th style={{ minWidth: 260 }}>Chủ đề</th>
              <th>Người gửi</th>
              <th>Bộ phận</th>
              <th>Ưu tiên</th>
              <th>Trạng thái</th>
              <th>Người xử lý</th>
              <th>Cập nhật</th>
              <th style={{ width: 90 }}></th>
            </tr>
          </thead>
          <tbody>
            {items.map((t) => (
              <tr key={t.id} className="clickable" style={{ cursor: 'pointer' }} onClick={() => nav(`/tickets/${t.id}`)}>
                <td>
                  <div style={{ fontWeight: 600, color: 'var(--navy)' }}>{t.subject || '(Không có chủ đề)'}</div>
                  <div style={{ fontSize: 11.5, color: '#94a3b8', marginTop: 2 }}>{t.code}</div>
                </td>
                <td style={{ fontSize: 13, color: 'var(--navy)' }}>{t.requester_name || '—'}</td>
                <td style={{ fontSize: 13, color: 'var(--muted)' }}>{t.department || '—'}</td>
                <td><PriorityBadge priority={t.priority} /></td>
                <td><StatusBadge status={t.status} /></td>
                <td style={{ fontSize: 13 }}>
                  {t.assignee_name
                    ? <span style={{ color: 'var(--navy)', fontWeight: 600 }}>{t.assignee_name}</span>
                    : <span style={{ color: '#f59e0b', fontWeight: 600 }}>Chưa ai nhận</span>}
                </td>
                <td style={{ fontSize: 12.5, color: 'var(--muted)', whiteSpace: 'nowrap' }}>{fmtDateTime(t.updated_at)}</td>
                <td onClick={(e) => e.stopPropagation()}>
                  {!t.assignee_id && t.status !== 'closed' && (
                    <button className="btn secondary" style={{ padding: '4px 10px', fontSize: 12.5 }}
                      disabled={busyId === t.id} onClick={() => take(t)}>
                      {busyId === t.id ? <i className="ti ti-loader spin" /> : <><i className="ti ti-hand-click" /> Nhận</>}
                    </button>
                  )}
                </td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td colSpan={8} style={{ padding: 30, textAlign: 'center', color: '#94a3b8', fontSize: 13.5 }}>
                Không có phiếu hỗ trợ nào khớp bộ lọc.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>

      <Pagination page={page} pageSize={pageSize} total={total} onChange={changePage} />
    </div>
  )
}
