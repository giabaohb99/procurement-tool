import { useEffect, useState } from 'react'
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
  fields,
  onApply,
  extra,
}: {
  fields: FilterField[]
  onApply: (params: Record<string, string>) => void
  extra?: React.ReactNode
}) {
  const [vals, setVals] = useState<Record<string, string>>({})
  const [dyn, setDyn] = useState<Record<string, { value: string; label: string }[]>>({})

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

  function set(k: string, v: string) { setVals((s) => ({ ...s, [k]: v })) }
  function apply() {
    const params: Record<string, string> = {}
    Object.entries(vals).forEach(([k, v]) => { if (v) params[k] = v })
    onApply(params)
  }
  function clear() { setVals({}); onApply({}) }

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
      <button className="btn secondary" onClick={apply}><i className="ti ti-filter" />Lọc</button>
      <button className="btn ghost" onClick={clear}>Xóa lọc</button>
      <span style={{ flex: 1 }} />
      {extra}
    </div>
  )
}
