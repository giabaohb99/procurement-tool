import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { toast } from './toast'
import FileDropzone from './FileDropzone'
import { fileIcon, fmtSize } from '../utils/file-type'
import { TICKET_DEPARTMENTS, TICKET_PRIORITY } from '../config/ticketMeta'

// Popup "Gửi yêu cầu hỗ trợ" — mở từ icon tai nghe ở menu avatar (không còn trang riêng).
// Mọi ô nhập dùng chung 1 font (font-family: inherit) + 1 cỡ chữ để form không bị lệch phông.

type Props = {
  open: boolean
  onClose: () => void
  originUrl?: string          // trang người dùng đang đứng lúc bấm Hỗ trợ (đính vào phiếu để dễ debug)
}

const LBL: React.CSSProperties = {
  fontSize: 12.5, fontWeight: 600, color: 'var(--muted)',
  display: 'block', marginBottom: 6, fontFamily: 'inherit',
}
const FIELD: React.CSSProperties = {
  fontFamily: 'inherit', fontSize: 13.5, fontWeight: 500,
  color: 'var(--navy)', width: '100%',
}

type UpFile = { file_id: number; filename: string; size: number; content_type: string }

export default function TicketCreateModal({ open, onClose, originUrl = '' }: Props) {
  const nav = useNavigate()
  const [subject, setSubject] = useState('')
  const [department, setDepartment] = useState(TICKET_DEPARTMENTS[0])
  const [priority, setPriority] = useState('normal')
  const [body, setBody] = useState('')
  const [files, setFiles] = useState<UpFile[]>([])
  const [uploading, setUploading] = useState(false)
  const [saving, setSaving] = useState(false)

  // Mỗi lần mở lại popup là một phiếu mới -> reset form, khoá cuộn nền
  useEffect(() => {
    if (!open) return
    setSubject(''); setDepartment(TICKET_DEPARTMENTS[0]); setPriority('normal'); setBody('')
    setFiles([]); setUploading(false)
    document.body.style.overflow = 'hidden'
    // CR-110 (phiếu hỗ trợ TK20082602): KHÔNG đóng bằng phím Esc và KHÔNG đóng khi bấm ra
    // nền. Người dùng gõ xong cả yêu cầu rồi lỡ tay bấm ra ngoài là mất trắng, phải nhập
    // lại từ đầu. Chỉ đóng bằng nút X hoặc nút Hủy — hai thao tác có chủ ý.
    return () => { document.body.style.overflow = '' }
  }, [open])

  if (!open) return null

  // Upload NGAY khi chọn file (chưa có id phiếu) → nhận file_id, gắn vào phiếu lúc Gửi.
  async function upload(list: File[]) {
    if (!list.length) return
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append('entity', 'ticket')
      list.forEach((f) => fd.append('files', f))
      const r = await api.post('/api/attachments/upload-file', fd)
      setFiles((s) => [...s, ...(r.data.data || [])])
    } catch {
      // interceptor toast
    } finally {
      setUploading(false)
    }
  }

  // Dán thẳng ảnh chụp màn hình (Ctrl/⌘ + V) vào ô nội dung
  function onPaste(e: React.ClipboardEvent) {
    const imgs = Array.from(e.clipboardData?.files || []).filter((f) => f.type.startsWith('image/'))
    if (!imgs.length) return
    e.preventDefault()
    upload(imgs)
  }

  async function submit() {
    if (!subject.trim()) { toast.error('Vui lòng nhập chủ đề'); return }
    setSaving(true)
    try {
      const r = await api.post('/api/tickets', {
        subject: subject.trim(), department, priority,
        body: body.trim(), origin_url: originUrl,
        file_ids: files.map((f) => f.file_id),
      })
      toast.success('Đã gửi yêu cầu hỗ trợ')
      onClose()
      nav(`/tickets/${r.data.data.id}`)
    } catch {
      // interceptor toast
    } finally {
      setSaving(false)
    }
  }

  return (
    <div
      style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 140,
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 12 }}>
      <div className="modal-card"
        style={{ width: 620, maxWidth: '96vw', maxHeight: '92vh', background: '#fff', borderRadius: 14,
          boxShadow: '0 24px 40px -12px rgba(15,23,42,.28)', display: 'flex', flexDirection: 'column',
          overflow: 'hidden', fontFamily: 'inherit' }}>

        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          padding: '14px 18px', borderBottom: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
            <span style={{ width: 34, height: 34, borderRadius: 10, background: '#ccfbf1', color: '#0f766e',
              display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <i className="ti ti-headset" style={{ fontSize: 18 }} />
            </span>
            <div style={{ minWidth: 0 }}>
              <h3 style={{ margin: 0, fontSize: 15.5, fontWeight: 700, color: 'var(--navy)' }}>Gửi yêu cầu hỗ trợ</h3>
              <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 1 }}>Nhóm Hỗ trợ sẽ phản hồi ngay trên phiếu.</div>
            </div>
          </div>
          <button className="icon-btn" onClick={onClose} title="Đóng"><i className="ti ti-x" style={{ fontSize: 18 }} /></button>
        </div>

        <div style={{ padding: '16px 18px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div>
            <label style={LBL}>Chủ đề <span style={{ color: 'var(--red)' }}>*</span></label>
            <input value={subject} autoFocus style={FIELD}
              onChange={(e) => setSubject(e.target.value)}
              placeholder="Tóm tắt vấn đề bạn cần hỗ trợ" />
          </div>

          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            <div style={{ flex: '1 1 200px', minWidth: 0 }}>
              <label style={LBL}>Bộ phận / Nhóm</label>
              <select value={department} onChange={(e) => setDepartment(e.target.value)} style={FIELD}>
                {TICKET_DEPARTMENTS.map((d) => <option key={d} value={d}>{d}</option>)}
              </select>
            </div>
            <div style={{ flex: '1 1 300px', minWidth: 0 }}>
              <label style={LBL}>Mức ưu tiên</label>
              <div style={{ display: 'flex', gap: 6, background: '#f1f5f9', borderRadius: 12, padding: 4, height: 40, boxSizing: 'border-box' }}>
                {Object.entries(TICKET_PRIORITY).map(([k, v]) => (
                  <button key={k} type="button" onClick={() => setPriority(k)}
                    style={{ flex: 1, border: 'none', cursor: 'pointer', borderRadius: 9, padding: 0,
                      fontFamily: 'inherit', fontSize: 12.5, fontWeight: 700, whiteSpace: 'nowrap',
                      background: priority === k ? '#fff' : 'transparent',
                      color: priority === k ? v.color : 'var(--muted)',
                      boxShadow: priority === k ? '0 1px 2px rgba(15,23,42,.14)' : 'none' }}>
                    {v.label}
                  </button>
                ))}
              </div>
            </div>
          </div>

          <div>
            <label style={LBL}>Nội dung</label>
            <textarea value={body} rows={6} onChange={(e) => setBody(e.target.value)} onPaste={onPaste}
              style={{ ...FIELD, height: 'auto', minHeight: 132, padding: '10px 14px', lineHeight: 1.55, resize: 'vertical' }}
              placeholder="Mô tả chi tiết vấn đề, các bước đã thử… (dán thẳng ảnh chụp màn hình bằng Ctrl/⌘ + V)" />
          </div>

          <div>
            <label style={LBL}>
              Tệp đính kèm
              {uploading && <span style={{ color: 'var(--teal)', fontWeight: 600, marginLeft: 8 }}><i className="ti ti-loader spin" /> Đang tải lên…</span>}
            </label>
            <FileDropzone hint="Ảnh chụp màn hình, PDF, Word, Excel… tối đa 50MB mỗi tệp" onFiles={upload} />
            {files.length > 0 && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 4, marginTop: 8 }}>
                {files.map((f) => {
                  const ic = fileIcon(f.filename, f.content_type)
                  return (
                    <div key={f.file_id} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5,
                      background: '#f5f7fa', borderRadius: 8, padding: '6px 9px' }}>
                      <i className={'ti ' + ic.icon} style={{ color: ic.color }} />
                      <span style={{ flex: 1, minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--navy)' }}>{f.filename}</span>
                      <span style={{ color: 'var(--muted)' }}>{fmtSize(f.size)}</span>
                      <button className="icon-btn" title="Bỏ tệp này"
                        onClick={() => setFiles((s) => s.filter((x) => x.file_id !== f.file_id))}>
                        <i className="ti ti-x" style={{ fontSize: 14, color: 'var(--red)' }} />
                      </button>
                    </div>
                  )
                })}
              </div>
            )}
          </div>

          {originUrl && (
            <div style={{ fontSize: 12, color: 'var(--muted)', background: '#f8fafc', border: '1px solid var(--border)',
              borderRadius: 10, padding: '9px 11px', display: 'flex', alignItems: 'center', gap: 7 }}>
              <i className="ti ti-link" style={{ color: 'var(--teal)', flexShrink: 0 }} />
              <span style={{ minWidth: 0, wordBreak: 'break-all' }}>
                Đính kèm trang bạn đang xem: <b style={{ color: 'var(--navy)' }}>{originUrl}</b>
              </span>
            </div>
          )}
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '12px 18px', borderTop: '1px solid var(--border)' }}>
          <button className="btn ghost" onClick={onClose} disabled={saving}>Hủy</button>
          <button className="btn" onClick={submit} disabled={saving || uploading || !subject.trim()}>
            {saving ? <><i className="ti ti-loader spin" /> Đang gửi…</> : <><i className="ti ti-send" /> Gửi yêu cầu</>}
          </button>
        </div>
      </div>
    </div>
  )
}
