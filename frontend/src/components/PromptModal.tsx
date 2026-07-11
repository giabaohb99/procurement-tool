import { useEffect, useRef, useState } from 'react'

interface PromptModalProps {
  open: boolean
  title?: string
  message: string
  placeholder?: string
  confirmText?: string
  cancelText?: string
  variant?: 'danger' | 'warn' | 'info' | 'primary'
  onConfirm: (value: string) => void
  onCancel: () => void
}

export default function PromptModal({
  open, title, message, placeholder = 'Nhập lý do...', confirmText = 'Xác nhận', cancelText = 'Hủy',
  variant = 'danger', onConfirm, onCancel,
}: PromptModalProps) {
  const [value, setValue] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (open) {
      setValue('')
      setTimeout(() => inputRef.current?.focus(), 50)
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
      if (e.key === 'Enter') onConfirm(value)
    }
    window.addEventListener('keydown', handler)
    return () => window.removeEventListener('keydown', handler)
  }, [open, onCancel, onConfirm, value])

  if (!open) return null

  const iconMap = {
    danger: 'ti ti-alert-triangle',
    warn: 'ti ti-alert-circle',
    info: 'ti ti-info-circle',
    primary: 'ti ti-message',
  }
  const colorMap = {
    danger: { icon: '#ef4444', btn: '#ef4444', btnHover: '#dc2626' },
    warn: { icon: '#f59e0b', btn: '#f59e0b', btnHover: '#d97706' },
    info: { icon: '#3b82f6', btn: '#3b82f6', btnHover: '#2563eb' },
    primary: { icon: 'var(--primary)', btn: 'var(--primary)', btnHover: 'var(--primary-dark)' },
  }
  const colors = colorMap[variant]

  return (
    <div className="confirm-modal-overlay">
      <div className="confirm-modal" onClick={(e) => e.stopPropagation()}>
        <div className="confirm-modal-icon" style={{ color: colors.icon }}>
          <i className={iconMap[variant]} />
        </div>
        {title && <h3 className="confirm-modal-title">{title}</h3>}
        <p className="confirm-modal-message" style={{ marginBottom: 12 }}>{message}</p>
        <input 
          ref={inputRef}
          type="text" 
          className="form-control" 
          placeholder={placeholder}
          value={value}
          onChange={e => setValue(e.target.value)}
          style={{ width: '100%', marginBottom: 20 }}
        />
        <div className="confirm-modal-actions">
          <button className="btn secondary" style={{ color: 'var(--muted)', borderColor: '#e2e8f0' }} onClick={onCancel}>
            {cancelText}
          </button>
          <button
            className="btn"
            style={{ background: colors.btn, borderColor: colors.btn, color: '#fff' }}
            onMouseEnter={(e) => (e.currentTarget.style.background = colors.btnHover)}
            onMouseLeave={(e) => (e.currentTarget.style.background = colors.btn)}
            onClick={() => onConfirm(value)}
          >
            {confirmText}
          </button>
        </div>
      </div>
    </div>
  )
}
