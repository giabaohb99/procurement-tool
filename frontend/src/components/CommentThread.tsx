import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import { useAuth } from '../auth/AuthContext'
import { toast } from './toast'
import { fmtDateTime, fmtRelative } from '../utils/datetime'
import MentionInput, { initials, MentionHandle, Person } from './MentionInput'

/**
 * Khối trao đổi gắn vào trang chi tiết chứng từ (CR-029, mở rộng ở CR-030 và CR-031).
 *
 * Dùng chung cho mọi loại phiếu qua cặp (entity, entityId) — cùng khuôn với đính kèm.
 * Quyền do backend quyết theo chứng từ cha: ai xem được phiếu thì bình luận được,
 * nên ở đây KHÔNG gọi can() để ẩn/hiện gì thêm.
 *
 * Luồng CHỈ 2 CẤP (kiểu YouTube): gốc + phản hồi. Bấm "Phản hồi" trên một phản hồi thì
 * bài mới vẫn nằm ở cấp 2 và tự mồi sẵn chip "@Tên người đó" trong ô nhập — backend ép
 * luật này, FE chỉ dựng giao diện cho khớp.
 *
 * Nhắc tên (CR-031): gõ `@` giữa câu để chọn người, nhắc được nhiều người trong một bài.
 * Nội dung lưu kèm thẻ `@[<user_id>]`; ở đây tra tên theo `mentions` trả từ API để dựng chip,
 * nên ai đổi tên thì bình luận cũ cũng hiện tên mới.
 *
 * Bố cục: MỖI LUỒNG GỐC LÀ MỘT THẺ RIÊNG (gốc + nhánh phản hồi của nó nằm trong cùng thẻ),
 * để nhìn ra ngay đâu là một mạch trao đổi thay vì một danh sách dài dính liền.
 */

type CommentItem = {
  id: number
  body: string
  parent_id: number
  author_id: number
  author_name: string
  author_code: string
  author_avatar: string
  created_at: string
  can_delete: boolean
  like_count: number
  liked: boolean
  reply_to_user_id: number
  reply_to_name: string
  mentions: { user_id: number; name: string }[]
  reply_count?: number
}

// Số gốc mỗi lần tải thêm — phải khớp PAGE_SIZE ở backend (comment/service.py).
const MOI_LAN = 10
const MUTED = '#94a3b8'
const LINE = '#eaeef4'
const DANGER = '#e11d48'

function linkBtn(color = MUTED, size = 13.5): React.CSSProperties {
  return { border: 'none', background: 'none', padding: 0, cursor: 'pointer', color,
           fontSize: size, fontFamily: 'inherit', fontWeight: 600, lineHeight: 1.2 }
}

function Chip({ name, onClear }: { name: string; onClear?: () => void }) {
  return (
    <span style={{ background: '#e5f7ff', color: 'var(--teal)', fontWeight: 600, fontSize: 13,
                   borderRadius: 6, padding: '2px 8px', marginRight: 6, whiteSpace: 'nowrap',
                   display: 'inline-flex', alignItems: 'center', gap: 5 }}>
      @{name}
      {onClear && (
        <i className="ti ti-x" style={{ fontSize: 13, cursor: 'pointer', opacity: 0.75 }}
           onClick={onClear} title="Bỏ nhắc tên" />
      )}
    </span>
  )
}

function Avatar({ name, src, size }: { name: string; src?: string; size: number }) {
  if (src) {
    return <img src={src} alt=""
                style={{ width: size, height: size, borderRadius: '50%', objectFit: 'cover', flexShrink: 0 }} />
  }
  return (
    <span style={{ width: size, height: size, borderRadius: '50%', flexShrink: 0,
                   background: '#e5f7ff', color: 'var(--teal)',
                   display: 'flex', alignItems: 'center', justifyContent: 'center',
                   fontWeight: 700, fontSize: size <= 32 ? 13 : 15 }}>
      {initials(name)}
    </span>
  )
}

