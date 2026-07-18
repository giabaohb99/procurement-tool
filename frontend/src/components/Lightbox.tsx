import { useEffect } from 'react'

// Popup xem ảnh full-screen, có next/prev. Không thêm thư viện — thuần React + CSS inline.
// Điều hướng bằng nút ‹ › hoặc phím mũi tên; đóng bằng ✕ / Esc / click nền.
type Img = { url: string; filename?: string }
type Props = {
  images: Img[]
  index: number
  onClose: () => void
  onNav: (i: number) => void   // truyền index mới (đã tính vòng)
}

export default function Lightbox({ images, index, onClose, onNav }: Props) {
  const n = images.length
  const go = (d: number) => onNav((index + d + n) % n)

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose()
      else if (e.key === 'ArrowLeft') go(-1)
      else if (e.key === 'ArrowRight') go(1)
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [index, n])

  if (!n || index < 0 || index >= n) return null
  const img = images[index]

  const navBtn: React.CSSProperties = {
    position: 'absolute', top: '50%', transform: 'translateY(-50%)',
    width: 48, height: 48, borderRadius: '50%', border: 'none', cursor: 'pointer',
    background: 'rgba(255,255,255,.9)', color: '#111', fontSize: 26, lineHeight: 1,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  }

  return (
    <div
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
      style={{
        position: 'fixed', inset: 0, zIndex: 3000, background: 'rgba(0,0,0,.82)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24,
      }}>
      <button onClick={onClose} title="Đóng (Esc)"
        style={{ position: 'absolute', top: 18, right: 22, width: 40, height: 40, borderRadius: '50%',
          border: 'none', cursor: 'pointer', background: 'rgba(255,255,255,.9)', color: '#111', fontSize: 22 }}>✕</button>

      {n > 1 && <button onClick={() => go(-1)} title="Ảnh trước (←)" style={{ ...navBtn, left: 20 }}>‹</button>}

      <figure style={{ margin: 0, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, maxWidth: '92vw', maxHeight: '92vh' }}>
        <img src={img.url} alt={img.filename || ''}
          style={{ maxWidth: '92vw', maxHeight: n > 1 ? '82vh' : '88vh', objectFit: 'contain', borderRadius: 8, boxShadow: '0 8px 40px rgba(0,0,0,.5)' }} />
        <figcaption style={{ color: '#e5e7eb', fontSize: 13 }}>
          {img.filename ? `${img.filename} — ` : ''}{index + 1}/{n}
        </figcaption>
      </figure>

      {n > 1 && <button onClick={() => go(1)} title="Ảnh sau (→)" style={{ ...navBtn, right: 20 }}>›</button>}
    </div>
  )
}
