import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import Pagination from '../../components/Pagination'
import TicketCreateModal from '../../components/TicketCreateModal'
import { PriorityBadge, StatusBadge, Ticket, TICKET_STATUS_TABS } from '../../config/ticketMeta'
import { fmtDateTime } from '../../utils/datetime'
import SegmentedFilter from './segmented-filter'

/**
 * Tab "Yêu cầu hỗ trợ của tôi" — CHỈ phiếu do chính mình gửi (mine=1),
 * kể cả người thuộc nhóm Hỗ trợ (họ xem phiếu cả công ty ở màn quản lý /tickets).
 */
export default function MyTicketsTab({ onCount }: { onCount?: (n: number) => void }) {
  const nav = useNavigate()
  const [items, setItems] = useState<Ticket[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [status, setStatus] = useState('')
  const [loading, setLoading] = useState(true)
  const [openForm, setOpenForm] = useState(false)

  async function load(p = page, s = pageSize, st = status) {
    setLoading(true)
    const params: any = { page: p, page_size: s, mine: 1 }
    if (st) params.status = st
    try {
      const r = await api.get('/api/tickets', { params })
      const d = r.data.data
      setItems(d.items || []); setTotal(d.total || 0)
      // Badge trên tab đếm TỔNG phiếu của mình → chỉ cập nhật khi không lọc trạng thái
      if (!st) onCount?.(d.total || 0)
    } finally { setLoading(false) }
  }
  useEffect(() => { setPage(1); load(1, pageSize, status) /* eslint-disable-next-line */ }, [status])
  function changePage(p: number, s: number) { setPage(p); setPageSize(s); load(p, s, status) }

  return (
    <div>
      <div className="card" style={{ padding: 14, marginBottom: 12, display: 'flex', gap: 12, flexWrap: 'wrap', alignItems: 'center', justifyContent: 'space-between' }}>
        <SegmentedFilter
          options={TICKET_STATUS_TABS.map((t) => ({ key: t.key, label: t.label }))}
          value={status}
          onChange={setStatus}
        />
        <button className="btn" onClick={() => setOpenForm(true)}><i className="ti ti-plus" /> Gửi yêu cầu hỗ trợ</button>
      </div>

      <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
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
              <tr>
                <td colSpan={6} style={{ padding: '40px 20px', textAlign: 'center' }}>
                  {loading ? (
                    <span style={{ color: '#94a3b8', fontSize: 13.5 }}>Đang tải…</span>
                  ) : (
                    <>
                      <i className="ti ti-headset" style={{ fontSize: 32, color: '#cbd5e1' }} />
                      <div style={{ marginTop: 10, fontSize: 14.5, fontWeight: 600, color: 'var(--navy)' }}>
                        {status ? 'Không có phiếu nào ở trạng thái này' : 'Bạn chưa gửi yêu cầu hỗ trợ nào'}
                      </div>
                      <div style={{ marginTop: 4, fontSize: 13, color: 'var(--muted)' }}>
                        Gặp lỗi hoặc cần trợ giúp? Bấm <b>Gửi yêu cầu hỗ trợ</b> để báo cho bộ phận hỗ trợ.
                      </div>
                    </>
                  )}
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      <Pagination page={page} pageSize={pageSize} total={total} onChange={changePage} />

      <TicketCreateModal
        open={openForm}
        onClose={() => { setOpenForm(false); load(1, pageSize, status) }}
        originUrl="/me?tab=tickets"
      />
    </div>
  )
}
