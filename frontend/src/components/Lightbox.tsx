import { useEffect } from 'react'
import { toast } from './toast'

// Popup xem ảnh full-screen, có next/prev. Không thêm thư viện — thuần React + CSS inline.
// Điều hướng bằng nút ‹ › hoặc phím mũi tên; đóng bằng ✕ / Esc / click nền.
// Có nút Tải xuống + Sao chép liên kết trên thanh công cụ (CR ticket: bấm ảnh không nhảy tab mới).
type Img = { url: string; filename?: string }

function luuBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url; a.download = filename; document.body.appendChild(a); a.click()
  a.remove(); URL.revokeObjectURL(url)
}

async function taiAnh(img: Img) {
  try {
    const r = await fetch(img.url)
    if (!r.ok) throw new Error()
    const ten = img.filename || decodeURIComponent(img.url.split('/').pop() || 'anh')
    luuBlob(await r.blob(), ten)
  } catch { toast.error('Tải ảnh thất bại') }
}

async function chepLienKet(img: Img) {
  const abs = new URL(img.url, window.location.href).href
  try {
    await navigator.clipboard.writeText(abs)
    toast.success('Đã sao chép liên kết ảnh')
  } catch {
    // Trình duyệt cũ / http nội bộ không có clipboard API — rơi về textarea + execCommand
    const ta = document.createElement('textarea')
    ta.value = abs; document.body.appendChild(ta); ta.select()
    const ok = document.execCommand('copy')
    ta.remove()
    ok ? toast.success('Đã sao chép liên kết ảnh') : toast.error('Không sao chép được liên kết')
  }
}
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
  const toolBtn: React.CSSProperties = {
    width: 40, height: 40, borderRadius: '50%', border: 'none', cursor: 'pointer',
    background: 'rgba(255,255,255,.9)', color: '#111', fontSize: 18,
    display: 'flex', alignItems: 'center', justifyContent: 'center',
  }

  return (
    <div
      onClick={(e) => { if (e.target === e.currentTarget) onClose() }}
      style={{
        position: 'fixed', inset: 0, zIndex: 3000, background: 'rgba(0,0,0,.82)',
        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 24,
      }}>
      {/* Thanh công cụ góc phải: sao chép liên kết · tải xuống · đóng */}
      <div style={{ position: 'absolute', top: 18, right: 22, display: 'flex', gap: 10 }}>
        <button onClick={() => chepLienKet(img)} title="Sao chép liên kết ảnh" style={toolBtn}>
          <i className="ti ti-link" />
        </button>
        <button onClick={() => taiAnh(img)} title="Tải ảnh xuống" style={toolBtn}>
          <i className="ti ti-download" />
        </button>
        <button onClick={onClose} title="Đóng (Esc)" style={{ ...toolBtn, fontSize: 22 }}>✕</button>
      </div>

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
