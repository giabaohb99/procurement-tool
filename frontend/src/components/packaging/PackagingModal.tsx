import { useEffect } from 'react'
import type { ReactNode } from 'react'
import './packaging.css'

/**
 * Khung hộp thoại dùng chung của cụm Giá bao bì: nền mờ, tiêu đề + dòng phụ, thân, chân nút.
 * Esc hoặc bấm nền để đóng — trừ khi `busy` (đang gửi) để khỏi mất thao tác dở.
 */
export default function PackagingModal({
  title, subtitle, onClose, busy, maxWidth, footer, children,
}: {
  title: string
  subtitle?: ReactNode
  onClose: () => void
  busy?: boolean
  maxWidth?: number
  footer: ReactNode
  children: ReactNode
}) {
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape' && !busy) onClose() }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [busy, onClose])

  return (
    <div className="pkg-modal-overlay" onMouseDown={(e) => { if (e.target === e.currentTarget && !busy) onClose() }}>
      <div className="pkg-modal" role="dialog" aria-modal="true" aria-label={title} style={maxWidth ? { maxWidth } : undefined}>
        <div className="pkg-modal-head">
          <div style={{ flex: 1, minWidth: 0 }}>
            <h3>{title}</h3>
            {subtitle && <div className="sub">{subtitle}</div>}
          </div>
          <button className="pkg-x" onClick={onClose} disabled={busy} aria-label="Đóng"><i className="ti ti-x" /></button>
        </div>
        <div className="pkg-modal-body">{children}</div>
        <div className="pkg-modal-foot">{footer}</div>
      </div>
    </div>
  )
}
