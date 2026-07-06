import { useEffect, useState } from 'react'

// Toast toàn cục dạng singleton (import ở đâu cũng gọi được, không cần context)
type ToastType = 'error' | 'success' | 'info'
type ToastItem = { id: number; type: ToastType; msg: string }

let items: ToastItem[] = []
let seq = 1
const listeners = new Set<(x: ToastItem[]) => void>()
const emit = () => listeners.forEach((l) => l([...items]))

function push(type: ToastType, msg: string) {
  if (!msg) return
  const id = seq++
  items = [...items, { id, type, msg }]
  emit()
  setTimeout(() => { items = items.filter((t) => t.id !== id); emit() }, type === 'error' ? 6000 : 3500)
}
function dismiss(id: number) { items = items.filter((t) => t.id !== id); emit() }

export const toast = {
  error: (m: string) => push('error', m),
  success: (m: string) => push('success', m),
  info: (m: string) => push('info', m),
}

const STYLE: Record<ToastType, { bg: string; bd: string; fg: string; icon: string }> = {
  error:   { bg: '#fef2f2', bd: '#fecaca', fg: '#b91c1c', icon: 'ti-alert-circle' },
  success: { bg: '#f0fdf4', bd: '#bbf7d0', fg: '#15803d', icon: 'ti-circle-check' },
  info:    { bg: '#eff6ff', bd: '#bfdbfe', fg: '#1d4ed8', icon: 'ti-info-circle' },
}

export function ToastHost() {
  const [list, setList] = useState<ToastItem[]>([])
  useEffect(() => { listeners.add(setList); return () => { listeners.delete(setList) } }, [])
  return (
    <div style={{ position: 'fixed', top: 16, right: 16, zIndex: 4000, display: 'flex', flexDirection: 'column', gap: 10, maxWidth: 380 }}>
      {list.map((t) => {
        const s = STYLE[t.type]
        return (
          <div key={t.id} onClick={() => dismiss(t.id)}
            style={{ background: s.bg, border: `1px solid ${s.bd}`, color: s.fg, borderRadius: 12,
              padding: '12px 14px', display: 'flex', alignItems: 'flex-start', gap: 10, cursor: 'pointer',
              boxShadow: '0 10px 30px rgba(27,37,89,.15)', fontSize: 13.5, lineHeight: 1.4, animation: 'toastIn .18s ease' }}>
            <i className={'ti ' + s.icon} style={{ fontSize: 18, marginTop: 1, flexShrink: 0 }} />
            <span style={{ flex: 1 }}>{t.msg}</span>
            <i className="ti ti-x" style={{ fontSize: 14, opacity: .6, flexShrink: 0 }} />
          </div>
        )
      })}
      <style>{`@keyframes toastIn{from{opacity:0;transform:translateX(20px)}to{opacity:1;transform:none}}`}</style>
    </div>
  )
}
