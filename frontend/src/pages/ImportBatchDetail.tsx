import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { toast } from '../components/toast'
import Pagination from '../components/Pagination'
import { fmtDateTime } from '../utils/datetime'
import { IMPORT_MODULE, IMPORT_MODE, statusBadge } from './ImportBatches'

const LEVEL: Record<number, { l: string; c: string }> = {
  0: { l: 'Info', c: '#64748b' }, 1: { l: 'Cảnh báo', c: '#d97706' },
  2: { l: 'Rà soát', c: '#7c3aed' }, 3: { l: 'Lỗi', c: '#dc2626' },
}
const TABS = [
  { key: '', label: 'Tất cả' }, { key: '3', label: 'Lỗi' },
  { key: '2', label: 'Cần rà soát' }, { key: '1', label: 'Cảnh báo' },
]

export default function ImportBatchDetail() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [b, setB] = useState<any>(null)
  const [tab, setTab] = useState('')
  const [logs, setLogs] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(50)

  async function loadBatch() {
    try { const r = await api.get(`/api/imports/${id}`); setB(r.data.data) } catch { /* toast */ }
  }
  async function loadLogs() {
    const params: any = { page, page_size: pageSize }
    if (tab) params.level = tab
    try { const r = await api.get(`/api/imports/${id}/logs`, { params }); setLogs(r.data.data.items || []); setTotal(r.data.data.total || 0) }
    catch { /* toast */ }
  }
  useEffect(() => { loadBatch() }, [id])
  useEffect(() => { loadLogs() }, [id, tab, page, pageSize])
  // Poll khi đang chạy
  useEffect(() => {
    if (!b || b.status > 1) return
    const t = setInterval(() => { loadBatch(); loadLogs() }, 4000)
    return () => clearInterval(t)
  }, [b])

  async function downloadFile() {
    try {
      const r = await api.get(`/api/imports/${id}/file`, { responseType: 'blob' })
      const url = URL.createObjectURL(r.data)
      const a = document.createElement('a'); a.href = url; a.download = b?.filename || 'import.xlsx'
      document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url)
    } catch { toast.error('Không tải được file') }
  }

  if (!b) return <div style={{ padding: 20, color: 'var(--muted)' }}>Đang tải…</div>
  const Stat = ({ label, val, color }: any) => (
    <div style={{ padding: '8px 14px', border: '1px solid var(--border)', borderRadius: 10, minWidth: 92, textAlign: 'center' }}>
      <div style={{ fontSize: 12, color: 'var(--muted)' }}>{label}</div>
      <div style={{ fontSize: 20, fontWeight: 700, color }}>{val}</div>
    </div>
  )
  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14 }}>
        <button className="btn ghost" onClick={() => navigate('/import-batches')}><i className="ti ti-arrow-left" /></button>
        <h2 className="page-title" style={{ margin: 0 }}>Import #{b.id} — {IMPORT_MODULE[b.module]}</h2>
        {statusBadge(b.status)}
        <span style={{ flex: 1 }} />
        <button className="btn ghost" onClick={downloadFile}><i className="ti ti-download" />Tải file</button>
      </div>

      <div className="card" style={{ padding: 16, marginBottom: 16 }}>
        <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap', fontSize: 13.5, marginBottom: 12 }}>
          <div><span style={{ color: 'var(--muted)' }}>Người import: </span><b>{b.created_by_name}</b></div>
          <div><span style={{ color: 'var(--muted)' }}>Bắt đầu: </span>{fmtDateTime(b.created_at)}</div>
          <div><span style={{ color: 'var(--muted)' }}>Kết thúc: </span>{b.finished_at ? fmtDateTime(b.finished_at) : '—'}</div>
          <div><span style={{ color: 'var(--muted)' }}>Chế độ: </span><b>{IMPORT_MODE[b.mode]}</b></div>
          <div><span style={{ color: 'var(--muted)' }}>Tên file: </span>{b.filename}</div>
        </div>
        <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
          <Stat label="Tổng dòng" val={b.total_rows} />
          <Stat label="Tạo" val={b.created_count} color="#15803d" />
          <Stat label="Cập nhật" val={b.updated_count} color="#2563eb" />
          <Stat label="Bỏ qua" val={b.skipped_count} />
          <Stat label="Cảnh báo" val={b.warning_count} color="#d97706" />
          <Stat label="Rà soát" val={b.review_count} color="#7c3aed" />
          <Stat label="Lỗi" val={b.error_count} color="#dc2626" />
        </div>
        {b.status === 3 && b.error_summary && (
          <pre style={{ marginTop: 12, background: '#fef2f2', color: '#991b1b', padding: 10, borderRadius: 8, fontSize: 12, whiteSpace: 'pre-wrap', maxHeight: 180, overflow: 'auto' }}>{b.error_summary}</pre>
        )}
      </div>

      <div style={{ display: 'flex', gap: 6, marginBottom: 10 }}>
        {TABS.map((t) => (
          <button key={t.key} className={'btn ' + (tab === t.key ? '' : 'ghost')} style={{ height: 34 }}
            onClick={() => { setTab(t.key); setPage(1) }}>{t.label}</button>
        ))}
      </div>
      <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
        <table className="table">
          <thead><tr><th>Sheet</th><th>Dòng</th><th>Loại</th><th>Phân loại</th><th>Thông báo</th><th>Tham chiếu</th></tr></thead>
          <tbody>
            {logs.map((lg) => {
              const lv = LEVEL[lg.level] || { l: '?', c: '#666' }
              return (
                <tr key={lg.id}>
                  <td>{lg.sheet}</td><td>{lg.row_no}</td>
                  <td><span className="badge" style={{ background: lv.c + '22', color: lv.c }}>{lv.l}</span></td>
                  <td style={{ fontSize: 12.5, color: 'var(--muted)' }}>{lg.category}</td>
                  <td>{lg.message}</td>
                  <td>{lg.ref_key}{lg.target_code ? ` → ${lg.target_code}` : ''}</td>
                </tr>
              )
            })}
            {logs.length === 0 && <tr><td colSpan={6} style={{ textAlign: 'center', color: 'var(--muted)', padding: 18 }}>Không có dòng log</td></tr>}
          </tbody>
        </table>
      </div>
      <Pagination page={page} pageSize={pageSize} total={total} onChange={(p, ps) => { setPage(p); setPageSize(ps) }} />
    </div>
  )
}
