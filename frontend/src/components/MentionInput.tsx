import { forwardRef, useEffect, useImperativeHandle, useRef, useState } from 'react'

/**
 * Ô nhập bình luận có gõ `@` để nhắc tên (CR-031).
 *
 * Vì sao KHÔNG dùng `<textarea>`: textarea chỉ chứa được chữ thuần, không hiện được chip.
 * Ở đây dùng `contenteditable` với mỗi người được nhắc là một `<span data-uid>` khóa cứng
 * (`contenteditable=false`) — xóa là mất nguyên cụm, không bao giờ còn "@Nguyễn Văn" cụt đầu
 * đuôi mà hệ thống vẫn tưởng là nhắc ai đó.
 *
 * Ô này chạy KHÔNG ĐIỀU KHIỂN (uncontrolled): React không ghi đè nội dung trong lúc gõ, nên
 * bộ gõ tiếng Việt (Telex/VNI) không bị nhảy dấu — lỗi kinh điển khi bọc contenteditable
 * bằng state. Cha lấy nội dung qua ref lúc bấm Gửi.
 *
 * Nội dung trả ra là chữ thuần kèm thẻ `@[<user_id>]` đúng vị trí trong câu, ví dụ:
 *   "nhờ @[12] xem giúp giá của @[7] nhé"
 */

export type Person = {
  user_id: number
  name: string
  code?: string
  avatar?: string
  related?: boolean
}

export type MentionHandle = {
  /** Nội dung kèm thẻ `@[id]`, đã cắt khoảng trắng thừa. */
  getValue: () => string
  clear: () => void
  focus: () => void
}

const LINE = '#eaeef4'
const MUTED = '#94a3b8'

export function initials(name: string): string {
  // Tên người Việt: lấy chữ cái của TÊN (từ cuối) — "Huỳnh Gia Bảo" -> "B".
  // Bỏ qua đuôi ghi chú kiểu "Nhân viên (Demo)" để không ra chữ "(".
  const parts = (name || '').trim().split(/\s+/).filter((w) => /^\p{L}/u.test(w))
  if (!parts.length) return '?'
  return parts[parts.length - 1][0].toUpperCase()
}

/** Dựng thẻ chip cho một người — tạo bằng DOM vì nó nằm trong vùng contenteditable. */
function chipEl(p: Person): HTMLSpanElement {
  const s = document.createElement('span')
  s.dataset.uid = String(p.user_id)
  s.contentEditable = 'false'
  s.textContent = '@' + p.name
  s.style.cssText = 'background:#e5f7ff;color:#00aeef;font-weight:600;border-radius:6px;' +
                    'padding:1px 6px;white-space:nowrap;'
  return s
}

/** Đọc ngược nội dung của ô ra chữ thuần + thẻ `@[id]`. */
function serialize(root: HTMLElement): string {
  let out = ''
  const walk = (node: Node) => {
    node.childNodes.forEach((n) => {
      if (n.nodeType === Node.TEXT_NODE) {
        out += n.textContent || ''
      } else if (n instanceof HTMLElement) {
        if (n.dataset.uid) out += `@[${n.dataset.uid}]`
        else if (n.tagName === 'BR') out += '\n'
        else {
          // Trình duyệt bọc mỗi dòng mới thành <div>/<p> — quy về ký tự xuống dòng
          if (out && !out.endsWith('\n')) out += '\n'
          walk(n)
        }
      }
    })
  }
  walk(root)
  return out.replace(/ /g, ' ').trim()
}

