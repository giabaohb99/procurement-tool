import { useRef, useState } from 'react'

type U = { id: number; full_name: string; email?: string }

/** Textarea có gợi ý @nhắc: gõ "@" → dropdown nhân sự; chọn → chèn "@Họ Tên".
 *  mentionIds được suy lại từ nội dung mỗi lần đổi (khớp "@Họ Tên" với danh sách users). */
export default function MentionTextarea({ value, onChange, users, disabled, placeholder, rows = 2 }: {
  value: string
  onChange: (v: string, mentionIds: number[]) => void
  users: U[]
  disabled?: boolean
  placeholder?: string
  rows?: number
}) {
  const ref = useRef<HTMLTextAreaElement>(null)
  const [menu, setMenu] = useState<{ q: string; at: number } | null>(null)

  // Suy id được @nhắc từ nội dung: khớp tên DÀI trước + kiểm ranh giới từ + "tiêu thụ"
  // đoạn đã khớp → tránh tên ngắn lồng trong tên dài (vd "Văn A" trong "Văn An").
  const deriveMentions = (text: string): number[] => {
    const ids = new Set<number>()
    const sorted = [...users].filter((u) => u.full_name)
      .sort((a, b) => b.full_name.length - a.full_name.length)
    let scratch = text
    for (const u of sorted) {
      const tag = '@' + u.full_name
      const idx = scratch.indexOf(tag)
      if (idx < 0) continue
      const after = scratch[idx + tag.length]
      if (after === undefined || /[^\p{L}\p{N}]/u.test(after)) {
        ids.add(u.id)
        scratch = scratch.slice(0, idx) + ' '.repeat(tag.length) + scratch.slice(idx + tag.length)
      }
    }
    return [...ids]
  }

  const handle = (v: string) => {
    onChange(v, deriveMentions(v))
    const pos = ref.current ? ref.current.selectionStart : v.length
    const m = v.slice(0, pos).match(/@([^\s@]*)$/)
    setMenu(m ? { q: m[1].toLowerCase(), at: pos - m[1].length - 1 } : null)
  }

  const pick = (u: U) => {
    if (!menu) return
    const caret = ref.current?.selectionStart ?? value.length
    const next = `${value.slice(0, menu.at)}@${u.full_name} ${value.slice(caret)}`
    setMenu(null)
    onChange(next, deriveMentions(next))
    setTimeout(() => ref.current?.focus(), 0)
  }

  const matches = menu
    ? users.filter((u) => u.full_name?.toLowerCase().includes(menu.q)).slice(0, 6)
    : []

  return (
    <div style={{ position: 'relative' }}>
      <textarea
        ref={ref} value={value} disabled={disabled} placeholder={placeholder} rows={rows}
        onChange={(e) => handle(e.target.value)}
        onBlur={() => setTimeout(() => setMenu(null), 150)}
        style={{ width: '100%', resize: 'vertical', fontSize: 13, padding: '8px 10px' }}
      />
      {menu && matches.length > 0 && (
        <div style={{
          position: 'absolute', zIndex: 30, top: '100%', left: 0, background: '#fff',
          border: '1px solid var(--border)', borderRadius: 6, boxShadow: '0 4px 14px rgba(0,0,0,.12)',
          minWidth: 220, maxHeight: 200, overflow: 'auto',
        }}>
          {matches.map((u) => (
            <div key={u.id} onMouseDown={(e) => { e.preventDefault(); pick(u) }}
              style={{ padding: '6px 10px', fontSize: 13, cursor: 'pointer' }}
              onMouseEnter={(e) => (e.currentTarget.style.background = '#f1f5f9')}
              onMouseLeave={(e) => (e.currentTarget.style.background = '#fff')}>
              <b>{u.full_name}</b>
              {u.email ? <span style={{ color: 'var(--muted)' }}> · {u.email}</span> : null}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
