import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { fmtDateTime } from '../utils/datetime'
import Pagination from '../components/Pagination'

// ── Hằng số đồng bộ với backend (app/modules/ticket/service.py) ──
export const TICKET_STATUS: Record<string, { label: string; bg: string; color: string }> = {
  open: { label: 'Mới', bg: '#eff6ff', color: '#1d4ed8' },
  in_progress: { label: 'Đang xử lý', bg: '#fff7ed', color: '#c2410c' },
  answered: { label: 'Đã trả lời', bg: '#ecfdf5', color: '#047857' },
  closed: { label: 'Đã đóng', bg: '#f1f5f9', color: '#64748b' },
}
export const TICKET_PRIORITY: Record<string, { label: string; bg: string; color: string }> = {
  low: { label: 'Thấp', bg: '#f1f5f9', color: '#64748b' },
  normal: { label: 'Trung bình', bg: '#eff6ff', color: '#2563eb' },
  high: { label: 'Cao', bg: '#fff7ed', color: '#c2410c' },
  urgent: { label: 'Khẩn', bg: '#fef2f2', color: '#dc2626' },
}
// Bộ phận / nhóm chỉ là nhãn phân loại (định tuyến tập trung về 1 nhóm Hỗ trợ)
export const TICKET_DEPARTMENTS = [
  'Kỹ thuật / Phần mềm',
  'Tài khoản & Đăng nhập',
  'Quy trình mua hàng',
  'Dữ liệu & Báo cáo',
  'Khác',
]

type Ticket = {
  id: number; code: string; subject: string; department: string
  priority: string; priority_label: string
  status: string; status_label: string
  requester_name: string; assignee_name: string
  created_at: string; updated_at: string
}

export function StatusBadge({ status }: { status: string }) {
  const c = TICKET_STATUS[status] || { label: status, bg: '#f1f5f9', color: '#64748b' }
  return (
    <span className="badge" style={{ background: c.bg, color: c.color, fontSize: 12, fontWeight: 700, padding: '3px 10px', borderRadius: 999 }}>
      {c.label}
    </span>
  )
}
export function PriorityBadge({ priority }: { priority: string }) {
  const c = TICKET_PRIORITY[priority] || { label: priority, bg: '#f1f5f9', color: '#64748b' }
  return (
    <span className="badge" style={{ background: c.bg, color: c.color, fontSize: 11.5, fontWeight: 700, padding: '2px 9px', borderRadius: 999 }}>
      {c.label}
    </span>
  )
}

export default function TicketList() {
  const nav = useNavigate()
  const [items, setItems] = useState<Ticket[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [status, setStatus] = useState('')
  const [priority, setPriority] = useState('')
  const [q, setQ] = useState('')
  const timer = useRef<any>(null)

  async function load(p = page, s = pageSize) {
    const params: any = { page: p, page_size: s }
    if (status) params.status = status
    if (priority) params.priority = priority
    const qq = q.trim(); if (qq) params.subject = qq
    const r = await api.get('/api/tickets', { params })
    const d = r.data.data
    setItems(d.items || []); setTotal(d.total || 0)
  }

  useEffect(() => { setPage(1); load(1, pageSize) /* eslint-disable-next-line */ }, [status, priority])
  useEffect(() => {
    clearTimeout(timer.current)
    timer.current = setTimeout(() => { setPage(1); load(1, pageSize) }, 350)
    return () => clearTimeout(timer.current)
    // eslint-disable-next-line
  }, [q])
  useEffect(() => { load(1, pageSize) /* eslint-disable-next-line */ }, [])

  function changePage(p: number, s: number) { setPage(p); setPageSize(s); load(p, s) }

  const lbl = { fontSize: 12, color: 'var(--muted)' } as const
  const STATUS_TABS: { key: string; label: string }[] = [
    { key: '', label: 'Tất cả' },
    { key: 'open', label: 'Mới' },
    { key: 'in_progress', label: 'Đang xử lý' },
    { key: 'answered', label: 'Đã trả lời' },
    { key: 'closed', label: 'Đã đóng' },
  ]

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
        <h2 className="page-title" style={{ margin: 0 }}>Yêu cầu hỗ trợ của tôi</h2>
        <button className="btn" onClick={() => nav('/tickets/new')}><i className="ti ti-plus" /> Mở phiếu hỗ trợ</button>
      </div>

      <div className="card" style={{ padding: 14, marginBottom: 12, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'flex-end' }}>
        <div>
          <label style={lbl}>Trạng thái</label>
          <div style={{ display: 'flex', gap: 6, background: '#f1f5f9', borderRadius: 8, padding: 3, marginTop: 4, flexWrap: 'wrap' }}>
            {STATUS_TABS.map((t) => (
              <button key={t.key} onClick={() => setStatus(t.key)}
                style={{ border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600, padding: '6px 14px', borderRadius: 6,
                  background: status === t.key ? '#fff' : 'transparent', color: status === t.key ? 'var(--navy)' : 'var(--muted)',
                  boxShadow: status === t.key ? '0 1px 2px rgba(15,23,42,.12)' : 'none' }}>
                {t.label}
              </button>
            ))}
          </div>
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
        <table className="table">
          <thead>
            <tr>
              <th style={{ minWidth: 260 }}>Chủ đề</th>
              <th>Bộ phận</th>
              <th>Ưu tiên</th>
              <th>Trạng thái</th>
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
                <td style={{ fontSize: 12.5, color: 'var(--muted)', whiteSpace: 'nowrap' }}>{fmtDateTime(t.updated_at)}</td>
              </tr>
            ))}
            {items.length === 0 && (
              <tr><td colSpan={5} style={{ padding: 30, textAlign: 'center', color: '#94a3b8', fontSize: 13.5 }}>
                Chưa có phiếu hỗ trợ nào. Bấm <b>Mở phiếu hỗ trợ</b> để tạo mới.
              </td></tr>
            )}
          </tbody>
        </table>
      </div>

      <Pagination page={page} pageSize={pageSize} total={total} onChange={changePage} />
    </div>
  )
}
