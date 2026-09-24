// bao-CR-470 — khung hộp thoại của màn Tra cứu giá hải quan (cùng kiểu lớp phủ inline của
// các màn bản cũ, vd Inventory.tsx). Bấm nền hoặc Esc để đóng.
import { ReactNode, useEffect, useRef } from 'react'

// Chồng hộp đang mở — Esc chỉ đóng hộp TRÊN CÙNG (hộp nhật ký lô mở trong hộp lịch sử nạp).
const openStack: object[] = []

export default function CustomsModal({ title, width = 720, onClose, children, footer }: {
  title: ReactNode
  width?: number
  onClose: () => void
  children: ReactNode
  footer?: ReactNode
}) {
  const token = useRef({})
  useEffect(() => {
    const me = token.current
    openStack.push(me)
    return () => { openStack.splice(openStack.indexOf(me), 1) }
  }, [])
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && openStack[openStack.length - 1] === token.current) onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])
  return (
    <div onClick={onClose} style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 100,
      display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
      <div className="modal-card" onClick={(e) => e.stopPropagation()} style={{ width, maxWidth: '100%', maxHeight: '90vh',
        background: '#fff', borderRadius: 12, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ display: 'flex', alignItems: 'center', padding: '14px 20px', borderBottom: '1px solid #e5e7eb' }}>
          <h3 style={{ margin: 0, color: 'var(--navy)', flex: 1, fontSize: 16 }}>{title}</h3>
          <button className="btn ghost" onClick={onClose} title="Đóng"><i className="ti ti-x" /></button>
        </div>
        <div style={{ padding: 20, overflowY: 'auto', flex: 1 }}>{children}</div>
        {footer && (
          <div style={{ display: 'flex', gap: 8, justifyContent: 'flex-end', padding: '12px 20px', borderTop: '1px solid #e5e7eb' }}>
            {footer}
          </div>
        )}
      </div>
    </div>
  )
}