/** Dựng nội dung bình luận: thẻ `@[12]` thành chip, phần còn lại giữ nguyên chữ. */
function renderBody(body: string, mentions: { user_id: number; name: string }[]) {
  if (!body.includes('@[')) return body
  const ten = new Map(mentions.map((m) => [m.user_id, m.name]))
  const ra: any[] = []
  const re = /@\[(\d+)\]/g
  let cuoi = 0
  let m: RegExpExecArray | null
  while ((m = re.exec(body))) {
    if (m.index > cuoi) ra.push(body.slice(cuoi, m.index))
    // Người bị xóa tài khoản: vẫn hiện chip nhưng ghi rõ không tra được tên
    ra.push(<Chip key={m.index} name={ten.get(+m[1]) || 'không rõ'} />)
    cuoi = m.index + m[0].length
  }
  ra.push(body.slice(cuoi))
  return ra
}

/** Ô nhập bo tròn có gõ `@` để nhắc tên; tự quản nội dung, cha chỉ nhận chuỗi lúc gửi. */
function Composer({ meName, meAvatar, placeholder, search, onSend, onCancel, initial, compact }: {
  meName: string
  meAvatar?: string
  placeholder: string
  search: (q: string) => Promise<Person[]>
  onSend: (body: string) => Promise<void>
  onCancel?: () => void
  initial?: Person | null
  compact?: boolean
}) {
  const h = useRef<MentionHandle>(null)
  const [rong, setRong] = useState(!initial)
  const [dangGui, setDangGui] = useState(false)

  async function gui() {
    const b = (h.current?.getValue() || '').trim()
    if (!b || dangGui) return
    setDangGui(true)
    try {
      await onSend(b)
      h.current?.clear()      // gửi lỗi thì KHÔNG xóa, người viết còn giữ lại được bài
    } finally {
      setDangGui(false)
    }
  }

  return (
    <div style={{ display: 'flex', gap: 10, alignItems: 'flex-start' }}>
      <Avatar name={meName} src={meAvatar} size={compact ? 32 : 36} />
      <div style={{ flex: 1, minWidth: 0 }}>
        <MentionInput ref={h} placeholder={placeholder} search={search} onSubmit={gui}
                      onCancel={onCancel} onEmptyChange={setRong} initial={initial}
                      compact={compact} />
        {/* Ô trả lời để trống thì không bày nút — giữ luồng gọn, đúng bản vẽ. */}
        {(!compact || !rong) && (
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', marginTop: 8 }}>
            {!!onCancel && (
              <button type="button" className="btn ghost" onClick={onCancel}
                      style={{ padding: '6px 14px', fontSize: 13.5 }}>Hủy</button>
            )}
            <button type="button" className="btn" onClick={gui} disabled={rong || dangGui}
                    style={{ padding: '6px 16px', fontSize: 13.5, opacity: rong || dangGui ? 0.5 : 1 }}>
              {dangGui ? 'Đang gửi…' : 'Gửi'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

/** Một bình luận (gốc hoặc phản hồi) — khác nhau ở cỡ avatar và chip mã nhân sự. */
function Row({ c, likers, onLike, onLikers, onReply, onRemove }: {
  c: CommentItem
  likers?: string[]
  onLike: (c: CommentItem) => void
  onLikers: (c: CommentItem) => void
  onReply: (c: CommentItem) => void
  onRemove: (c: CommentItem) => void
}) {
  const sub = !!c.parent_id
  return (
    <div style={{ display: 'flex', gap: 12 }}>
      <Avatar name={c.author_name} src={c.author_avatar} size={sub ? 32 : 40} />
      <div style={{ minWidth: 0, flex: 1 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', gap: 8, flexWrap: 'wrap' }}>
          <span style={{ fontWeight: 700, fontSize: sub ? 14.5 : 15.5, color: 'var(--navy)' }}>
            {c.author_name || 'Không rõ'}
          </span>
          {/* Mã nhân sự chỉ hiện ở bình luận gốc — nhánh phản hồi thêm nữa sẽ rối */}
          {!sub && !!c.author_code && (
            <span style={{ fontSize: 13, color: MUTED, fontWeight: 600 }}>{c.author_code}</span>
          )}
          <span style={{ fontSize: 13, color: MUTED }} title={fmtDateTime(c.created_at)}>
            {fmtRelative(c.created_at)}
          </span>
        </div>
        <div style={{ fontSize: sub ? 14 : 14.5, color: '#334155', whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word', marginTop: 4, lineHeight: 1.6 }}>
          {/* reply_to_name: chip của bình luận cũ (trước CR-031) — nay chip nằm ngay trong nội dung */}
          {!!c.reply_to_name && !c.body.includes('@[') && <Chip name={c.reply_to_name} />}
          {renderBody(c.body, c.mentions || [])}
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: 18, marginTop: 8 }}>
          <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
            <button type="button" onClick={() => onLike(c)} style={linkBtn(c.liked ? 'var(--teal)' : MUTED)}
                    title={c.liked ? 'Bỏ thích' : 'Thích'}>
              <i className="ti ti-thumb-up" style={{ fontSize: 17, verticalAlign: -3 }} />
            </button>
            {c.like_count > 0 && (
              <button type="button" onClick={() => onLikers(c)} title="Xem ai đã thích"
                      style={linkBtn(c.liked ? 'var(--teal)' : MUTED, 13)}>
                {c.like_count}
              </button>
            )}
          </span>
          <button type="button" onClick={() => onReply(c)} style={linkBtn()}>Phản hồi</button>
          {/* Thùng rác nằm NGAY sau "Phản hồi" chứ không đẩy ra mép phải — gần nội dung nó tác động */}
          {c.can_delete && (
            <button type="button" onClick={() => onRemove(c)} title="Xóa bình luận"
                    style={linkBtn(DANGER)}>
              <i className="ti ti-trash" style={{ fontSize: 16, verticalAlign: -3 }} />
            </button>
          )}
        </div>

        {!!likers && (
          <div style={{ fontSize: 12.5, color: MUTED, marginTop: 5 }}>
            {likers.length ? `Đã thích: ${likers.join(', ')}` : 'Chưa ai thích'}
          </div>
        )}
      </div>
    </div>
  )
}

export default function CommentThread({
  entity,
  entityId,
  title = 'Trao đổi',
}: {
  entity: string
  entityId: number
  title?: string
}) {
  const { user } = useAuth()
  const meName = user?.full_name || user?.email || ''
  const [roots, setRoots] = useState<CommentItem[]>([])
  const [total, setTotal] = useState(0)
  const [olderCount, setOlderCount] = useState(0)
  const [oldestId, setOldestId] = useState(0)
  const [replies, setReplies] = useState<Record<number, CommentItem[]>>({})
  const [openIds, setOpenIds] = useState<number[]>([])
  const [active, setActive] = useState<{ rootId: number; nguoi: Person | null } | null>(null)
  const [likers, setLikers] = useState<Record<number, string[]>>({})
  const [newestFirst, setNewestFirst] = useState(false)
  const [loading, setLoading] = useState(true)
  // Đã bấm "Xem thêm" lần nào chưa -> mới có cái để thu gọn lại
  const [daTaiThem, setDaTaiThem] = useState(false)
  const [gapKhoi, setGapKhoi] = useState(false)
  const khung = useRef<HTMLDivElement>(null)

  /** Danh sách người có thể `@` — backend đã xếp người đang dính tới phiếu lên đầu. */
  async function timNguoi(q: string): Promise<Person[]> {
    try {
      const r = await api.get('/api/comments/mentionable', {
        params: { entity, entity_id: entityId, q }, _silent: true,
      } as any)
      return r.data?.data || []
    } catch {
      return []
    }
  }

  async function load(before = 0) {
    if (!entityId) return
    try {
      const r = await api.get('/api/comments', {
        params: { entity, entity_id: entityId, ...(before ? { before_id: before } : {}) },
        _silent: true,
      } as any)
      const d = r.data?.data || {}
      setRoots((prev) => (before ? [...(d.items || []), ...prev] : d.items || []))
      if (before) setDaTaiThem(true)
      setTotal(d.total || 0)
      setOlderCount(d.older_count || 0)
      setOldestId(d.oldest_id || 0)
    } catch {
      // Không có quyền / phiếu ngoài phạm vi: để khối rỗng, không bắn popup làm phiền
      if (!before) setRoots([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    setLoading(true)
    setRoots([]); setReplies({}); setOpenIds([]); setActive(null); setLikers({})
    setDaTaiThem(false); setGapKhoi(false)
    load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [entity, entityId])

  /** Trả luồng về đúng trang đầu (10 gốc mới nhất), gập luôn các nhánh phản hồi đang mở. */
  function thuGon() {
    setReplies({}); setOpenIds([]); setActive(null); setLikers({})
    setDaTaiThem(false)
    load()
    // Đang đọc ở giữa mà luồng ngắn lại thì màn hình nhảy lung tung -> kéo về đầu khối
    khung.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
  }

  /** Sửa 1 bình luận ở bất kỳ cấp nào (dùng cho lượt thích) mà không phải tải lại cả luồng. */
  function patch(cid: number, fn: (c: CommentItem) => CommentItem) {
    setRoots((prev) => prev.map((c) => (c.id === cid ? fn(c) : c)))
    setReplies((prev) => {
      const next: Record<number, CommentItem[]> = {}
      for (const k of Object.keys(prev)) next[+k] = prev[+k].map((c) => (c.id === cid ? fn(c) : c))
      return next
    })
  }

  async function openReplies(rootId: number) {
    if (!replies[rootId]) {
      const r = await api.get(`/api/comments/${rootId}/replies`, { _silent: true } as any)
      setReplies((prev) => ({ ...prev, [rootId]: r.data?.data || [] }))
    }
    setOpenIds((prev) => (prev.includes(rootId) ? prev : [...prev, rootId]))
  }

  function toggleReplies(rootId: number) {
    if (openIds.includes(rootId)) setOpenIds((prev) => prev.filter((i) => i !== rootId))
    else openReplies(rootId)
  }

  function startReply(rootId: number, c: CommentItem) {
    // Trả lời gốc thì không nhắc ai; trả lời một phản hồi thì mồi sẵn chip @tên người đó
    // NGAY TRONG ô nhập — người viết xóa đi được nếu chỉ muốn nói chung.
    setActive({
      rootId,
      nguoi: c.parent_id ? { user_id: c.author_id, name: c.author_name, code: c.author_code } : null,
    })
    openReplies(rootId)
  }

  async function send(text: string) {
    const r = await api.post('/api/comments', { entity, entity_id: entityId, body: text })
    setRoots((prev) => [...prev, { ...r.data.data, reply_count: 0 }])
    setTotal((n) => n + 1)
  }

  async function sendReply(rootId: number, text: string) {
    // Không gửi reply_to_user_id nữa: người được nhắc nằm ngay trong nội dung dưới dạng thẻ @[id],
    // nên xóa chip đi là thật sự không nhắc ai, không còn cái "ẩn" báo lén sau lưng.
    const r = await api.post('/api/comments', {
      entity, entity_id: entityId, body: text, parent_id: rootId,
    })
    const c: CommentItem = r.data.data
    setReplies((prev) => ({ ...prev, [rootId]: [...(prev[rootId] || []), c] }))
    setRoots((prev) => prev.map((x) => (x.id === rootId
      ? { ...x, reply_count: (x.reply_count || 0) + 1 } : x)))
    setTotal((n) => n + 1)
  }

  async function like(c: CommentItem) {
    const r = await api.post(`/api/comments/${c.id}/like`)
    const d = r.data.data
    patch(c.id, (x) => ({ ...x, liked: d.liked, like_count: d.count }))
    setLikers((prev) => { const n = { ...prev }; delete n[c.id]; return n })
  }

  async function showLikers(c: CommentItem) {
    if (likers[c.id]) { setLikers((prev) => { const n = { ...prev }; delete n[c.id]; return n }); return }
    const r = await api.get(`/api/comments/${c.id}/likes`, { _silent: true } as any)
    setLikers((prev) => ({ ...prev, [c.id]: (r.data?.data || []).map((x: any) => x.name) }))
  }

  async function remove(c: CommentItem) {
    const n = c.parent_id ? 0 : c.reply_count || 0
    if (!confirm(n ? `Xóa bình luận này và ${n} phản hồi của nó?` : 'Xóa bình luận này?')) return
    const r = await api.delete(`/api/comments/${c.id}`)
    if (c.parent_id) {
      const pid = c.parent_id
      setReplies((prev) => ({ ...prev, [pid]: (prev[pid] || []).filter((x) => x.id !== c.id) }))
      setRoots((prev) => prev.map((x) => (x.id === pid
        ? { ...x, reply_count: Math.max(0, (x.reply_count || 1) - 1) } : x)))
      setTotal((t) => Math.max(0, t - 1))
    } else {
      setRoots((prev) => prev.filter((x) => x.id !== c.id))
      setReplies((prev) => { const nx = { ...prev }; delete nx[c.id]; return nx })
      setTotal((t) => Math.max(0, t - 1 - n))
    }
    toast.success(r.data?.message || 'Đã xóa bình luận')
  }

  if (!entityId) return null

  // Đổi thứ tự chỉ là chuyện hiển thị: luôn tải N gốc MỚI NHẤT rồi bày xuôi hay ngược tùy chọn.
  const hienThi = newestFirst ? [...roots].reverse() : roots
  const vienNut: React.CSSProperties = {
    border: `1px solid ${LINE}`, background: '#fff', borderRadius: 999,
    padding: '9px 20px', fontSize: 13.5, fontWeight: 600, cursor: 'pointer',
    fontFamily: 'inherit', display: 'inline-flex', alignItems: 'center', gap: 6,
  }
  // Mỗi lần bấm server chỉ trả THÊM 10 gốc (PAGE_SIZE), nên chữ phải ghi đúng 10 —
  // ghi tổng số còn lại dễ làm người dùng tưởng bấm một phát là ra hết.
  const lanNay = Math.min(olderCount, MOI_LAN)
  const chuTaiThem = `Xem thêm ${lanNay} bình luận ${newestFirst ? 'cũ hơn' : 'trước'}`
    + (olderCount > lanNay ? ` (còn ${olderCount})` : '')
  const nutTaiThem = (olderCount > 0 || daTaiThem) && (
    <div style={{ display: 'flex', justifyContent: 'center', gap: 8,
                  margin: newestFirst ? '14px 0 0' : '0 0 14px' }}>
      {olderCount > 0 && (
        <button type="button" onClick={() => load(oldestId)}
                style={{ ...vienNut, color: 'var(--navy)' }}>
          {chuTaiThem}
        </button>
      )}
      {/* Bung ra rồi thì phải có đường lùi — không thì luồng dài chỉ có một chiều */}
      {daTaiThem && (
        <button type="button" onClick={thuGon} style={{ ...vienNut, color: MUTED }}
                title="Chỉ hiện lại 10 bình luận mới nhất">
          <i className="ti ti-chevrons-up" style={{ fontSize: 16 }} />
          Thu gọn
        </button>
      )}
    </div>
  )

  return (
    <div ref={khung}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 9,
                    marginBottom: gapKhoi ? 0 : 14 }}>
        {/* Bấm vào tiêu đề để gập/mở cả khối — phiếu dài, có lúc chỉ muốn xem nội dung phiếu */}
        <button type="button" onClick={() => setGapKhoi((v) => !v)}
                title={gapKhoi ? 'Mở khối trao đổi' : 'Gập khối trao đổi'}
                style={{ border: 'none', background: 'none', padding: 0, cursor: 'pointer',
                         fontFamily: 'inherit', display: 'inline-flex', alignItems: 'center',
                         gap: 9 }}>
          <i className="ti ti-message-circle" style={{ color: 'var(--teal)', fontSize: 21 }} />
          <span style={{ fontWeight: 700, color: 'var(--navy)', fontSize: 17 }}>{title}</span>
          {total > 0 && (
            <span style={{ fontSize: 13, fontWeight: 700, color: '#475569', background: '#eef2f7',
                           borderRadius: 999, padding: '2px 10px' }}>
              {total}
            </span>
          )}
          <i className={`ti ti-chevron-${gapKhoi ? 'down' : 'up'}`}
             style={{ color: MUTED, fontSize: 18 }} />
        </button>
        {!gapKhoi && (
          <button type="button" onClick={() => setNewestFirst((v) => !v)}
                  title="Đổi thứ tự sắp xếp"
                  style={{ ...linkBtn(MUTED), marginLeft: 'auto', display: 'inline-flex',
                           alignItems: 'center', gap: 5 }}>
            <i className="ti ti-arrows-sort" style={{ fontSize: 16, verticalAlign: -3 }} />
            {newestFirst ? 'Mới nhất trước' : 'Cũ nhất trước'}
          </button>
        )}
      </div>

      {gapKhoi ? null : <>
      {!newestFirst && nutTaiThem}

      {loading ? (
        <div style={{ color: MUTED, fontSize: 14 }}>Đang tải…</div>
      ) : roots.length === 0 ? (
        <div style={{ color: MUTED, fontSize: 14, marginBottom: 16, lineHeight: 1.6 }}>
          Chưa có trao đổi nào. Ghi chú, hỏi thêm thông tin hay giải thích lý do đều để ở đây —
          người tạo phiếu và những ai đã tham gia sẽ nhận thông báo.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginBottom: 16 }}>
          {hienThi.map((c) => {
            const open = openIds.includes(c.id)
            const n = c.reply_count || 0
            const act = active && active.rootId === c.id ? active : null
            return (
              <div key={c.id} style={{ background: '#fff', border: `1px solid ${LINE}`,
                                       borderRadius: 14, padding: 18 }}>
                <Row c={c} likers={likers[c.id]} onLike={like} onLikers={showLikers}
                     onReply={(x) => startReply(c.id, x)} onRemove={remove} />

                {n > 0 && (
                  <button type="button" onClick={() => toggleReplies(c.id)}
                          style={{ ...linkBtn('var(--teal)'), marginLeft: 52, marginTop: 8,
                                   display: 'inline-flex', alignItems: 'center', gap: 4 }}>
                    <i className={`ti ti-chevron-${open ? 'up' : 'down'}`} style={{ fontSize: 17 }} />
                    {n} phản hồi
                  </button>
                )}

                {(open || act) && (
                  <div style={{ marginLeft: 14, marginTop: 12, paddingLeft: 18,
                                borderLeft: `2px solid ${LINE}`,
                                display: 'flex', flexDirection: 'column', gap: 14 }}>
                    {open && (replies[c.id] || []).map((r) => (
                      <Row key={r.id} c={r} likers={likers[r.id]} onLike={like}
                           onLikers={showLikers} onReply={(x) => startReply(c.id, x)} onRemove={remove} />
                    ))}

                    {act && (
                      <div style={{ borderTop: open && (replies[c.id] || []).length
                                      ? `1px solid ${LINE}` : 'none', paddingTop: 14 }}>
                        {/* key gắn theo người được nhắc: bấm "Phản hồi" ở dòng khác thì ô nhập
                            dựng lại với chip mới thay vì giữ nguyên chip cũ */}
                        <Composer
                          key={`${act.rootId}:${act.nguoi?.user_id || 0}`}
                          meName={meName} meAvatar={user?.avatar}
                          placeholder="Viết phản hồi… (gõ @ để nhắc tên)"
                          search={timNguoi}
                          onSend={(t) => sendReply(c.id, t)}
                          onCancel={() => setActive(null)}
                          initial={act.nguoi}
                          compact
                        />
                      </div>
                    )}
                  </div>
                )}
              </div>
            )
          })}
        </div>
      )}

      {newestFirst && nutTaiThem}

      <Composer
        meName={meName} meAvatar={user?.avatar}
        placeholder="Viết bình luận… (gõ @ để nhắc tên · Ctrl + Enter để gửi)"
        search={timNguoi} onSend={send}
      />
      </>}
    </div>
  )
}
