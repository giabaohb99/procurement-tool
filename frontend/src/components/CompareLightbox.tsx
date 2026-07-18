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
  const [idx, setIdx] = useState(0)   // ảnh đang chọn xem lớn ở bên này
  const n = imgs.length
  const i = n ? Math.min(idx, n - 1) : 0
  const img = n ? imgs[i] : null

  return (
    <div style={{ flex: 1, minWidth: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10 }}>
      <div style={{ color: '#e5e7eb', fontSize: 13, fontWeight: 600 }}>{label}</div>
      {img ? (
        <>
          <img src={img.url} alt={img.filename || ''}
            style={{ maxWidth: '44vw', maxHeight: '64vh', objectFit: 'contain', borderRadius: 8, boxShadow: '0 8px 40px rgba(0,0,0,.5)' }} />
          <div style={{ color: '#e5e7eb', fontSize: 12.5 }}>
            {img.filename ? `${img.filename} — ` : ''}{i + 1}/{n}
          </div>
          {/* Dải thumbnail: bấm để chọn ảnh so sánh */}
          {n > 1 && (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6, justifyContent: 'center', maxWidth: '44vw' }}>
              {imgs.map((a, k) => (
                <img key={k} src={a.url} alt={a.filename || ''} title={a.filename || ''} onClick={() => setIdx(k)}
                  style={{ width: 52, height: 52, objectFit: 'cover', borderRadius: 6, cursor: 'pointer',
                    border: k === i ? '2px solid #38bdf8' : '2px solid transparent', opacity: k === i ? 1 : 0.6 }} />
              ))}
            </div>
          )}
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
