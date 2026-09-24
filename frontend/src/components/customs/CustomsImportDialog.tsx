// bao-CR-470 — nạp tệp GTT02 (HQ1). Luôn CHẠY THỬ trước: mỗi tệp một lô, báo số dòng, khoảng
// ngày, số ngày bị đảo đã vá và số dòng cũ SẼ BỊ THAY; người nạp xem rồi mới bấm Áp dụng.
//
// Luật thay dữ liệu: lô mới xóa mọi dòng cũ nằm trong khoảng ngày của nó rồi ghi lại — tệp
// GTT02 không có khóa duy nhất (806 dòng trùng khít trong 5 tệp mẫu), nên nạp chồng theo
// khoảng ngày là cách duy nhất không đếm đôi.
import { useEffect, useRef, useState } from 'react'
import { api } from '../../api/client'
import { toast } from '../toast'
import CustomsModal from './CustomsModal'
import { fmtDate } from './customs-shared'

const STATUS = { QUEUED: 0, RUNNING: 1, DONE: 2, FAILED: 3 }
const running = (b: any) => b.status === STATUS.QUEUED || b.status === STATUS.RUNNING

export default function CustomsImportDialog({ onClose, onApplied }: { onClose: () => void; onApplied: () => void }) {
  const [files, setFiles] = useState<File[]>([])
  const [dry, setDry] = useState<any[]>([])        // lô chạy thử
  const [applied, setApplied] = useState<any[]>([]) // lô ghi thật
  const [uploading, setUploading] = useState(false)
  const busy = useRef(false)                       // chặn bấm đúp: state React chậm một nhịp render

  // Hỏi lại trạng thái các lô đang chạy mỗi 1,5 giây
  useEffect(() => {
    const pending = [...dry, ...applied].filter(running)
    if (!pending.length) return
    const t = setTimeout(async () => {
      const fresh = await Promise.all(pending.map((b) => api.get(`/api/customs/imports/${b.id}`).then((r) => r.data.data)))
      const byId = new Map(fresh.map((b) => [b.id, b]))
      setDry((xs) => xs.map((b) => byId.get(b.id) || b))
      setApplied((xs) => xs.map((b) => byId.get(b.id) || b))
    }, 1500)
    return () => clearTimeout(t)
  }, [dry, applied])

  const appliedDone = applied.length > 0 && applied.every((b) => !running(b))
  useEffect(() => {
    if (!appliedDone) return
    const failed = applied.filter((b) => b.status === STATUS.FAILED)
    if (failed.length) toast.error(`${failed.length} tệp ghi lỗi — xem Lịch sử nạp`)
    else toast.success(`Đã nạp ${applied.reduce((s, b) => s + (b.created_count || 0), 0)} dòng hàng`)
    onApplied()
  }, [appliedDone]) // chỉ chạy một lần khi mọi lô ghi thật đã xong

  async function upload() {
    if (busy.current || !files.length) return
    busy.current = true
    setUploading(true)
    try {
      const fd = new FormData()
      files.forEach((f) => fd.append('files', f))
      const r = await api.post('/api/customs/imports', fd)
      setDry(r.data.data)
    } catch { /* interceptor đã báo lỗi */ } finally {
      busy.current = false
      setUploading(false)
    }
  }

  async function apply() {
    if (busy.current) return
    busy.current = true
    try {
      const out = []
      for (const b of dry.filter((x) => x.status === STATUS.DONE && x.created_count > 0)) {
        const r = await api.post(`/api/customs/imports/${b.id}/commit`)
        out.push(r.data.data)
      }
      setApplied(out)
    } catch { /* interceptor đã báo lỗi */ } finally {
      busy.current = false
    }
  }

  const dryDone = dry.length > 0 && dry.every((b) => !running(b))
  const usable = dry.filter((b) => b.status === STATUS.DONE && b.created_count > 0)
  const willReplace = usable.reduce((s, b) => s + (b.deleted_count || 0), 0)
  const stage = applied.length ? 'apply' : dry.length ? 'dry' : 'pick'

  return (
    <CustomsModal title="Nạp dữ liệu hải quan (tệp GTT02)" width={900} onClose={onClose}
      footer={<>
        <button className="btn ghost" onClick={onClose}>{appliedDone ? 'Đóng' : 'Hủy'}</button>
        {stage === 'pick' && (
          <button className="btn" disabled={!files.length || uploading} onClick={upload}>
            <i className="ti ti-player-play" />{uploading ? 'Đang tải lên…' : 'Chạy thử'}
          </button>
        )}
        {stage === 'dry' && (
          <button className="btn" disabled={!dryDone || !usable.length} onClick={apply}>
            <i className="ti ti-check" />Áp dụng {usable.length} tệp
          </button>
        )}
      </>}>
      {stage === 'pick' && (
        <div>
          <p style={{ marginTop: 0, fontSize: 13 }}>
            Chọn một hoặc nhiều tệp <b>.xls / .xlsx</b> xuất từ hệ thống hải quan (mẫu GTT02 — đủ 32 cột).
            Mỗi tệp chạy thử riêng; chưa có gì ghi vào dữ liệu cho tới khi bấm <b>Áp dụng</b>.
          </p>
          <input type="file" multiple accept=".xls,.xlsx" onChange={(e) => setFiles(Array.from(e.target.files || []))} />
          {files.length > 0 && (
            <ul style={{ fontSize: 13, marginBottom: 0 }}>
              {files.map((f) => <li key={f.name}>{f.name} — {(f.size / 1024 / 1024).toFixed(1)} MB</li>)}
            </ul>
          )}
          <div style={{ marginTop: 12, fontSize: 12, color: 'var(--muted)' }}>
            Lưu ý: nạp tệp có khoảng ngày trùng dữ liệu đã có thì các dòng cũ trong khoảng đó được THAY bằng tệp mới
            (tệp hải quan không có mã dòng để đối chiếu từng dòng).
          </div>
        </div>
      )}
      {stage !== 'pick' && (
        <>
          <BatchTable rows={stage === 'apply' ? applied : dry} applying={stage === 'apply'} />
          {stage === 'dry' && dryDone && willReplace > 0 && (
            <div style={{ marginTop: 12, border: '1px solid #f5c26b', background: '#fff8e8', color: '#8a5a00',
              borderRadius: 8, padding: '8px 12px', fontSize: 13 }}>
              <i className="ti ti-alert-triangle" /> Áp dụng sẽ <b>thay {willReplace} dòng cũ</b> nằm trong khoảng ngày
              của các tệp này. Lô đã thay dữ liệu cũ thì KHÔNG hoàn tác được.
            </div>
          )}
          {stage === 'dry' && !dryDone && <div style={{ marginTop: 10, fontSize: 13, color: 'var(--muted)' }}>Đang chạy thử…</div>}
        </>
      )}
    </CustomsModal>
  )
}

