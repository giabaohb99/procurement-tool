import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { fmtDateTime } from '../utils/datetime'
import { askConfirm } from './confirm'
import MentionTextarea from './MentionTextarea'

type C = {
  id: number; body: string; parent_id: number | null
  by: string; by_id: number; at: string; mention_user_ids: number[]
}
type U = { id: number; full_name: string; email?: string }

/** Khối bình luận đa hình (dùng cho cấp phiếu entity='survey' và cấp dòng 'survey_line').
 *  Threading 1 cấp, @nhắc, sửa/xóa có điều kiện. */
export default function CommentSection({ entity, entityId, surveyId, surveyCode, onChanged }: {
  entity: string
  entityId: number | string
  surveyId: number | string
  surveyCode?: string
  onChanged?: () => void
}) {
  const { user, can } = useAuth()
  const uid = (user as any)?.id
  const [items, setItems] = useState<C[]>([])
  const [users, setUsers] = useState<U[]>([])
  const [text, setText] = useState(''); const [mentions, setMentions] = useState<number[]>([])
  const [replyOf, setReplyOf] = useState<number | null>(null)
  const [rText, setRText] = useState(''); const [rMentions, setRMentions] = useState<number[]>([])
  const [editId, setEditId] = useState<number | null>(null)
  const [eText, setEText] = useState(''); const [eMentions, setEMentions] = useState<number[]>([])

  const load = () => api.get('/api/comments', { params: { entity, entity_id: entityId }, _silent: true } as any)
    .then((r) => setItems(r.data.data)).catch(() => {})
  // Guard chống race: đổi entityId nhanh (mở popup dòng khác) không ghi đè dữ liệu cũ.
  useEffect(() => {
    let alive = true
    if (entityId) api.get('/api/comments', { params: { entity, entity_id: entityId }, _silent: true } as any)
      .then((r) => { if (alive) setItems(r.data.data) }).catch(() => {})
    else setItems([])
    return () => { alive = false }
  }, [entity, entityId])
  useEffect(() => {
    api.get('/api/users', { params: { page_size: 500 }, _silent: true } as any)
      .then((r) => setUsers((r.data.data.items || []).map((u: any) => ({ id: u.id, full_name: u.full_name, email: u.email }))))
      .catch(() => {})
  }, [])

  const after = () => { load(); onChanged?.() }
  const post = async (body: string, mention_user_ids: number[], parent_id: number | null) => {
    if (!body.trim()) return
    await api.post('/api/comments', {
      entity, entity_id: entityId, body, mention_user_ids, parent_id,
      survey_id: surveyId, survey_code: surveyCode,
    })
    setText(''); setMentions([]); setReplyOf(null); setRText(''); setRMentions([])
    after()
  }
  const saveEdit = async (id: number) => {
    if (!eText.trim()) return
    await api.patch(`/api/comments/${id}`, { body: eText, mention_user_ids: eMentions })
    setEditId(null); after()
  }
  const del = async (id: number) => {
    if (await askConfirm({ message: 'Xóa bình luận này?' })) { await api.delete(`/api/comments/${id}`); after() }
  }

  const roots = items.filter((c) => !c.parent_id)
  const repliesOf = (pid: number) => items.filter((c) => c.parent_id === pid)
  const canDel = (c: C) => c.by_id === uid || can('survey', 'delete')

  const bubble = (c: C, isReply: boolean) => (
    <div key={c.id} style={{ marginLeft: isReply ? 26 : 0, marginBottom: 8 }}>
      <div style={{ display: 'flex', alignItems: 'baseline', gap: 8 }}>
        <b style={{ fontSize: 13 }}>{c.by}</b>
        <span style={{ fontSize: 11.5, color: 'var(--muted)' }}>{fmtDateTime(c.at)}</span>
      </div>
      {editId === c.id ? (
        <div style={{ marginTop: 4 }}>
          <MentionTextarea value={eText} users={users} onChange={(v, m) => { setEText(v); setEMentions(m) }} />
          <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
            <button className="btn" style={{ height: 28, fontSize: 12 }} onClick={() => saveEdit(c.id)}>Lưu</button>
            <button className="btn ghost" style={{ height: 28, fontSize: 12 }} onClick={() => setEditId(null)}>Hủy</button>
          </div>
        </div>
      ) : (
        <>
          <div style={{ fontSize: 13, whiteSpace: 'pre-wrap', margin: '2px 0' }}>{c.body}</div>
          <div style={{ display: 'flex', gap: 12, fontSize: 12 }}>
            {!isReply && (
              <a style={link} onClick={() => { setReplyOf(replyOf === c.id ? null : c.id); setRText(''); setRMentions([]) }}>Trả lời</a>
            )}
            {c.by_id === uid && (
              <a style={link} onClick={() => { setEditId(c.id); setEText(c.body); setEMentions(c.mention_user_ids || []) }}>Sửa</a>
            )}
            {canDel(c) && <a style={{ ...link, color: 'var(--red)' }} onClick={() => del(c.id)}>Xóa</a>}
          </div>
        </>
      )}
      {replyOf === c.id && !isReply && (
        <div style={{ marginTop: 6 }}>
          <MentionTextarea value={rText} users={users} placeholder="Trả lời… (gõ @ để nhắc)"
            onChange={(v, m) => { setRText(v); setRMentions(m) }} />
          <div style={{ display: 'flex', gap: 6, marginTop: 4 }}>
            <button className="btn" style={{ height: 28, fontSize: 12 }} onClick={() => post(rText, rMentions, c.id)}>Gửi</button>
            <button className="btn ghost" style={{ height: 28, fontSize: 12 }} onClick={() => setReplyOf(null)}>Hủy</button>
          </div>
        </div>
      )}
      {repliesOf(c.id).map((r) => bubble(r, true))}
    </div>
  )

  return (
    <div>
      <div style={{ marginBottom: 12 }}>
        {roots.length === 0 && <div style={{ color: '#999', fontSize: 13 }}>Chưa có bình luận nào.</div>}
        {roots.map((c) => bubble(c, false))}
      </div>
      <MentionTextarea value={text} users={users} placeholder="Viết bình luận… (gõ @ để nhắc ai đó)"
        onChange={(v, m) => { setText(v); setMentions(m) }} />
      <div style={{ marginTop: 6 }}>
        <button className="btn" style={{ height: 30, fontSize: 13 }} disabled={!text.trim()}
          onClick={() => post(text, mentions, null)}><i className="ti ti-send" /> Gửi bình luận</button>
      </div>
    </div>
  )
}

const link: React.CSSProperties = { color: 'var(--teal)', cursor: 'pointer', textDecoration: 'none' }
