import { useEffect, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { fmtDateTime } from '../utils/datetime'
import { toast } from '../components/toast'
import { askConfirm } from '../components/confirm'
import DocumentAttachmentSection, { AttachmentFile } from '../components/DocumentAttachmentSection'
import { StatusBadge, PriorityBadge, TICKET_STATUS } from './TicketList'

type Message = {
  id: number; body: string; is_staff: boolean
  author_id: number; author_name: string; created_at: string
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

function initialsOf(name: string) {
  return (name || '?').trim().split(' ').slice(-1)[0]?.[0]?.toUpperCase() || '?'
}

export default function TicketDetail() {
  const { id } = useParams()
  const nav = useNavigate()
  const { can } = useAuth()
  // FE không có scope trong map quyền → dùng quyền 'delete' (chỉ nhóm Hỗ trợ/QT có) làm proxy handler.
  const isHandler = can('ticket', 'delete')

  const [t, setT] = useState<Ticket | null>(null)
  const [files, setFiles] = useState<AttachmentFile[]>([])
  const [reply, setReply] = useState('')
  const [sending, setSending] = useState(false)
  const [busy, setBusy] = useState(false)
  const threadRef = useRef<HTMLDivElement | null>(null)

  async function load() {
    try {
      const r = await api.get(`/api/tickets/${id}`)
      setT(r.data.data)
    } catch {
      toast.error('Không mở được phiếu hỗ trợ (ngoài phạm vi hoặc không tồn tại)')
      nav('/tickets')
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

  async function sendReply() {
    if (!reply.trim()) return
    setSending(true)
    try {
      const r = await api.post(`/api/tickets/${id}/messages`, { body: reply.trim() })
      setT(r.data.data); setReply('')
    } catch {
      // interceptor toast
    } finally {
      setSending(false)
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

  const info: { label: string; value: any }[] = [
    { label: 'Mã phiếu', value: t.code },
    { label: 'Bộ phận / Nhóm', value: t.department || '—' },
    { label: 'Mức ưu tiên', value: <PriorityBadge priority={t.priority} /> },
    { label: 'Trạng thái', value: <StatusBadge status={t.status} /> },
    { label: 'Người gửi', value: t.requester_name || '—' },
    { label: 'Người xử lý', value: t.assignee_name || 'Chưa nhận' },
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

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 14, flexWrap: 'wrap' }}>
        <button className="btn ghost" onClick={() => nav('/tickets')}><i className="ti ti-arrow-left" /> Danh sách</button>
        <div style={{ flex: 1, minWidth: 0 }}>
          <h2 className="page-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{t.subject}</span>
            <StatusBadge status={t.status} />
          </h2>
          <div style={{ fontSize: 12.5, color: '#94a3b8', marginTop: 2 }}>{t.code}</div>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', alignItems: 'flex-start' }}>
        {/* Cột trái: luồng tin nhắn + trả lời + đính kèm */}
        <div style={{ flex: '1 1 520px', minWidth: 0, display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
            <div style={{ padding: '12px 16px', borderBottom: '1px solid var(--border)', fontWeight: 700, color: 'var(--navy)', fontSize: 14, display: 'flex', alignItems: 'center', gap: 8 }}>
              <i className="ti ti-messages" style={{ color: 'var(--teal)', fontSize: 18 }} /> Trao đổi
            </div>
            <div ref={threadRef} style={{ maxHeight: 460, overflowY: 'auto', padding: 16, display: 'flex', flexDirection: 'column', gap: 14, background: '#f8fafc' }}>
              {t.messages.map((m) => (
                <div key={m.id} style={{ display: 'flex', gap: 10, flexDirection: m.is_staff ? 'row-reverse' : 'row' }}>
                  <span className="avatar" style={{ flexShrink: 0, background: m.is_staff ? 'var(--teal)' : '#0f172a', width: 34, height: 34, fontSize: 13 }}>
                    {initialsOf(m.author_name)}
                  </span>
                  <div style={{ maxWidth: '78%', display: 'flex', flexDirection: 'column', alignItems: m.is_staff ? 'flex-end' : 'flex-start' }}>
                    <div style={{ fontSize: 11.5, color: '#94a3b8', marginBottom: 3 }}>
                      <b style={{ color: 'var(--navy)' }}>{m.author_name || 'Người dùng'}</b>
                      {m.is_staff && <span className="badge" style={{ background: '#ccfbf1', color: '#0f766e', fontSize: 10.5, fontWeight: 700, padding: '1px 7px', borderRadius: 999, marginLeft: 6 }}>Hỗ trợ</span>}
                      <span style={{ marginLeft: 6 }}>{fmtDateTime(m.created_at)}</span>
                    </div>
                    <div style={{
                      whiteSpace: 'pre-wrap', wordBreak: 'break-word', fontSize: 13.5, lineHeight: 1.5,
                      padding: '10px 14px', borderRadius: 12,
                      background: m.is_staff ? '#e0f2fe' : '#ffffff',
                      border: '1px solid ' + (m.is_staff ? '#bae6fd' : 'var(--border)'),
                      color: 'var(--navy)',
                    }}>
                      {m.body || <span style={{ color: '#94a3b8' }}>(không có nội dung)</span>}
                    </div>
                  </div>
                </div>
              ))}
            </div>
            {/* Ô trả lời */}
            <div style={{ borderTop: '1px solid var(--border)', padding: 12 }}>
              {isClosed ? (
                <div style={{ textAlign: 'center', color: 'var(--muted)', fontSize: 13, padding: '6px 0' }}>
                  <i className="ti ti-lock" /> Phiếu đã đóng. {isHandler ? 'Mở lại để tiếp tục trao đổi.' : 'Mở lại phiếu nếu bạn vẫn cần hỗ trợ.'}
                </div>
              ) : (
                <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end' }}>
                  <textarea value={reply} onChange={(e) => setReply(e.target.value)} rows={2}
                    placeholder="Nhập nội dung trả lời…" style={{ flex: 1, resize: 'vertical' }}
                    onKeyDown={(e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) sendReply() }} />
                  <button className="btn" onClick={sendReply} disabled={sending || !reply.trim()} style={{ flexShrink: 0 }}>
                    {sending ? <i className="ti ti-loader spin" /> : <><i className="ti ti-send" /> Gửi</>}
                  </button>
                </div>
              )}
              {!isClosed && <div style={{ fontSize: 11, color: '#94a3b8', marginTop: 4 }}>Mẹo: Ctrl/⌘ + Enter để gửi nhanh.</div>}
            </div>
          </div>

          <DocumentAttachmentSection
            entity="ticket"
            entityId={t.id}
            permEntity="ticket"
            files={files}
            editable={!isClosed}
            title="Tệp đính kèm"
            maxSizeMb={10}
            onRefresh={loadFiles}
          />
        </div>

        {/* Cột phải: thông tin + hành động */}
        <div style={{ flex: '0 1 300px', minWidth: 260, display: 'flex', flexDirection: 'column', gap: 16 }}>
          <div className="card" style={{ padding: 16 }}>
            <div style={{ fontWeight: 700, color: 'var(--navy)', fontSize: 14, marginBottom: 12 }}>Thông tin phiếu</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {info.map((r) => (
                <div key={r.label} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'center' }}>
                  <span style={{ fontSize: 12.5, color: 'var(--muted)' }}>{r.label}</span>
                  <span style={{ fontSize: 13, color: 'var(--navy)', fontWeight: 600, textAlign: 'right' }}>{r.value}</span>
                </div>
              ))}
            </div>
          </div>

          <div className="card" style={{ padding: 16 }}>
            <div style={{ fontWeight: 700, color: 'var(--navy)', fontSize: 14, marginBottom: 12 }}>Hành động</div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {isHandler ? (
                <>
                  {t.status !== 'in_progress' && !isClosed && (
                    <button className="btn secondary" disabled={busy} onClick={() => changeStatus('in_progress')}>
                      <i className="ti ti-progress" /> Đánh dấu đang xử lý
                    </button>
                  )}
                  {t.status !== 'answered' && !isClosed && (
                    <button className="btn secondary" disabled={busy} onClick={() => changeStatus('answered')}>
                      <i className="ti ti-check" /> Đánh dấu đã trả lời
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
                <>
                  {!isClosed ? (
                    <button className="btn" disabled={busy} onClick={() => changeStatus('closed', 'Bạn đã được giải quyết và muốn đóng phiếu?')}>
                      <i className="ti ti-circle-check" /> Đóng phiếu
                    </button>
                  ) : (
                    <button className="btn secondary" disabled={busy} onClick={() => changeStatus('in_progress')}>
                      <i className="ti ti-lock-open" /> Mở lại phiếu
                    </button>
                  )}
                </>
              )}
            </div>
            <div style={{ fontSize: 11.5, color: '#94a3b8', marginTop: 10, lineHeight: 1.5 }}>
              {isHandler
                ? 'Bạn thuộc nhóm Hỗ trợ: trả lời và đổi trạng thái phiếu của mọi người.'
                : (TICKET_STATUS[t.status]?.label && 'Nhóm Hỗ trợ sẽ phản hồi phiếu của bạn sớm nhất.')}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