function BatchTable({ rows, applying }: { rows: any[]; applying: boolean }) {
  return (
    <div className="table-scroll"><table>
      <thead><tr>
        <th>Tệp</th><th>Trạng thái</th><th style={{ textAlign: 'right' }}>Dòng hàng</th><th>Khoảng ngày</th>
        <th style={{ textAlign: 'right' }}>Đã vá ngày</th><th style={{ textAlign: 'right' }}>{applying ? 'Đã thay' : 'Sẽ thay'}</th>
        <th style={{ textAlign: 'right' }}>Cảnh báo</th>
      </tr></thead>
      <tbody>
        {rows.map((b) => (
          <tr key={b.id}>
            <td style={{ wordBreak: 'break-all' }}>{b.filename}</td>
            <td><StatusBadge b={b} /></td>
            <td style={{ textAlign: 'right' }}>{b.status === STATUS.DONE ? b.created_count : '—'}</td>
            <td>{b.date_from ? `${fmtDate(b.date_from)} → ${fmtDate(b.date_to)}` : '—'}</td>
            <td style={{ textAlign: 'right' }}>{b.date_fixed || 0}</td>
            <td style={{ textAlign: 'right' }}>{b.deleted_count || 0}</td>
            <td style={{ textAlign: 'right' }}>{b.warning_count || 0}</td>
          </tr>
        ))}
        {rows.some((b) => b.status === STATUS.FAILED) && (
          <tr><td colSpan={7} style={{ color: '#b91c1c', fontSize: 12, whiteSpace: 'pre-wrap' }}>
            {rows.filter((b) => b.status === STATUS.FAILED).map((b) => `${b.filename}: ${(b.error_summary || '').split('\n')[0]}`).join('\n')}
          </td></tr>
        )}
      </tbody>
    </table></div>
  )
}

export function StatusBadge({ b }: { b: any }) {
  if (b.status === 4) return <span className="badge gray">Đã hoàn tác</span>
  if (b.status === STATUS.FAILED) return <span className="badge err">Lỗi</span>
  if (b.status === STATUS.DONE) return <span className="badge ok">{b.mode === 0 ? 'Chạy thử xong' : 'Đã ghi'}</span>
  return <span className="badge info">Đang chạy</span>
}
