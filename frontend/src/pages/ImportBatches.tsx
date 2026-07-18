import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { toast } from '../components/toast'
import Pagination from '../components/Pagination'
import { fmtDateTime } from '../utils/datetime'

export const IMPORT_MODULE: Record<number, string> = { 1: 'Khảo sát', 2: 'Đơn mua hàng' }
export const IMPORT_MODE: Record<number, string> = { 0: 'Chạy thử', 1: 'Ghi' }
export const IMPORT_STATUS: Record<number, { l: string; c: string }> = {
  0: { l: 'Chờ', c: 'gray' }, 1: { l: 'Đang chạy', c: 'warn' }, 2: { l: 'Xong', c: 'ok' }, 3: { l: 'Lỗi', c: 'err' },
}
export const statusBadge = (s: number) => {
  const x = IMPORT_STATUS[s] || { l: '?', c: 'gray' }
  return <span className={'badge ' + x.c}>{x.l}</span>
}

export default function ImportBatches() {
  const navigate = useNavigate()
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)
  const [fModule, setFModule] = useState('')
  const [fStatus, setFStatus] = useState('')
  const [showModal, setShowModal] = useState(false)
  const [upModule, setUpModule] = useState(1)
  const [upMode, setUpMode] = useState(0)
  const [busy, setBusy] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  async function load() {
    const params: any = { page, page_size: pageSize }
    if (fModule) params.module = fModule
    if (fStatus) params.status = fStatus
    try {
      const r = await api.get('/api/imports', { params })
      setRows(r.data.data.items || []); setTotal(r.data.data.total || 0)
    } catch { /* interceptor toast */ }
  }
  useEffect(() => { load() }, [page, pageSize, fModule, fStatus])
  // Poll nhẹ khi có batch đang chạy (để thấy cập nhật khi worker xong)
  useEffect(() => {
    if (!rows.some((r) => r.status <= 1)) return
    const t = setInterval(load, 4000)
    return () => clearInterval(t)
  }, [rows])

  async function doUpload() {
    const file = fileRef.current?.files?.[0]
    if (!file) { toast.error('Chọn file .xlsx'); return }
    const fd = new FormData()
    fd.append('file', file); fd.append('module', String(upModule)); fd.append('mode', String(upMode))
    setBusy(true)
    try {
      await api.post('/api/imports', fd)
      toast.success('Đã nhận file — đang import nền, sẽ báo khi xong')
      setShowModal(false); if (fileRef.current) fileRef.current.value = ''
      setPage(1); load()
    } catch { /* interceptor toast */ } finally { setBusy(false) }
  }

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <h2 className="page-title" style={{ margin: 0 }}>Quản lý Import</h2>
        <span style={{ flex: 1 }} />
        <select value={fModule} onChange={(e) => { setFModule(e.target.value); setPage(1) }}>
          <option value="">— Chức năng —</option><option value="1">Khảo sát</option><option value="2">Đơn mua hàng</option>
        </select>
        <select value={fStatus} onChange={(e) => { setFStatus(e.target.value); setPage(1) }}>
          <option value="">— Trạng thái —</option><option value="0">Chờ</option><option value="1">Đang chạy</option>
          <option value="2">Xong</option><option value="3">Lỗi</option>
        </select>
        <button className="btn" onClick={() => setShowModal(true)}><i className="ti ti-upload" />Import mới</button>
      </div>

      <div className="card" style={{ padding: 0, overflowX: 'auto' }}>
        <table className="table">
          <thead>
            <tr>
              <th>Thời gian</th><th>Người import</th><th>Chức năng</th><th>Tên file</th><th>Chế độ</th>
              <th>Trạng thái</th><th style={{ textAlign: 'right' }}>Tạo</th><th style={{ textAlign: 'right' }}>Cập nhật</th>
              <th style={{ textAlign: 'right' }}>Bỏ qua</th><th style={{ textAlign: 'right' }}>Cảnh báo</th>
              <th style={{ textAlign: 'right' }}>Rà soát</th><th style={{ textAlign: 'right' }}>Lỗi</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="clickable" onClick={() => navigate(`/import-batches/${r.id}`)}>
                <td>{fmtDateTime(r.created_at)}</td>
                <td>{r.created_by_name}</td>
                <td>{IMPORT_MODULE[r.module] || r.module}</td>
                <td style={{ maxWidth: 220, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={r.filename}>{r.filename}</td>
                <td>{IMPORT_MODE[r.mode] || r.mode}</td>
                <td>{statusBadge(r.status)}</td>
                <td style={{ textAlign: 'right' }}>{r.created_count}</td>
                <td style={{ textAlign: 'right' }}>{r.updated_count}</td>
                <td style={{ textAlign: 'right' }}>{r.skipped_count}</td>
                <td style={{ textAlign: 'right', color: r.warning_count ? '#d97706' : undefined }}>{r.warning_count}</td>
                <td style={{ textAlign: 'right', color: r.review_count ? '#7c3aed' : undefined }}>{r.review_count}</td>
                <td style={{ textAlign: 'right', color: r.error_count ? '#dc2626' : undefined }}>{r.error_count}</td>
              </tr>
            ))}
            {rows.length === 0 && <tr><td colSpan={12} style={{ textAlign: 'center', color: 'var(--muted)', padding: 20 }}>Chưa có lần import nào</td></tr>}
          </tbody>
        </table>
      </div>
      <Pagination page={page} pageSize={pageSize} total={total} onChange={(p, ps) => { setPage(p); setPageSize(ps) }} />

      {showModal && (
        <div style={{ position: 'fixed', inset: 0, background: 'rgba(27,37,89,.3)', zIndex: 200, display: 'flex', alignItems: 'flex-start', justifyContent: 'center', padding: '8vh 12px' }} onClick={() => setShowModal(false)}>
          <div className="card" style={{ width: 460, maxWidth: '100%', padding: 20 }} onClick={(e) => e.stopPropagation()}>
            <h3 className="sec-title" style={{ marginTop: 0 }}>Import Excel</h3>
            <div className="form-grid">
              <div className="form-row"><label>Chức năng</label>
                <select value={upModule} onChange={(e) => setUpModule(Number(e.target.value))}>
                  <option value={1}>Khảo sát</option><option value={2}>Đơn mua hàng</option>
                </select>
              </div>
              <div className="form-row"><label>Chế độ</label>
                <select value={upMode} onChange={(e) => setUpMode(Number(e.target.value))}>
                  <option value={0}>Chạy thử (dry-run) — chưa ghi</option><option value={1}>Ghi (apply)</option>
                </select>
              </div>
              <div className="form-row" style={{ gridColumn: '1 / -1' }}><label>File .xlsx</label>
                <input type="file" accept=".xlsx" ref={fileRef} />
              </div>
            </div>
            <div style={{ fontSize: 12.5, color: 'var(--muted)', marginTop: 8 }}>
              File to sẽ chạy nền; xong sẽ có chuông báo. Nên "Chạy thử" trước để xem cảnh báo.
            </div>
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, marginTop: 16 }}>
              <button className="btn ghost" onClick={() => setShowModal(false)}>Đóng</button>
              <button className="btn" disabled={busy} onClick={doUpload}><i className="ti ti-upload" />{busy ? 'Đang gửi...' : 'Bắt đầu import'}</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
