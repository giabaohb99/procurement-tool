// bao-CR-728 (bê bao-CR-718 của bản v2) — chi tiết MỘT lô xuất toàn bộ chạy nền (`/customs-prices/exports/:id`).
// Đích của chuông "xuất xong": backend ghi link đường v2 `/procurement/customs-prices/exports/<id>`, App.tsx có route
// cùng đường đó chuyển sang đây. Lô còn chờ / đang xuất thì hỏi lại mỗi 3 giây; tệp đã xong tải được ngay, kể cả khi
// lô chưa xong hẳn. Backend chặn: chỉ người xuất (hoặc có quyền xuất phạm vi tất cả) xem / tải; chỉ người xuất dừng.
import { useCallback, useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { askConfirm } from '../components/confirm'
import { toast } from '../components/toast'
import { blobErrorMessage, downloadBlob } from '../components/customs/customs-shared'
import {
  CUSTOMS_EXPORT_STATUS, CUSTOMS_EXPORTS_PATH, CustomsExportBatch, CustomsExportFile, exportProgressPercent,
  exportStatusBadgeClass, formatFileSize,
} from '../utils/customs-export'
import { fmtDateTime } from '../utils/datetime'

const POLL_MS = 3000

export default function CustomsExportBatchDetail() {
  const { can } = useAuth()
  const navigate = useNavigate()
  const { id } = useParams()
  const batchId = Number(id) > 0 ? Number(id) : 0
  const [batch, setBatch] = useState<CustomsExportBatch | null>(null)
  const [error, setError] = useState('')
  const [downloading, setDownloading] = useState<number | null>(null)
  const [stopping, setStopping] = useState(false)
  // Một cú bấm = một lần tải / một lần dừng (state chỉ đổi ở lượt vẽ sau).
  const busy = useRef(false)
  const allowed = can('customs_price', 'export')

  const load = useCallback(() => {
    if (!allowed || !batchId) return
    api.get(`/api/customs/export-batches/${batchId}`, { _silent: true } as any)
      .then((r) => { setBatch(r.data.data); setError('') })
      .catch((e) => setError(e?.response?.status === 403
        ? (e.response.data?.error?.message || 'Chỉ người đã xuất được xem lô này')
        : 'Không tìm thấy lô xuất này — có thể đường dẫn sai hoặc lô đã bị xóa.'))
  }, [batchId, allowed])
  useEffect(() => { load() }, [load])

  const active = !!batch?.active
  useEffect(() => {
    if (!active) return
    const t = setInterval(load, POLL_MS)
    return () => clearInterval(t)
  }, [active, load])

  async function download(f: CustomsExportFile) {
    if (busy.current || !f.available) return
    busy.current = true
    setDownloading(f.part)
    try {
      await downloadBlob(api, `/api/customs/export-batches/${batchId}/files/${f.part}`, f.filename)
    } catch (e: any) {
      toast.error(await blobErrorMessage(e, 'Không tải được tệp'))
    } finally {
      busy.current = false
      setDownloading(null)
    }
  }

  async function stop() {
    if (busy.current || !batch) return
    const ok = await askConfirm({
      title: `Dừng lô xuất #${batch.id}`,
      message: 'Dừng ghi các tệp còn lại? Tệp đã xong vẫn tải được tới hạn giữ. Muốn xuất tiếp phải tạo lô mới.',
      confirmText: 'Dừng lô',
    })
    if (!ok) return
    busy.current = true
    setStopping(true)
    try {
      const r = await api.post(`/api/customs/export-batches/${batch.id}/cancel`)
      setBatch(r.data.data)
      toast.success(`Đã dừng lô xuất #${batch.id}`)
    } catch { /* interceptor đã báo lỗi */ } finally {
      busy.current = false
      setStopping(false)
    }
  }

  const header = (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10, flexWrap: 'wrap' }}>
      <button className="btn ghost" title="Quay lại Lô xuất của tôi" aria-label="Quay lại Lô xuất của tôi"
        onClick={() => navigate(CUSTOMS_EXPORTS_PATH)}><i className="ti ti-arrow-left" /></button>
      <h2 className="page-title" style={{ margin: 0 }}>Lô xuất #{batch?.id ?? batchId}</h2>
      {batch && <span className={exportStatusBadgeClass(batch.status)}>{batch.status_label || `Trạng thái ${batch.status}`}</span>}
      <span style={{ flex: 1 }} />
      {batch?.active && (
        <button className="btn err" disabled={stopping} onClick={stop}><i className="ti ti-player-stop" />Dừng</button>
      )}
    </div>
  )

  if (!allowed) return (
    <div className="card" style={{ padding: 24, color: 'var(--muted)' }}>
      Tài khoản chưa được cấp quyền <b>Xuất</b> của Tra cứu thị trường. Nhờ quản trị tick quyền này trên vai trò của bạn.
    </div>
  )
  if (!batch) return (
    <div>
      {header}
      <div className="card" style={{ padding: 24, color: 'var(--muted)' }}>{error || 'Đang tải lô xuất…'}</div>
    </div>
  )

  const percent = exportProgressPercent(batch)
  const label = { color: 'var(--muted)', width: 110, flexShrink: 0 } as const
  return (
    <div>
      {header}
      <div className="card" style={{ padding: 16, marginBottom: 12, fontSize: 13.5 }}>
        <div style={{ display: 'grid', gap: 6, marginBottom: 12 }}>
          <div style={{ display: 'flex', gap: 10 }}><span style={label}>Bộ lọc</span>
            <span style={{ wordBreak: 'break-word' }}>{batch.filter_summary || 'Toàn bộ dữ liệu'}</span></div>
          <div style={{ display: 'flex', gap: 10 }}><span style={label}>Lúc tạo</span><span>{fmtDateTime(batch.created_at)}</span></div>
          {batch.finished_at && (
            <div style={{ display: 'flex', gap: 10 }}><span style={label}>Kết thúc</span><span>{fmtDateTime(batch.finished_at)}</span></div>
          )}
          <div style={{ display: 'flex', gap: 10 }}><span style={label}>Hạn giữ tệp</span>
            <span>{batch.expires_at ? fmtDateTime(batch.expires_at) : (batch.active ? 'Tính từ lúc xong' : 'Giữ mãi')}</span></div>
        </div>
        <div role="progressbar" aria-label="Tiến độ xuất" aria-valuenow={percent} aria-valuemin={0} aria-valuemax={100}
          style={{ height: 8, borderRadius: 4, background: '#e5e7eb', overflow: 'hidden', marginBottom: 6 }}>
          <div style={{ width: `${percent}%`, height: '100%', background: 'var(--teal)', transition: 'width .3s' }} />
        </div>
        <div style={{ color: 'var(--muted)' }}>
          Tệp xong: <b style={{ color: 'var(--navy)' }}>{batch.files_done}/{batch.file_count}</b> · Dòng đã ghi:{' '}
          <b style={{ color: 'var(--navy)' }}>
            {batch.rows_done.toLocaleString('vi-VN')}/{batch.total_rows.toLocaleString('vi-VN')}
          </b> ({percent}%){batch.active && ' · đang tự cập nhật, xong sẽ báo chuông'}
        </div>
        {batch.error && <div role="alert" style={{ color: '#b91c1c', marginTop: 8 }}>Lỗi: {batch.error}</div>}
        {batch.status === CUSTOMS_EXPORT_STATUS.expired && (
          <div style={{ color: 'var(--muted)', marginTop: 8 }}>
            Lô đã quá hạn giữ, các tệp đã được dọn. Cần dữ liệu thì tạo lô xuất mới từ Tra cứu thị trường.
          </div>
        )}
      </div>

      <div className="card table-card">
        <div className="table-scroll"><table>
          <thead><tr>
            <th>Tệp</th><th>Tải</th><th>Tên tệp</th>
            <th style={{ textAlign: 'right' }}>Số dòng</th><th style={{ textAlign: 'right' }}>Dung lượng</th>
          </tr></thead>
          <tbody>
            {batch.files.map((f) => (
              <tr key={f.part}>
                <td>{f.part}/{batch.file_count}</td>
                <td>
                  <button className="btn ghost" disabled={!f.available || downloading === f.part}
                    title={f.available ? `Tải ${f.filename}` : 'Tệp đã quá hạn giữ và bị dọn — tạo lô xuất mới'}
                    aria-label={`Tải tệp ${f.part}`} onClick={() => download(f)}>
                    <i className={downloading === f.part ? 'ti ti-loader spin' : 'ti ti-download'} />Tải
                  </button>
                </td>
                <td style={{ wordBreak: 'break-all' }}>{f.filename}</td>
                <td style={{ textAlign: 'right' }}>{f.rows.toLocaleString('vi-VN')}</td>
                <td style={{ textAlign: 'right' }}>{formatFileSize(f.size)}</td>
              </tr>
            ))}
            {!batch.files.length && (
              <tr><td colSpan={5} className="table-empty">
                {batch.active ? 'Đang ghi tệp đầu tiên…' : 'Lô này không có tệp nào.'}
              </td></tr>
            )}
          </tbody>
        </table></div>
      </div>
      <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 8 }}>
        Tệp có cột ID và Thao tác: sửa ô rồi nạp lại qua "Nạp dữ liệu" là ghi đè đúng dòng đó; gõ "xóa" ở cột Thao tác là
        xóa dòng đó. Hoàn tác lô nạp trả lại như cũ.
      </div>
    </div>
  )
}
