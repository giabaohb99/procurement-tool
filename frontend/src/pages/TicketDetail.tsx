import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { fmtDateTime } from '../utils/datetime'
import { initialsOf } from '../utils/name'
import { toast } from '../components/toast'
import { askConfirm } from '../components/confirm'
import { fileIcon, fmtSize, isImageFile } from '../utils/file-type'
import { StatusBadge, PriorityBadge } from '../config/ticketMeta'

// Bố cục: THÔNG TIN YÊU CẦU ở trên (tiêu đề + đầy đủ thông tin + mô tả + tệp gửi kèm),
// TRAO ĐỔI ở dưới theo kiểu nhắn tin — đính kèm nằm luôn trong ô trả lời, không có
// khu upload riêng nữa (file gắn vào từng tin nhắn, entity 'ticket_message').

type TFile = { id: number; file_id: number; filename: string; url: string; content_type: string; size: number }
type Message = {
  id: number; body: string; is_staff: boolean
  author_id: number; author_name: string; created_at: string
  files?: TFile[]
}
type Ticket = {
  id: number; code: string; subject: string; department: string
  priority: string; priority_label: string
  status: string; status_label: string
  requester_id: number; requester_name: string
  assignee_id: number; assignee_name: string
  origin_url?: string
  created_at: string; updated_at: string; closed_at?: string
  messages: Message[]
}


/** 1 tệp đính kèm trong bong bóng tin nhắn / phần mô tả: ảnh xem luôn, tệp khác là thẻ bấm mở. */
function FileChip({ f, compact }: { f: TFile; compact?: boolean }) {
  if (isImageFile(f.filename, f.content_type)) {
    return (
      <a href={f.url} target="_blank" rel="noreferrer" title={f.filename}
        style={{ display: 'block', lineHeight: 0, borderRadius: 10, overflow: 'hidden', border: '1px solid var(--border)' }}>
        <img src={f.url} alt={f.filename}
          style={{ display: 'block', maxWidth: compact ? 200 : 240, maxHeight: 180, objectFit: 'cover' }} />
      </a>
    )
  }
  const ic = fileIcon(f.filename, f.content_type)
  return (
    <a href={f.url} target="_blank" rel="noreferrer" title={f.filename}
      style={{ display: 'flex', alignItems: 'center', gap: 8, textDecoration: 'none',
        background: '#fff', border: '1px solid var(--border)', borderRadius: 10, padding: '7px 10px', maxWidth: 260 }}>
      <i className={'ti ' + ic.icon} style={{ fontSize: 20, color: ic.color, flexShrink: 0 }} />
      <span style={{ minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap',
        fontSize: 12.5, fontWeight: 600, color: 'var(--navy)' }}>{f.filename}</span>
      <span style={{ fontSize: 11.5, color: 'var(--muted)', flexShrink: 0 }}>{fmtSize(f.size)}</span>
    </a>
  )
}

