import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'

export type FilterField = {
  key: string
  label: string
  type?: 'text' | 'select'
  options?: { value: string; label: string }[]
  // Nguồn option động từ API (vd suppliers, companies, item-groups...)
  source?: { url: string; value?: string; label?: string }
}

export default function FilterBar({
  fields, onApply, extra,
}: {
  fields: FilterField[]
  onApply: (params: Record<string, string>) => void
  extra?: React.ReactNode
}) {
  const [vals, setVals] = useState<Record<string, string>>({})
  const [dyn, setDyn] = useState<Record<string, { value: string; label: string }[]>>({})
  const onApplyRef = useRef(onApply)
  onApplyRef.current = onApply
  const first = useRef(true)

  useEffect(() => {
    fields.filter((f) => f.source).forEach((f) => {
      api.get(f.source!.url, { params: { page_size: 1000 } }).then((r) => {
        const vk = f.source!.value || 'code'
        const lk = f.source!.label || 'name'
        const opts = (r.data.data.items || []).map((it: any) => ({
          value: String(it[vk] ?? ''), label: String(it[lk] ?? it[vk] ?? ''),
        })).filter((o: any) => o.value)
        setDyn((s) => ({ ...s, [f.key]: opts }))
      }).catch(() => {})
    })
  }, [fields])

  // Tự lọc khi ngừng gõ / đổi lựa chọn (debounce 400ms) — không cần bấm nút
  useEffect(() => {
    if (first.current) { first.current = false; return }
    const t = setTimeout(() => {
      const params: Record<string, string> = {}
      Object.entries(vals).forEach(([k, v]) => { if (v) params[k] = v })
      onApplyRef.current(params)
    }, 400)
    return () => clearTimeout(t)
  }, [vals])

  function set(k: string, v: string) { setVals((s) => ({ ...s, [k]: v })) }
  function clear() { setVals({}) }

  return (
    <div className="toolbar">
      {fields.map((f) => {
        const opts = f.options || dyn[f.key]
        return (f.type === 'select' || f.source) ? (
          <select key={f.key} value={vals[f.key] || ''} onChange={(e) => set(f.key, e.target.value)}>
            <option value="">{f.label}: Tất cả</option>
            {(opts || []).map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        ) : (
          <input key={f.key} placeholder={f.label} value={vals[f.key] || ''}
                 onChange={(e) => set(f.key, e.target.value)} />
        )
      })}
      {Object.values(vals).some((v) => v) && <button className="btn ghost" onClick={clear}>Xóa lọc</button>}
      <span style={{ flex: 1 }} />
      {extra}
    </div>
  )
}
