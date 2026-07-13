import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import SearchSelect from './SearchSelect'

export type FilterField = {
  key: string
  label: string
  type?: 'text' | 'select' | 'daterange'   // daterange -> gửi 2 param <key>_from / <key>_to
  options?: { value: string; label: string }[]
  // Nguồn option động từ API (vd suppliers, companies, item-groups...)
  source?: { url: string; value?: string; label?: string }
}

export default function FilterBar({
  fields, onApply, extra, initial,
}: {
  fields: FilterField[]
  onApply: (params: Record<string, string>) => void
  extra?: React.ReactNode
  initial?: Record<string, string>   // giá trị lọc khởi tạo (vd điền sẵn từ URL query)
}) {
  const [vals, setVals] = useState<Record<string, string>>(initial || {})
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
    <div className="card" style={{ padding: 18, marginBottom: 14 }}>
      <div className="toolbar" style={{ marginBottom: 0, alignItems: 'flex-end' }}>
        {fields.map((f) => {
          const opts = f.options || dyn[f.key]
          return (
            <div key={f.key} className="toolbar-filter-item"
                 style={f.type === 'daterange' ? { flex: '1 1 260px', maxWidth: 320 } : undefined}>
              <label style={{ fontSize: 13, fontWeight: 700, color: 'var(--navy)', display: 'block', marginBottom: 6 }}>
                {f.label}
              </label>
              {(f.type === 'select' || f.source) ? (
                <SearchSelect value={vals[f.key] || ''} options={opts || []} placeholder="Tất cả" onChange={(v) => set(f.key, v)} />
              ) : f.type === 'daterange' ? (
                <div style={{ display: 'flex', gap: 6, alignItems: 'center' }}>
                  <input type="date" value={vals[f.key + '_from'] || ''} onChange={(e) => set(f.key + '_from', e.target.value)} style={{ minWidth: 0, flex: 1 }} />
                  <span style={{ color: 'var(--muted)' }}>–</span>
                  <input type="date" value={vals[f.key + '_to'] || ''} onChange={(e) => set(f.key + '_to', e.target.value)} style={{ minWidth: 0, flex: 1 }} />
                </div>
              ) : (
                <input placeholder={`Nhập ${f.label.toLowerCase()}…`} value={vals[f.key] || ''}
                       onChange={(e) => set(f.key, e.target.value)} />
              )}
            </div>
          )
        })}
        {Object.values(vals).some((v) => v) && (
          <button className="btn ghost" onClick={clear} style={{ height: 40, borderRadius: 12 }}>
            Xóa lọc
          </button>
        )}
        <span style={{ flex: 1 }} />
        {extra}
      </div>
    </div>
  )
}
