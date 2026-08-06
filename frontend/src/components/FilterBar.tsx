import { useEffect, useRef, useState } from 'react'
import { api } from '../api/client'
import SearchSelect from './SearchSelect'
import DateRangePicker from './DateRangePicker'
import FilterPanel, { FilterItem } from './FilterPanel'

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
  extra?: React.ReactNode            // nút phụ bên phải (vd nút "Bộ lọc điều kiện")
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
  // daterange: 1 bộ chọn khoảng → set cùng lúc 2 param <key>_from / <key>_to
  function setRange(k: string, v: { from: string; to: string }) {
    setVals((s) => ({ ...s, [k + '_from']: v.from, [k + '_to']: v.to }))
  }
  function clear() { setVals({}) }

  function renderField(f: FilterField) {
    const opts = f.options || dyn[f.key]
    const isRange = f.type === 'daterange'
    return (
      <FilterItem key={f.key} label={f.label} width={isRange ? 260 : undefined}>
        {(f.type === 'select' || f.source) ? (
          <SearchSelect value={vals[f.key] || ''} options={opts || []} placeholder="Tất cả" onChange={(v) => set(f.key, v)} />
        ) : isRange ? (
          <DateRangePicker block
            value={{ from: vals[f.key + '_from'] || '', to: vals[f.key + '_to'] || '' }}
            onChange={(v) => setRange(f.key, v)} />
        ) : (
          <input placeholder={`Nhập ${f.label.toLowerCase()}…`} value={vals[f.key] || ''}
                 onChange={(e) => set(f.key, e.target.value)} />
        )}
      </FilterItem>
    )
  }

  return (
    <FilterPanel onClear={clear} canClear={Object.values(vals).some((v) => v)} extra={extra}>
      {fields.map(renderField)}
    </FilterPanel>
  )
}
