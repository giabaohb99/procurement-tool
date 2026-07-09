import { useEffect, useState } from 'react'

// Hộp thoại xác nhận / nhập lý do dùng chung (singleton, promise-based) — thay confirm()/prompt() trình duyệt.
type Req = {
  id: number
  title: string
  message: string
  confirmText: string
  cancelText: string
  danger: boolean
  withInput: boolean
  inputLabel: string
  placeholder: string
  defaultValue: string
  required: boolean
  resolve: (v: boolean | string) => void
}

let current: Req | null = null
let seq = 1
const listeners = new Set<(x: Req | null) => void>()
const emit = () => listeners.forEach((l) => l(current))

/** Xác nhận Yes/No → Promise<boolean>. */
export function askConfirm(opts: {
  title?: string; message: string; confirmText?: string; cancelText?: string; danger?: boolean
}): Promise<boolean> {
  return new Promise((resolve) => {
    current = {
      id: seq++, title: opts.title || 'Xác nhận', message: opts.message,
      confirmText: opts.confirmText || 'Đồng ý', cancelText: opts.cancelText || 'Hủy',
      danger: opts.danger ?? true, withInput: false, inputLabel: '', placeholder: '',
      defaultValue: '', required: false, resolve: (v) => resolve(v === true),
    }
    emit()
  })
}

/** Nhập 1 dòng (vd lý do) → Promise<string|null> (null = bấm Hủy). */
export function askPrompt(opts: {
  title?: string; message: string; inputLabel?: string; placeholder?: string
  defaultValue?: string; confirmText?: string; danger?: boolean; required?: boolean
}): Promise<string | null> {
  return new Promise((resolve) => {
    current = {
      id: seq++, title: opts.title || 'Nhập thông tin', message: opts.message,
      confirmText: opts.confirmText || 'Xác nhận', cancelText: 'Hủy',
      danger: opts.danger ?? false, withInput: true, inputLabel: opts.inputLabel || '',
      placeholder: opts.placeholder || '', defaultValue: opts.defaultValue || '',
      required: opts.required ?? false, resolve: (v) => resolve(v === false ? null : (v as string)),
    }
    emit()
  })
}

export function ConfirmHost() {
  const [req, setReq] = useState<Req | null>(null)
  const [val, setVal] = useState('')
  useEffect(() => { listeners.add(setReq); return () => { listeners.delete(setReq) } }, [])
  useEffect(() => { if (req) setVal(req.defaultValue) }, [req?.id])
  if (!req) return null

  const close = (result: boolean | string) => { const r = req.resolve; current = null; emit(); r(result) }
  const onOk = () => {
    if (req.withInput) { if (req.required && !val.trim()) return; close(val) }
    else close(true)
  }

  return (
    <div onClick={() => close(false)} style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 5000, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 16 }}>
      <div onClick={(e) => e.stopPropagation()} style={{ background: '#fff', borderRadius: 16, width: 430, maxWidth: '100%', boxShadow: '0 20px 60px rgba(15,23,42,.35)', overflow: 'hidden', animation: 'confIn .16s ease' }}>
        <div style={{ padding: '20px 22px 0' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 10 }}>
            <span style={{ width: 38, height: 38, borderRadius: 11, display: 'grid', placeItems: 'center', background: req.danger ? '#fef2f2' : '#eff6ff', color: req.danger ? '#dc2626' : '#2563eb', flexShrink: 0 }}>
              <i className={'ti ' + (req.danger ? 'ti-alert-triangle' : 'ti-help-circle')} style={{ fontSize: 21 }} />
            </span>
            <h3 style={{ margin: 0, fontSize: 16.5, color: '#0f172a', fontWeight: 700 }}>{req.title}</h3>
          </div>
          <div style={{ fontSize: 14, color: '#475569', lineHeight: 1.55, whiteSpace: 'pre-line' }}>{req.message}</div>
          {req.withInput && (
            <div style={{ marginTop: 14 }}>
              {req.inputLabel && <label style={{ fontSize: 12.5, color: '#64748b', display: 'block', marginBottom: 5 }}>{req.inputLabel}</label>}
              <input autoFocus value={val} placeholder={req.placeholder} onChange={(e) => setVal(e.target.value)}
                onKeyDown={(e) => { if (e.key === 'Enter') onOk(); if (e.key === 'Escape') close(false) }}
                style={{ width: '100%', padding: '10px 12px', border: '1px solid #e2e8f0', borderRadius: 10, fontSize: 14, outline: 'none', boxSizing: 'border-box' }} />
            </div>
          )}
        </div>
        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 10, padding: '18px 22px 20px' }}>
          <button onClick={() => close(false)} style={{ padding: '9px 17px', borderRadius: 10, border: '1px solid #e2e8f0', background: '#fff', color: '#475569', fontSize: 13.5, cursor: 'pointer', fontWeight: 500 }}>{req.cancelText}</button>
          <button onClick={onOk} style={{ padding: '9px 19px', borderRadius: 10, border: 'none', background: req.danger ? '#dc2626' : '#2563eb', color: '#fff', fontSize: 13.5, cursor: 'pointer', fontWeight: 600 }}>{req.confirmText}</button>
        </div>
      </div>
      <style>{`@keyframes confIn{from{opacity:0;transform:translateY(8px) scale(.98)}to{opacity:1;transform:none}}`}</style>
    </div>
  )
}