export default function TicketDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const { can, user } = useAuth()
  // FE không có scope trong map quyền → dùng quyền 'delete' (chỉ nhóm Hỗ trợ/QT có) làm proxy handler.
  const isHandler = can('ticket', 'delete')
  // Người gửi thường không vào được màn quản lý → quay về tab phiếu của mình ở trang cá nhân.
  const backTo = isHandler ? '/tickets' : '/me?tab=tickets'

  const [t, setT] = useState<Ticket | null>(null)
  const [files, setFiles] = useState<TFile[]>([])     // tệp gửi kèm lúc tạo phiếu (entity 'ticket')
  const [reply, setReply] = useState('')
  const [draft, setDraft] = useState<TFile[]>([])     // tệp đã upload, chờ gắn vào tin nhắn sắp gửi
  const [uploading, setUploading] = useState(false)
  const [sending, setSending] = useState(false)
  const [busy, setBusy] = useState(false)
  const threadRef = useRef<HTMLDivElement | null>(null)
  const pickRef = useRef<HTMLInputElement | null>(null)

  async function load() {
    try {
      const r = await api.get(`/api/tickets/${id}`)
      setT(r.data.data)
    } catch {
      toast.error('Không mở được phiếu hỗ trợ (ngoài phạm vi hoặc không tồn tại)')
      nav(backTo)
    }
  }
  async function loadFiles() {
    try {
      const r = await api.get('/api/attachments', { params: { entity: 'ticket', entity_id: id } })
      setFiles(r.data.data || [])
    } catch { setFiles([]) }
  }

  useEffect(() => { load(); loadFiles() /* eslint-disable-next-line */ }, [id])
  useEffect(() => { threadRef.current?.scrollTo({ top: threadRef.current.scrollHeight }) }, [t?.messages?.length])

  const isClosed = t?.status === 'closed'

  // Upload ngay khi chọn/dán/kéo-thả → giữ file_id, gắn vào tin nhắn lúc bấm Gửi.
  async function upload(list: File[]) {
    if (!list.length) return
    setUploading(true)
    try {
      const fd = new FormData()
      fd.append('entity', 'ticket_message')
      list.forEach((f) => fd.append('files', f))
      const r = await api.post('/api/attachments/upload-file', fd)
      setDraft((s) => [...s, ...(r.data.data || [])])
    } catch {
      // interceptor toast
    } finally {
      setUploading(false)
    }
  }

  function onPaste(e: React.ClipboardEvent) {
    const imgs = Array.from(e.clipboardData?.files || []).filter((f) => f.type.startsWith('image/'))
    if (!imgs.length) return
    e.preventDefault()
    upload(imgs)
  }

  async function sendReply() {
    if (!reply.trim() && !draft.length) return
    setSending(true)
    try {
      const r = await api.post(`/api/tickets/${id}/messages`, {
        body: reply.trim(), file_ids: draft.map((f) => f.file_id),
      })
      setT(r.data.data); setReply(''); setDraft([])
    } catch {
      // interceptor toast
    } finally {
      setSending(false)
    }
  }

  async function assign(assigneeId: number) {
    setBusy(true)
    try {
      const r = await api.post(`/api/tickets/${id}/assign`, { assignee_id: assigneeId })
      setT(r.data.data)
      toast.success(assigneeId ? 'Bạn đã nhận phiếu này' : 'Đã trả phiếu về hàng chờ')
    } catch {
      // interceptor toast
    } finally {
      setBusy(false)
    }
  }

  async function changeStatus(status: string, confirmMsg?: string) {
    if (confirmMsg && !(await askConfirm({ message: confirmMsg }))) return
    setBusy(true)
    try {
      const r = await api.post(`/api/tickets/${id}/status`, { status })
      setT(r.data.data)
      toast.success('Đã cập nhật trạng thái')
    } catch {
      // interceptor toast
    } finally {
      setBusy(false)
    }
  }

  if (!t) return <div className="card" style={{ padding: 30, textAlign: 'center', color: 'var(--muted)' }}>Đang tải…</div>

  // Tin nhắn đầu tiên của người gửi chính là NỘI DUNG yêu cầu → đưa lên khối thông tin,
  // phần Trao đổi bên dưới chỉ còn các lượt qua lại thực sự.
  const first = t.messages[0]
  const desc = first && !first.is_staff ? first : null
  const thread = desc ? t.messages.slice(1) : t.messages

  const info: { label: string; value: any }[] = [
    { label: 'Mã phiếu', value: t.code },
    { label: 'Bộ phận / Nhóm', value: t.department || '—' },
    { label: 'Mức ưu tiên', value: <PriorityBadge priority={t.priority} /> },
    { label: 'Trạng thái', value: <StatusBadge status={t.status} /> },
    { label: 'Người gửi', value: t.requester_name || '—' },
    { label: 'Người xử lý', value: t.assignee_name || <span style={{ color: '#94a3b8' }}>Chưa ai nhận</span> },
    { label: 'Ngày tạo', value: fmtDateTime(t.created_at) },
    { label: 'Cập nhật', value: fmtDateTime(t.updated_at) },
  ]
  if (t.closed_at) info.push({ label: 'Đã đóng', value: fmtDateTime(t.closed_at) })
  if (t.origin_url) {
    const ori = t.origin_url
    info.push({
      label: 'Trang lúc tạo',
      value: ori.startsWith('/')
        ? <a href={ori} onClick={(e) => { e.preventDefault(); nav(ori) }} style={{ color: 'var(--teal)', fontWeight: 600, wordBreak: 'break-all' }} title={ori}>{ori}</a>
        : <span style={{ wordBreak: 'break-all' }}>{ori}</span>,
    })
  }

  const actions = isHandler ? (
    <>
      {!isClosed && (
        t.assignee_id !== user?.id ? (
          <button className="btn" disabled={busy} onClick={() => assign(user?.id || 0)}>
            <i className="ti ti-hand-click" /> {t.assignee_id ? 'Nhận lại phiếu' : 'Nhận phiếu'}
          </button>
        ) : (
          <button className="btn ghost" disabled={busy} onClick={() => assign(0)}>
            <i className="ti ti-user-off" /> Trả phiếu
          </button>
        )
      )}
      {t.status !== 'in_progress' && !isClosed && (
        <button className="btn secondary" disabled={busy} onClick={() => changeStatus('in_progress')}>
          <i className="ti ti-progress" /> Đang xử lý
        </button>
      )}
      {t.status !== 'answered' && !isClosed && (
        <button className="btn secondary" disabled={busy} onClick={() => changeStatus('answered')}>
          <i className="ti ti-check" /> Đã trả lời
        </button>
      )}
      {!isClosed ? (
        <button className="btn" disabled={busy} onClick={() => changeStatus('closed', 'Đóng phiếu hỗ trợ này?')}>
          <i className="ti ti-lock" /> Đóng phiếu
        </button>
      ) : (
        <button className="btn secondary" disabled={busy} onClick={() => changeStatus('in_progress')}>
          <i className="ti ti-lock-open" /> Mở lại phiếu
        </button>
      )}
    </>
  ) : (
    !isClosed ? (
      <button className="btn" disabled={busy} onClick={() => changeStatus('closed', 'Bạn đã được giải quyết và muốn đóng phiếu?')}>
        <i className="ti ti-circle-check" /> Đóng phiếu
      </button>
    ) : (
      <button className="btn secondary" disabled={busy} onClick={() => changeStatus('in_progress')}>
        <i className="ti ti-lock-open" /> Mở lại phiếu
      </button>
    )
  )

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* ── Khối 1: thông tin yêu cầu ── */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap',
          padding: '14px 18px', borderBottom: '1px solid var(--border)' }}>
          <button className="btn ghost" onClick={() => nav(backTo)} style={{ flexShrink: 0 }}>
            <i className="ti ti-arrow-left" /> Danh sách
          </button>
          <div style={{ flex: '1 1 320px', minWidth: 0 }}>
            <h2 className="page-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap', fontSize: 19 }}>
              <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{t.subject}</span>
              <StatusBadge status={t.status} />
              <PriorityBadge priority={t.priority} />
            </h2>
            <div style={{ fontSize: 12.5, color: '#94a3b8', marginTop: 3 }}>
              {t.code} · {t.requester_name || 'Người dùng'} gửi lúc {fmtDateTime(t.created_at)}
            </div>
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>{actions}</div>
        </div>

        <div style={{ padding: '14px 18px', display: 'grid', gap: 12,
          gridTemplateColumns: 'repeat(auto-fit, minmax(160px, 1fr))' }}>
          {info.map((r) => (
            <div key={r.label} style={{ minWidth: 0 }}>
              <div style={{ fontSize: 11.5, color: 'var(--muted)', fontWeight: 600, marginBottom: 3 }}>{r.label}</div>
              <div style={{ fontSize: 13.5, color: 'var(--navy)', fontWeight: 600 }}>{r.value}</div>
            </div>
          ))}
        </div>

        <div style={{ padding: '0 18px 16px' }}>
          <div style={{ fontSize: 11.5, color: 'var(--muted)', fontWeight: 600, marginBottom: 6 }}>Nội dung yêu cầu</div>
          <div style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: 13.5, lineHeight: 1.6,
            color: 'var(--navy)', background: '#f8fafc', border: '1px solid var(--border)',
            borderRadius: 10, padding: '12px 14px' }}>
            {desc?.body || <span style={{ color: '#94a3b8' }}>(người gửi không nhập mô tả)</span>}
          </div>
          {(files.length > 0 || (desc?.files?.length || 0) > 0) && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginTop: 10 }}>
              {[...files, ...(desc?.files || [])].map((f) => <FileChip key={f.id} f={f} />)}
            </div>
          )}
        </div>
      </div>

      {/* ── Khối 2: trao đổi ── */}
      <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
        <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', fontWeight: 700,
          color: 'var(--navy)', fontSize: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
          <i className="ti ti-messages" style={{ color: 'var(--teal)', fontSize: 18 }} /> Trao đổi
          {thread.length > 0 && <span style={{ color: 'var(--muted)', fontWeight: 600, fontSize: 12.5 }}>({thread.length})</span>}
        </div>

        <div ref={threadRef} style={{ maxHeight: 520, minHeight: 160, overflowY: 'auto', padding: 16,
          display: 'flex', flexDirection: 'column', gap: 14, background: '#f8fafc' }}>
          {thread.length === 0 && (
            <div style={{ margin: 'auto', textAlign: 'center', color: '#94a3b8', fontSize: 13 }}>
              <i className="ti ti-message-2" style={{ fontSize: 26, display: 'block', marginBottom: 6 }} />
              Chưa có trao đổi nào. {isHandler ? 'Trả lời để bắt đầu hỗ trợ.' : 'Nhóm Hỗ trợ sẽ phản hồi sớm nhất.'}
            </div>
          )}
          {thread.map((m) => (
            <div key={m.id} style={{ display: 'flex', gap: 10, flexDirection: m.is_staff ? 'row-reverse' : 'row' }}>
              <span className="avatar" style={{ flexShrink: 0, background: m.is_staff ? 'var(--teal)' : '#0f172a', width: 34, height: 34, fontSize: 13 }}>
                {initialsOf(m.author_name)}
              </span>
              <div style={{ maxWidth: '78%', display: 'flex', flexDirection: 'column', gap: 6, alignItems: m.is_staff ? 'flex-end' : 'flex-start' }}>
                <div style={{ fontSize: 11.5, color: '#94a3b8' }}>
                  <b style={{ color: 'var(--navy)' }}>{m.author_name || 'Người dùng'}</b>
                  {m.is_staff && <span className="badge" style={{ background: '#ccfbf1', color: '#0f766e', fontSize: 10.5, fontWeight: 700, padding: '1px 7px', borderRadius: 999, marginLeft: 6 }}>Hỗ trợ</span>}
                  <span style={{ marginLeft: 6 }}>{fmtDateTime(m.created_at)}</span>
                </div>
                {m.body && (
                  <div style={{
                    whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: 13.5, lineHeight: 1.5,
                    padding: '10px 14px', borderRadius: 12,
                    background: m.is_staff ? '#e0f2fe' : '#ffffff',
                    border: '1px solid ' + (m.is_staff ? '#bae6fd' : 'var(--border)'),
                    color: 'var(--navy)',
                  }}>
                    {m.body}
                  </div>
                )}
                {(m.files?.length || 0) > 0 && (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, justifyContent: m.is_staff ? 'flex-end' : 'flex-start' }}>
                    {m.files!.map((f) => <FileChip key={f.id} f={f} compact />)}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* Ô trả lời kiểu nhắn tin: gõ chữ + kẹp file + dán ảnh + kéo thả, tất cả trong 1 ô */}
        <div style={{ borderTop: '1px solid var(--border)', padding: 12 }}>
          {isClosed ? (
            <div style={{ textAlign: 'center', color: 'var(--muted)', fontSize: 13, padding: '6px 0' }}>
              <i className="ti ti-lock" /> Phiếu đã đóng. {isHandler ? 'Mở lại để tiếp tục trao đổi.' : 'Mở lại phiếu nếu bạn vẫn cần hỗ trợ.'}
            </div>
          ) : (
            <div
              onDragOver={(e) => e.preventDefault()}
              onDrop={(e) => { e.preventDefault(); upload(Array.from(e.dataTransfer.files || [])) }}
              style={{ border: '1px solid var(--border)', borderRadius: 12, background: '#fff', padding: 8 }}>
              {draft.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, padding: '2px 2px 8px' }}>
                  {draft.map((f) => {
                    const ic = fileIcon(f.filename, f.content_type)
                    return (
                      <span key={f.file_id} style={{ display: 'inline-flex', alignItems: 'center', gap: 6,
                        background: '#f1f5f9', borderRadius: 999, padding: '4px 6px 4px 10px', fontSize: 12.5, maxWidth: 240 }}>
                        <i className={'ti ' + ic.icon} style={{ color: ic.color }} />
                        <span style={{ minWidth: 0, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', color: 'var(--navy)', fontWeight: 600 }}>{f.filename}</span>
                        <span style={{ color: 'var(--muted)' }}>{fmtSize(f.size)}</span>
                        <button className="icon-btn" title="Bỏ tệp này" style={{ width: 20, height: 20 }}
                          onClick={() => setDraft((s) => s.filter((x) => x.file_id !== f.file_id))}>
                          <i className="ti ti-x" style={{ fontSize: 13, color: 'var(--red)' }} />
                        </button>
                      </span>
                    )
                  })}
                </div>
              )}
              <textarea value={reply} rows={2} onChange={(e) => setReply(e.target.value)} onPaste={onPaste}
                placeholder="Nhập nội dung trả lời… (kéo thả tệp vào đây hoặc dán ảnh bằng Ctrl/⌘ + V)"
                style={{ width: '100%', border: 'none', outline: 'none', boxShadow: 'none', background: 'transparent',
                  resize: 'vertical', minHeight: 52, padding: '4px 6px', fontSize: 13.5 }}
                onKeyDown={(e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) sendReply() }} />
              <div style={{ display: 'flex', alignItems: 'center', gap: 8, paddingTop: 4 }}>
                <button className="icon-btn" title="Đính kèm tệp" disabled={uploading} onClick={() => pickRef.current?.click()}>
                  <i className={uploading ? 'ti ti-loader spin' : 'ti ti-paperclip'} style={{ fontSize: 18, color: 'var(--teal)' }} />
                </button>
                <input ref={pickRef} type="file" multiple style={{ display: 'none' }}
                  onChange={(e) => { upload(Array.from(e.target.files || [])); e.target.value = '' }} />
                <span style={{ flex: 1, fontSize: 11.5, color: '#94a3b8' }}>
                  {uploading ? 'Đang tải tệp lên…' : 'Ctrl/⌘ + Enter để gửi nhanh · tối đa 20MB mỗi tệp'}
                </span>
                <button className="btn" onClick={sendReply} disabled={sending || uploading || (!reply.trim() && !draft.length)}>
                  {sending ? <i className="ti ti-loader spin" /> : <><i className="ti ti-send" /> Gửi</>}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
