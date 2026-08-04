import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api/client'
import { toast } from '../components/toast'
import { TICKET_DEPARTMENTS, TICKET_PRIORITY } from './TicketList'

// ── Màn hình riêng "Mở phiếu hỗ trợ" (/tickets/new) ──
export default function TicketCreate() {
  const nav = useNavigate()
  const [subject, setSubject] = useState('')
  const [department, setDepartment] = useState(TICKET_DEPARTMENTS[0])
  const [priority, setPriority] = useState('normal')
  const [body, setBody] = useState('')
  const [saving, setSaving] = useState(false)
  // Trang người dùng đang đứng lúc bấm Hỗ trợ (do AppLayout ghi lại) — đính vào phiếu để dễ debug
  const [origin] = useState(() => sessionStorage.getItem('support_origin') || '')

  async function submit() {
    if (!subject.trim()) { toast.error('Vui lòng nhập chủ đề'); return }
    setSaving(true)
    try {
      const r = await api.post('/api/tickets', { subject: subject.trim(), department, priority, body: body.trim(), origin_url: origin })
      toast.success('Đã tạo phiếu hỗ trợ')
      sessionStorage.removeItem('support_origin')
      nav(`/tickets/${r.data.data.id}`)
    } catch {
      // interceptor toast
    } finally {
      setSaving(false)
    }
  }

  const lbl = { fontSize: 12.5, color: 'var(--muted)', fontWeight: 600, marginBottom: 4, display: 'block' } as const

  return (
    <div style={{ maxWidth: 720, margin: '0 auto' }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 14 }}>
        <button className="btn ghost" onClick={() => nav('/tickets')}><i className="ti ti-arrow-left" /> Danh sách</button>
        <h2 className="page-title" style={{ margin: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          <i className="ti ti-headset" style={{ color: 'var(--teal)' }} /> Mở phiếu hỗ trợ
        </h2>
      </div>

      <div className="card" style={{ padding: 22, display: 'flex', flexDirection: 'column', gap: 16 }}>
        <div>
          <label style={lbl}>Chủ đề <span style={{ color: 'var(--red)' }}>*</span></label>
          <input value={subject} onChange={(e) => setSubject(e.target.value)} placeholder="Tóm tắt vấn đề bạn cần hỗ trợ" autoFocus />
        </div>
        <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
          <div style={{ flex: '1 1 240px' }}>
            <label style={lbl}>Bộ phận / Nhóm</label>
            <select value={department} onChange={(e) => setDepartment(e.target.value)}>
              {TICKET_DEPARTMENTS.map((d) => <option key={d} value={d}>{d}</option>)}
            </select>
          </div>
          <div style={{ flex: '1 1 180px' }}>
            <label style={lbl}>Mức ưu tiên</label>
            <select value={priority} onChange={(e) => setPriority(e.target.value)}>
              {Object.entries(TICKET_PRIORITY).map(([k, v]) => <option key={k} value={k}>{v.label}</option>)}
            </select>
          </div>
        </div>
        <div>
          <label style={lbl}>Nội dung</label>
          <textarea value={body} onChange={(e) => setBody(e.target.value)} rows={7} placeholder="Mô tả chi tiết vấn đề, các bước đã thử, ảnh chụp màn hình (đính kèm sau khi tạo phiếu)…" />
        </div>
        {origin && (
          <div style={{ fontSize: 12, color: 'var(--muted)', background: '#f8fafc', border: '1px solid var(--border)', borderRadius: 8, padding: '8px 10px', display: 'flex', alignItems: 'center', gap: 6 }}>
            <i className="ti ti-link" style={{ color: 'var(--teal)' }} />
            <span>Sẽ đính kèm trang bạn đang gặp vấn đề: <b style={{ color: 'var(--navy)' }}>{origin}</b></span>
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, marginTop: 4, paddingTop: 14, borderTop: '1px solid var(--border)' }}>
          <button className="btn ghost" onClick={() => nav('/tickets')} disabled={saving}>Hủy</button>
          <button className="btn" onClick={submit} disabled={saving}>
            {saving ? <><i className="ti ti-loader spin" /> Đang tạo…</> : <><i className="ti ti-send" /> Gửi phiếu</>}
          </button>
        </div>
      </div>
    </div>
  )
}
