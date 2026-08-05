import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { fmtDateTime } from '../utils/datetime'
import { askConfirm } from '../components/confirm'
import { toast } from '../components/toast'
import FilterPanel, { FilterItem } from '../components/FilterPanel'
import Pagination from '../components/Pagination'

type Notif = { id: number; title: string; body: string; link: string; is_read: boolean; at: string }

export default function Notifications() {
  const nav = useNavigate()
  const [items, setItems] = useState<Notif[]>([])
  const [total, setTotal] = useState(0)
  const [unread, setUnread] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [tab, setTab] = useState<'all' | 'unread'>('all')
  const [q, setQ] = useState('')
  const timer = useRef<any>(null)

  async function load(p = page, s = pageSize) {
    const params: any = { page: p, page_size: s }
    if (tab === 'unread') params.unread = 'true'
    const qq = q.trim(); if (qq) params.q = qq
    const r = await api.get('/api/notifications', { params })
    const d = r.data.data
    setItems(d.items || []); setTotal(d.total || 0); setUnread(d.unread || 0)
  }

  // Nạp lại khi đổi tab/trang/cỡ trang; tìm kiếm debounce 350ms
  useEffect(() => { setPage(1); load(1, pageSize) /* eslint-disable-next-line */ }, [tab])
  useEffect(() => {
    clearTimeout(timer.current)
    timer.current = setTimeout(() => { setPage(1); load(1, pageSize) }, 350)
    return () => clearTimeout(timer.current)
    // eslint-disable-next-line
  }, [q])
  useEffect(() => { load(1, pageSize) /* eslint-disable-next-line */ }, [])

  function changePage(p: number, s: number) { setPage(p); setPageSize(s); load(p, s) }

  async function openNotif(n: Notif) {
    if (!n.is_read) { try { await api.post(`/api/notifications/${n.id}/read`) } catch { /* noop */ } }
    if (n.link) nav(n.link)
    else load()
  }
  async function markRead(n: Notif, e: React.MouseEvent) {
    e.stopPropagation()
    try { await api.post(`/api/notifications/${n.id}/read`) } catch { /* noop */ }
    load()
  }
  async function delOne(n: Notif, e: React.MouseEvent) {
    e.stopPropagation()
    try { await api.delete(`/api/notifications/${n.id}`) } catch { /* noop */ }
    load()
  }
  async function readAll() {
    try { await api.post('/api/notifications/read-all') } catch { /* noop */ }
    load()
  }
  async function clearRead() {
    if (!(await askConfirm({ title: 'Xóa đã đọc', message: 'Xóa tất cả thông báo ĐÃ ĐỌC của bạn?', confirmText: 'Xóa', danger: true }))) return
    try { const r = await api.delete('/api/notifications/read'); toast.success(r.data.message || 'Đã xóa') } catch { /* noop */ }
    setPage(1); load(1, pageSize)
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
        <h2 className="page-title" style={{ margin: 0 }}>Thông báo{unread > 0 ? ` · ${unread} chưa đọc` : ''}</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          {unread > 0 && <button className="btn ghost" onClick={readAll}><i className="ti ti-checks" />Đánh dấu đã đọc tất cả</button>}
          <button className="btn ghost" style={{ color: 'var(--red)', borderColor: '#fecaca' }} onClick={clearRead}><i className="ti ti-trash" />Xóa đã đọc</button>
        </div>
      </div>

      <FilterPanel onClear={() => { setTab('all'); setQ('') }} canClear={tab !== 'all' || !!q}>
        <FilterItem label="Trạng thái" width={200}>
          <div style={{ display: 'flex', gap: 6, background: '#f1f5f9', borderRadius: 8, padding: 3, height: 40, boxSizing: 'border-box' }}>
            {(['all', 'unread'] as const).map((t) => (
              <button key={t} onClick={() => setTab(t)}
                style={{ flex: 1, border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: 600, padding: '0 12px', borderRadius: 6,
                  background: tab === t ? '#fff' : 'transparent', color: tab === t ? 'var(--navy)' : 'var(--muted)',
                  boxShadow: tab === t ? '0 1px 2px rgba(15,23,42,.12)' : 'none' }}>
                {t === 'all' ? 'Tất cả' : 'Chưa đọc'}
              </button>
            ))}
          </div>
        </FilterItem>
        <FilterItem label="Tìm kiếm" grow>
          <input value={q} placeholder="Tìm theo tiêu đề / nội dung…" onChange={(e) => setQ(e.target.value)} />
        </FilterItem>
      </FilterPanel>

      <div className="card">
        {items.length === 0 && (
          <div style={{ padding: 30, textAlign: 'center', color: '#94a3b8', fontSize: 13.5 }}>
            {tab === 'unread' ? 'Không có thông báo chưa đọc.' : 'Không có thông báo nào.'}
          </div>
        )}
        {items.map((n) => (
          <div key={n.id} onClick={() => openNotif(n)} className="clickable"
            style={{ display: 'flex', gap: 12, padding: '12px 16px', borderBottom: '1px solid #f1f5f9', cursor: 'pointer', background: n.is_read ? '#fff' : '#eff6ff' }}>
            <i className="ti ti-bell" style={{ color: n.is_read ? '#94a3b8' : 'var(--teal)', marginTop: 2, fontSize: 18 }} />
            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{ fontSize: 14, fontWeight: n.is_read ? 500 : 700, color: 'var(--navy)' }}>{n.title}</div>
              <div style={{ fontSize: 13, color: 'var(--muted)', marginTop: 2 }}>{n.body}</div>
              <div style={{ fontSize: 11.5, color: '#94a3b8', marginTop: 3 }}>{fmtDateTime(n.at)}</div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 4 }} onClick={(e) => e.stopPropagation()}>
              {!n.is_read && <button className="icon-btn" title="Đánh dấu đã đọc" onClick={(e) => markRead(n, e)}><i className="ti ti-check" style={{ color: 'var(--teal)' }} /></button>}
              <button className="icon-btn" title="Xóa" onClick={(e) => delOne(n, e)}><i className="ti ti-trash" style={{ color: 'var(--red)' }} /></button>
            </div>
          </div>
        ))}
      </div>

      <Pagination page={page} pageSize={pageSize} total={total} onChange={changePage} />
    </div>
  )
}
