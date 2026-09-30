// bao-CR-503 (bản cũ) — ô gõ có gợi ý để THÊM doanh nghiệp nhập khẩu / đối tác nước ngoài vào bộ
// lọc, bê từ `customs-party-picker.tsx` bản v2. Chọn một mục là cộng thêm một chip (cùng cơ chế nút
// «Lọc theo doanh nghiệp này»), ô tự trống lại để gõ tiếp. Tra phía server (`/api/customs/parties`)
// vì đối tượng có hàng nghìn, không nạp hết được.
import { useEffect, useRef, useState } from 'react'
import { api } from '../../api/client'

type Party = { id: number; name: string; tax_code: string }

export default function CustomsPartyPicker({ partyType, selectedIds, placeholder, onPick }: {
  /** 1 = doanh nghiệp trong nước · 2 = đối tác nước ngoài (khớp `PartyType` backend). */
  partyType: 1 | 2
  /** Id đang nằm trong bộ lọc, nối dấu phẩy — để khỏi gợi ý lại người đã chọn. */
  selectedIds: string
  placeholder: string
  onPick: (id: number, name: string) => void
}) {
  const [keyword, setKeyword] = useState('')
  const [items, setItems] = useState<Party[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const box = useRef<HTMLDivElement>(null)

  // Gõ xong ngưng 300ms mới hỏi server; mở ô mà chưa gõ gì thì ra 20 mục đầu theo tên.
  useEffect(() => {
    if (!open) return
    let live = true
    const t = setTimeout(() => {
      setLoading(true)
      api.get('/api/customs/parties', { params: { type: partyType, q: keyword.trim() } })
        .then((r) => { if (live) setItems(r.data.data) })
        .finally(() => { if (live) setLoading(false) })
    }, 300)
    return () => { live = false; clearTimeout(t) }
  }, [keyword, open, partyType])

  // Bấm ra ngoài thì đóng danh sách.
  useEffect(() => {
    const onDown = (e: MouseEvent) => { if (box.current && !box.current.contains(e.target as Node)) setOpen(false) }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [])

  const selected = new Set(selectedIds.split(',').map((v) => v.trim()).filter(Boolean))
  const shown = items.filter((p) => !selected.has(String(p.id)))

  function pick(p: Party) {
    onPick(p.id, p.name)
    setKeyword('')
    setOpen(false)
  }

  return (
    <div ref={box} style={{ position: 'relative' }}>
      <input value={keyword} placeholder={placeholder} onFocus={() => setOpen(true)}
        onChange={(e) => { setKeyword(e.target.value); setOpen(true) }}
        onKeyDown={(e) => {
          if (e.key === 'Escape') setOpen(false)
          // Enter chọn mục đầu — và chặn Enter lan ra ô lọc cha (sẽ bấm «Tìm» với ô chưa chọn gì).
          if (e.key === 'Enter') { e.preventDefault(); if (shown[0]) pick(shown[0]) }
        }} />
      {open && (
        <div style={{ position: 'absolute', top: '100%', left: 0, right: 0, zIndex: 30, marginTop: 2,
          background: '#fff', border: '1px solid #e5e7eb', borderRadius: 8, boxShadow: '0 8px 20px rgba(15,23,42,.12)',
          maxHeight: 280, overflowY: 'auto', fontSize: 13 }}>
          {shown.map((p) => (
            <div key={p.id} onMouseDown={(e) => { e.preventDefault(); pick(p) }}
              style={{ padding: '6px 10px', cursor: 'pointer', borderBottom: '1px solid #f1f5f9' }}
              onMouseEnter={(e) => { e.currentTarget.style.background = '#f1f5f9' }}
              onMouseLeave={(e) => { e.currentTarget.style.background = '' }}>
              {p.name}
              {p.tax_code && <span style={{ color: 'var(--muted)', marginLeft: 6 }}>· MST {p.tax_code}</span>}
            </div>
          ))}
          {!shown.length && (
            <div style={{ padding: '8px 10px', color: 'var(--muted)' }}>{loading ? 'Đang tìm…' : 'Không tìm thấy.'}</div>
          )}
        </div>
      )}
    </div>
  )
}
