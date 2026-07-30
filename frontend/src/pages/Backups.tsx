import { useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import { api } from '../api/client'
import { toast } from '../components/toast'
import Pagination from '../components/Pagination'
import { fmtDateTime } from '../utils/datetime'

const STATUS: Record<string, { l: string; c: string }> = {
  running: { l: 'Đang chạy', c: 'warn' },
  success: { l: 'Thành công', c: 'ok' },
  failed: { l: 'Thất bại', c: 'err' },
}
const statusBadge = (s: string) => {
  const x = STATUS[s] || { l: s || '?', c: 'gray' }
  return <span className={'badge ' + x.c}>{x.l}</span>
}

const SOURCE: Record<string, { l: string; bg: string; color: string }> = {
  auto: { l: 'Tự động', bg: '#eff6ff', color: '#2563eb' },
  manual: { l: 'Bấm tay', bg: '#f0fdf4', color: '#16a34a' },
}

function fmtSize(n: number): string {
  if (!n) return '—'
  if (n < 1024) return n + ' B'
  if (n < 1024 * 1024) return (n / 1024).toFixed(1) + ' KB'
  return (n / 1024 / 1024).toFixed(2) + ' MB'
}

export default function Backups() {
  const { can } = useAuth()
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [keep, setKeep] = useState(30)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [busy, setBusy] = useState(false)

  async function load() {
    try {
      const r = await api.get('/api/backups', { params: { page, page_size: pageSize } })
      const data = r.data.data
      setRows(data.items || []); setTotal(data.total || 0)
      if (data.keep) setKeep(data.keep)
    } catch { /* interceptor toast */ }
  }
  useEffect(() => { load() }, [page, pageSize])
  // Poll nhẹ khi có bản đang chạy
  useEffect(() => {
    if (!rows.some((r) => r.status === 'running')) return
    const t = setInterval(load, 4000)
    return () => clearInterval(t)
  }, [rows])

  async function runNow() {
    if (busy) return
    setBusy(true)
    try {
      await api.post('/api/backups/run')
      toast.success('Đã bắt đầu sao lưu — làm mới sau vài giây')
      setTimeout(load, 2000)
    } catch { /* interceptor toast */ } finally { setBusy(false) }
  }

  async function download(id: number) {
    try {
      const r = await api.get(`/api/backups/${id}/download`)
      const url = r.data.data?.url
      if (url) window.open(url, '_blank')
      else toast.error('Không lấy được đường dẫn tải')
    } catch { /* interceptor toast */ }
  }

  async function remove(id: number) {
    if (!window.confirm('Xóa bản sao lưu này? File trên storage cũng sẽ bị xóa.')) return
    try {
      await api.delete(`/api/backups/${id}`)
      toast.success('Đã xóa bản sao lưu')
      load()
    } catch { /* interceptor toast */ }
  }

  return (
    <div>
      {/* ===== HEADER ===== */}
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 18, flexWrap: 'wrap' }}>
        <h2 className="page-title" style={{ margin: 0 }}>Sao lưu CSDL</h2>
        <span style={{ flex: 1 }} />
        {can('backup', 'create') && (
          <button className="btn" onClick={runNow} disabled={busy} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <i className="ti ti-database-export" />{busy ? 'Đang gửi...' : 'Sao lưu ngay'}
          </button>
        )}
      </div>

      {/* ===== INFO BAR ===== */}
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 14, padding: '10px 14px', background: '#eff6ff', borderRadius: 10, border: '1px solid #bfdbfe' }}>
        <i className="ti ti-info-circle" style={{ color: '#3b82f6', fontSize: 16, marginTop: 1, flexShrink: 0 }} />
        <div style={{ fontSize: 12.5, color: '#1e40af', lineHeight: 1.5 }}>
          Hệ thống tự động sao lưu <b>2 lần/ngày</b> (01:00 và 13:00, giờ VN), đẩy file nén lên kho lưu trữ riêng.
          Giữ lại <b>{keep} bản</b> mới nhất, bản cũ hơn sẽ tự xóa. Đường dẫn tải là liên kết tạm thời (hết hạn sau ít phút).
        </div>
      </div>

      {/* ===== TABLE ===== */}
      <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
        <table className="table">
          <thead>
            <tr>
              <th style={{ width: 46, textAlign: 'center' }}>#</th>
              <th>Thời gian tạo</th>
              <th style={{ textAlign: 'center' }}>Nguồn</th>
              <th style={{ textAlign: 'center' }}>Trạng thái</th>
              <th style={{ textAlign: 'right' }}>Dung lượng</th>
              <th>Người thực hiện</th>
              <th>Ghi chú</th>
              <th style={{ textAlign: 'center', width: 120 }}>Thao tác</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => {
              const src = SOURCE[r.source] || { l: r.source, bg: '#f1f5f9', color: '#64748b' }
              return (
                <tr key={r.id}>
                  <td style={{ textAlign: 'center', color: 'var(--muted)', fontSize: 12 }}>{r.id}</td>
                  <td style={{ whiteSpace: 'nowrap' }}>{fmtDateTime(r.started_at || r.created_at)}</td>
                  <td style={{ textAlign: 'center' }}>
                    <span style={{ padding: '2px 8px', borderRadius: 6, fontSize: 12, fontWeight: 600, background: src.bg, color: src.color }}>
                      {src.l}
                    </span>
                  </td>
                  <td style={{ textAlign: 'center' }}>{statusBadge(r.status)}</td>
                  <td style={{ textAlign: 'right', whiteSpace: 'nowrap' }}>{fmtSize(r.size_bytes)}</td>
                  <td>{r.created_by_name}</td>
                  <td style={{ maxWidth: 260, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: r.status === 'failed' ? '#dc2626' : 'var(--muted)' }} title={r.message}>
                    {r.message || '—'}
                  </td>
                  <td style={{ textAlign: 'center', whiteSpace: 'nowrap' }}>
                    {r.status === 'success' && r.file_key && (
                      <button className="btn ghost" title="Tải về" onClick={() => download(r.id)}
                        style={{ padding: '4px 8px', height: 28 }}>
                        <i className="ti ti-download" />
                      </button>
                    )}
                    {can('backup', 'delete') && r.status !== 'running' && (
                      <button className="btn ghost" title="Xóa" onClick={() => remove(r.id)}
                        style={{ padding: '4px 8px', height: 28, color: '#dc2626' }}>
                        <i className="ti ti-trash" />
                      </button>
                    )}
                  </td>
                </tr>
              )
            })}
            {rows.length === 0 && <tr><td colSpan={8} style={{ textAlign: 'center', color: 'var(--muted)', padding: 28 }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 8 }}>
                <i className="ti ti-database-off" style={{ fontSize: 32, opacity: 0.4 }} />
                <span>Chưa có bản sao lưu nào</span>
              </div>
            </td></tr>}
          </tbody>
        </table>
      </div>
      <Pagination page={page} pageSize={pageSize} total={total} onChange={(p, ps) => { setPage(p); setPageSize(ps) }} />
    </div>
  )
}
