// bao-CR-734 — NGĂN KÉO "Tra cứu thuốc BVTV" của trang chi tiết thuốc, đồng bộ v2
// (`customs-pesticide-detail-page.tsx`, Sheet bên phải): màn hẹp hơn 1280px không có cột tra cứu bên
// phải nữa — trước đây cột này bị đẩy xuống cuối trang, phải cuộn hết mới thấy. Nay bấm nút "Tra cứu"
// ở thẻ đầu trang là mở ngăn kéo từ mép phải; bấm nền tối, nút đóng hoặc phím Esc là đóng.
import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import CustomsPesticideLookup from './CustomsPesticideLookup'

/** Mốc bề rộng hiện cột tra cứu cố định — trùng `.pesticide-detail-layout` (index.css) và `xl` của v2. */
export const PESTICIDE_LOOKUP_WIDE_QUERY = '(min-width: 1280px)'

/** Màn đủ rộng để bày cột tra cứu bên phải hay chưa; theo dõi khi người dùng kéo cửa sổ. */
export function useWideLookupLayout(): boolean {
  const [wide, setWide] = useState(() => window.matchMedia(PESTICIDE_LOOKUP_WIDE_QUERY).matches)
  useEffect(() => {
    const mq = window.matchMedia(PESTICIDE_LOOKUP_WIDE_QUERY)
    const onChange = () => setWide(mq.matches)
    onChange()
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [])
  return wide
}

export default function CustomsPesticideLookupDrawer({ open, onClose, currentPestGroup }: {
  open: boolean
  onClose: () => void
  currentPestGroup: string
}) {
  useEffect(() => {
    if (!open) return
    function onKey(e: KeyboardEvent) { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null
  return createPortal(
    <div onClick={onClose}
      style={{ position: 'fixed', inset: 0, zIndex: 1000, background: 'rgba(0, 0, 0, 0.45)' }}>
      <div role="dialog" aria-modal="true" aria-labelledby="pesticide-lookup-drawer-title"
        onClick={(e) => e.stopPropagation()}
        style={{ position: 'absolute', top: 0, right: 0, bottom: 0, width: 'min(384px, 85vw)',
          background: 'var(--surface, #fff)', boxShadow: '-12px 0 40px rgba(0, 0, 0, 0.18)',
          display: 'flex', flexDirection: 'column' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '14px 16px',
          borderBottom: '1px solid var(--border)' }}>
          <h3 id="pesticide-lookup-drawer-title" style={{ margin: 0, fontSize: 16, flex: 1 }}>Tra cứu thuốc BVTV</h3>
          <button type="button" className="btn ghost" onClick={onClose} title="Đóng" aria-label="Đóng">
            <i className="ti ti-x" />
          </button>
        </div>
        {/* Thẻ tra cứu dùng lại nguyên khối của cột bên phải; bỏ viền / bóng thẻ cho liền ngăn kéo. */}
        <div style={{ flex: 1, overflowY: 'auto' }}>
          <CustomsPesticideLookup currentPestGroup={currentPestGroup} bare />
        </div>
      </div>
    </div>,
    document.body,
  )
}
