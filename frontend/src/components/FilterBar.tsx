import { useState } from 'react'

export type FilterField = {
  key: string
  label: string
  type?: 'text' | 'select'
  options?: { value: string; label: string }[]
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

  function set(k: string, v: string) {
    setVals((s) => ({ ...s, [k]: v }))
  }
  function apply() {
    const params: Record<string, string> = {}
    Object.entries(vals).forEach(([k, v]) => { if (v) params[k] = v })
    onApply(params)
  }
  function clear() {
    setVals({})
    onApply({})
  }

  return (
    <div className="toolbar">
      {fields.map((f) =>
        f.type === 'select' ? (
          <select key={f.key} value={vals[f.key] || ''} onChange={(e) => set(f.key, e.target.value)}>
            <option value="">{f.label}: Tất cả</option>
            {f.options?.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        ) : (
          <input key={f.key} placeholder={f.label} value={vals[f.key] || ''}
                 onChange={(e) => set(f.key, e.target.value)} />
        )
      )}
      <button className="btn secondary" onClick={apply}><i className="ti ti-filter" />Lọc</button>
      <button className="btn ghost" onClick={clear}>Xóa lọc</button>
      <span style={{ flex: 1 }} />
      {extra}
    </div>
  )
}