const MentionInput = forwardRef<MentionHandle, {
  placeholder: string
  search: (q: string) => Promise<Person[]>
  onSubmit: () => void
  onCancel?: () => void
  onEmptyChange?: (empty: boolean) => void
  initial?: Person | null
  compact?: boolean
}>(function MentionInput({ placeholder, search, onSubmit, onCancel, onEmptyChange, initial, compact }, ref) {
  const boxRef = useRef<HTMLDivElement>(null)
  const [rong, setRong] = useState(true)
  const [goiY, setGoiY] = useState<Person[]>([])
  const [chon, setChon] = useState(0)
  const [dangTim, setDangTim] = useState(false)
  // Vùng chữ "@abc" đang gõ dở — giữ để lúc chọn người thì thay đúng đoạn đó
  const vung = useRef<{ node: Text; start: number; end: number } | null>(null)
  const timer = useRef<any>(null)
  // Từ khóa của lần tìm gần nhất — cùng từ khóa thì KHÔNG tìm lại, để dòng đang chọn đứng yên
  const truyVan = useRef<string | null>(null)

  useImperativeHandle(ref, () => ({
    getValue: () => (boxRef.current ? serialize(boxRef.current) : ''),
    clear: () => {
      if (!boxRef.current) return
      boxRef.current.innerHTML = ''
      dong()
      capNhatRong()
    },
    focus: () => boxRef.current?.focus(),
  }))

  function capNhatRong() {
    const el = boxRef.current
    const r = !el || (!el.querySelector('[data-uid]') && !(el.textContent || '').trim())
    setRong(r)
    onEmptyChange?.(r)
  }

  function dong() {
    vung.current = null
    truyVan.current = null
    clearTimeout(timer.current)
    setGoiY([])
    setDangTim(false)
    setChon(0)
  }

  // Mồi sẵn chip người đang được trả lời, rồi đặt con trỏ ra sau nó
  useEffect(() => {
    const el = boxRef.current
    if (!el) return
    el.innerHTML = ''
    if (initial) {
      el.appendChild(chipEl(initial))
      el.appendChild(document.createTextNode(' '))
    }
    capNhatRong()
    const sel = window.getSelection()
    if (initial && sel) {
      const r = document.createRange()
      r.selectNodeContents(el)
      r.collapse(false)
      sel.removeAllRanges()
      sel.addRange(r)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  /** Sau mỗi lần gõ: xem con trỏ có đang đứng sau một cụm "@..." hay không. */
  function doQuet() {
    const sel = window.getSelection()
    const node = sel?.anchorNode
    if (!sel || !node || node.nodeType !== Node.TEXT_NODE || !boxRef.current?.contains(node)) {
      dong(); return
    }
    const t = node as Text
    const truoc = (t.textContent || '').slice(0, sel.anchorOffset)
    // `@` phải đứng đầu dòng hoặc sau khoảng trắng — tránh bắt nhầm trong email
    const m = /(^|[\s ])@([^\s @]{0,30})$/.exec(truoc)
    if (!m) { dong(); return }
    vung.current = { node: t, start: sel.anchorOffset - m[2].length - 1, end: sel.anchorOffset }
    const q = m[2]
    // Con trỏ chỉ di chuyển chứ chữ không đổi (bấm mũi tên, Home/End) -> giữ nguyên
    // danh sách VÀ dòng đang chọn. Tìm lại ở đây sẽ kéo highlight về dòng đầu.
    if (truyVan.current === q) return
    truyVan.current = q
    setDangTim(true)
    clearTimeout(timer.current)
    timer.current = setTimeout(async () => {
      try {
        const ds = await search(q)
        // Người dùng có thể đã gõ tiếp / đóng menu trong lúc chờ mạng
        if (vung.current) { setGoiY(ds); setChon(0) }
      } finally {
        setDangTim(false)
      }
    }, 180)
  }

  function chonNguoi(p: Person) {
    const v = vung.current
    const el = boxRef.current
    if (!v || !el) return
    const r = document.createRange()
    r.setStart(v.node, v.start)
    r.setEnd(v.node, Math.min(v.end, (v.node.textContent || '').length))
    r.deleteContents()
    const chip = chipEl(p)
    const cach = document.createTextNode(' ')
    r.insertNode(cach)
    r.insertNode(chip)
    const sel = window.getSelection()
    if (sel) {
      const sau = document.createRange()
      sau.setStartAfter(cach)
      sau.collapse(true)
      sel.removeAllRanges()
      sel.addRange(sau)
    }
    dong()
    capNhatRong()
    el.focus()
  }

  function phim(e: React.KeyboardEvent) {
    if (goiY.length) {
      if (e.key === 'ArrowDown') { e.preventDefault(); setChon((i) => (i + 1) % goiY.length); return }
      if (e.key === 'ArrowUp') { e.preventDefault(); setChon((i) => (i - 1 + goiY.length) % goiY.length); return }
      if (e.key === 'Enter' || e.key === 'Tab') { e.preventDefault(); chonNguoi(goiY[chon]); return }
      if (e.key === 'Escape') { e.preventDefault(); dong(); return }
    }
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') { e.preventDefault(); onSubmit(); return }
    if (e.key === 'Escape' && onCancel) { e.preventDefault(); onCancel() }
  }

  return (
    <div style={{ position: 'relative' }}>
      <div
        ref={boxRef}
        contentEditable
        suppressContentEditableWarning
        role="textbox"
        aria-multiline="true"
        onInput={() => { capNhatRong(); doQuet() }}
        onKeyUp={(e) => {
          // Menu đang mở thì lên/xuống là để CHỌN NGƯỜI, con trỏ không nhúc nhích -> đừng dò lại
          if (goiY.length && (e.key === 'ArrowDown' || e.key === 'ArrowUp')) return
          if (e.key.startsWith('Arrow') || e.key === 'Home' || e.key === 'End') doQuet()
        }}
        onKeyDown={phim}
        onBlur={() => setTimeout(dong, 150)}   // chờ cú bấm chuột vào menu kịp chạy
        // Dán thì chỉ lấy chữ thuần — không kéo theo màu mè, thẻ HTML từ nơi khác
        onPaste={(e) => {
          e.preventDefault()
          document.execCommand('insertText', false, e.clipboardData.getData('text/plain'))
        }}
        style={{ border: `1px solid ${LINE}`, borderRadius: 12, padding: '9px 13px',
                 background: '#fff', minHeight: compact ? 20 : 22, maxHeight: 220,
                 overflowY: 'auto', outline: 'none', fontSize: compact ? 14 : 14.5,
                 lineHeight: 1.55, color: '#1e293b', whiteSpace: 'pre-wrap',
                 wordBreak: 'break-word' }}
      />
      {rong && (
        <div style={{ position: 'absolute', top: 10, left: 14, color: MUTED, pointerEvents: 'none',
                      fontSize: compact ? 14 : 14.5, lineHeight: 1.55 }}>
          {placeholder}
        </div>
      )}

      {(goiY.length > 0 || dangTim) && (
        <div style={{ position: 'absolute', zIndex: 30, top: '100%', left: 0, marginTop: 4,
                      minWidth: 280, maxWidth: 380, background: '#fff', borderRadius: 12,
                      border: `1px solid ${LINE}`, boxShadow: '0 8px 24px rgba(27,37,89,.12)',
                      overflow: 'hidden' }}>
          {goiY.length === 0 ? (
            <div style={{ padding: '10px 14px', fontSize: 13.5, color: MUTED }}>Đang tìm…</div>
          ) : goiY.map((p, i) => (
            <div key={p.user_id}
                 onMouseDown={(e) => { e.preventDefault(); chonNguoi(p) }}
                 onMouseEnter={() => setChon(i)}
                 style={{ display: 'flex', alignItems: 'center', gap: 10, padding: '8px 13px',
                          cursor: 'pointer', background: i === chon ? '#e5f7ff' : '#fff',
                          // Vạch xanh bên trái: nhìn phát biết mũi tên đang đứng ở dòng nào
                          borderLeft: `3px solid ${i === chon ? 'var(--teal)' : 'transparent'}` }}>
              <span style={{ width: 28, height: 28, borderRadius: '50%', flexShrink: 0,
                             background: '#e5f7ff', color: 'var(--teal)', fontWeight: 700,
                             fontSize: 13, display: 'flex', alignItems: 'center',
                             justifyContent: 'center' }}>
                {initials(p.name)}
              </span>
              <span style={{ fontSize: 14, fontWeight: 600, color: 'var(--navy)',
                             overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                {p.name}
              </span>
              {!!p.code && <span style={{ fontSize: 12.5, color: MUTED }}>{p.code}</span>}
              {p.related && (
                <span style={{ marginLeft: 'auto', fontSize: 11.5, color: 'var(--teal)',
                               background: '#e5f7ff', borderRadius: 999, padding: '1px 8px' }}>
                  trong phiếu
                </span>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
})

export default MentionInput
