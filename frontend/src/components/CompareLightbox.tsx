import { useEffect, useState } from 'react'

// Lightbox CHIA ĐÔI để đối chiếu: trái = ảnh gốc (catalog SP), phải = ảnh đối chiếu (thực tế).
// Mỗi bên tự next/prev độc lập. Đóng bằng ✕ / Esc / click nền. Không thêm thư viện.
type Img = { url: string; filename?: string }
type Props = {
  left: Img[]
  right: Img[]
  leftLabel?: string
  rightLabel?: string
  onClose: () => void
}

function Side({ imgs, label, empty }: { imgs: Img[]; label: string; empty: string }) {
  const [idx, setIdx] = useState(0)   // ảnh đang xem lớn ở bên này
  const n = imgs.length
  const i = n ? ((idx % n) + n) % n : 0   // vòng lại khi vượt biên
  const go = (d: number) => setIdx((x) => x + d)
  const img = n ? imgs[i] : null

  const nav: React.CSSProperties = {
    position: 'absolute', top: '50%', transform: 'translateY(-50%)', width: 40, height: 40, borderRadius: '50%',
    border: 'none', cursor: 'pointer', background: 'rgba(255,255,255,.9)', color: '#111', fontSize: 24, lineHeight: 1, zIndex: 1,
  }

  return (
    <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
      <div style={{ color: '#e5e7eb', fontSize: 13, fontWeight: 600 }}>{label}</div>
      {img ? (
        <>
          {/* Khung cao cố định 70vh; ảnh absolute-center KHÔNG đổi kích thước khung → nút ‹ › ghim cứng tâm khung (hết giật) */}
          <div style={{ position: 'relative', width: '100%', height: '70vh' }}>
            {n > 1 && <button onClick={() => go(-1)} title="Ảnh trước" style={{ ...nav, left: 6 }}>‹</button>}
            <img src={img.url} alt={img.filename || ''}
              style={{ position: 'absolute', top: 0, right: 0, bottom: 0, left: 0, margin: 'auto',
                maxWidth: '40vw', maxHeight: '100%', objectFit: 'contain', borderRadius: 8, boxShadow: '0 8px 40px rgba(0,0,0,.5)' }} />
            {n > 1 && <button onClick={() => go(1)} title="Ảnh sau" style={{ ...nav, right: 6 }}>›</button>}
          </div>
          <div style={{ color: '#e5e7eb', fontSize: 12.5 }}>
            {img.filename ? `${img.filename} — ` : ''}{i + 1}/{n}
          </div>
        </>
      ) : (
        <div style={{ color: '#9ca3af', fontSize: 13, padding: '40px 12px' }}>{empty}</div>
      )}
    </div>
  )
}

export default function CompareLightbox({ left, right, leftLabel, rightLabel, onClose }: Props) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  return (
    <div onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
      style={{ position: 'fixed', inset: 0, zIndex: 3000, background: 'rgba(0,0,0,.82)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24 }}>
      <button onClick={onClose} title="Đóng (Esc)"
        style={{ position: 'absolute', top: 18, right: 22, width: 40, height: 40, borderRadius: '50%',
          border: 'none', cursor: 'pointer', background: 'rgba(255,255,255,.9)', color: '#111', fontSize: 22, zIndex: 2 }}>✕</button>
      <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start', width: '100%', justifyContent: 'center' }}>
        <Side imgs={left} label={leftLabel || 'Ảnh gốc'} empty="Chưa có ảnh gốc" />
        <div style={{ width: 1, alignSelf: 'stretch', background: 'rgba(255,255,255,.2)' }} />
        <Side imgs={right} label={rightLabel || 'Ảnh đối chiếu'} empty="Chưa có ảnh đối chiếu" />
      </div>
    </div>
  )
}
