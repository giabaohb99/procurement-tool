import { useEffect, useRef } from 'react'

interface ConfirmModalProps {
  open: boolean
  title?: string
  message: string
  confirmText?: string
  cancelText?: string
  hideCancel?: boolean
  variant?: 'danger' | 'warn' | 'info'
  onConfirm: () => void
  onCancel: () => void
}

export default function ConfirmModal({
  open, title, message, confirmText = 'Xác nhận', cancelText = 'Hủy',
  hideCancel = false, variant = 'danger', onConfirm, onCancel,
}: ConfirmModalProps) {
  const confirmRef = useRef<HTMLButtonElement>(null)

  useEffect(() => {
    if (open) {
      confirmRef.current?.focus()
      document.body.style.overflow = 'hidden'
    } else {
      document.body.style.overflow = ''
    }
    return () => { document.body.style.overflow = '' }
  }, [open])

  useEffect(() => {
    if (!open) return
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onCancel()
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onCancel])

  if (!open) return null

  const iconMap = {
    danger: 'ti ti-alert-triangle',
    warn: 'ti ti-alert-circle',
    info: 'ti ti-info-circle',
  }
  const colorMap = {
    danger: { icon: '#ef4444', btn: '#ef4444', btnHover: '#dc2626' },
    warn: { icon: '#f59e0b', btn: '#f59e0b', btnHover: '#d97706' },
    info: { icon: '#3b82f6', btn: '#3b82f6', btnHover: '#2563eb' },
  }
  const colors = colorMap[variant]

  return (
    <div className="confirm-modal-overlay">
      <div className="confirm-modal" onClick={(e) => e.stopPropagation()}>
        <div className="confirm-modal-icon" style={{ color: colors.icon }}>
          <i className={iconMap[variant]} />
        </div>
        {title && <h3 className="confirm-modal-title">{title}</h3>}
        <p className="confirm-modal-message">{message}</p>
        <div className="confirm-modal-actions">
          {!hideCancel && (
            <button className="btn secondary" style={{ color: 'var(--muted)', borderColor: '#e2e8f0' }} onClick={onCancel}>
              {cancelText}
            </button>
          )}
          <button
            ref={confirmRef}
            className="btn"
            style={{ background: colors.btn, borderColor: colors.btn, color: '#fff' }}
            onMouseEnter={(e) => (e.currentTarget.style.background = colors.btnHover)}
            onMouseLeave={(e) => (e.currentTarget.style.background = colors.btn)}
            onClick={onConfirm}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}
