import { useRef } from 'react'
import AsyncSelect from 'react-select/async'
import { api } from '../api/client'

// Ô chọn sản phẩm có tìm kiếm (gõ mã hoặc tên → LIKE trên server). Dùng cho DS cả ngàn SP.
export default function ProductPicker({ code, name, disabled, onPick }: { code?: string; name?: string; disabled?: boolean; onPick: (prod: any) => void }) {
  const t = useRef<any>(null)
  const loadOptions = (input: string) =>
    new Promise<any[]>((resolve) => {
      clearTimeout(t.current)
      t.current = setTimeout(async () => {
        try {
          const r = await api.get('/api/products', { params: { search: input, page_size: 30 } })
          resolve((r.data.data.items || []).map((p: any) => ({ value: p.code, label: `${p.code} — ${p.name}`, prod: p })))
        } catch { resolve([]) }
      }, 250)
    })
  const cur = code ? { value: code, label: name ? `${code} — ${name}` : code } : null
  return (
    <AsyncSelect
      value={cur} isDisabled={disabled} isClearable cacheOptions defaultOptions
      loadOptions={loadOptions} placeholder="Gõ mã/tên để tìm..."
      noOptionsMessage={({ inputValue }) => (inputValue ? 'Không tìm thấy' : 'Gõ để tìm sản phẩm')}
      loadingMessage={() => 'Đang tìm...'}
      onChange={(o: any) => onPick(o?.prod || null)}
      menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
      styles={{
        control: (b) => ({ ...b, minHeight: 36, borderRadius: 8, borderColor: '#E9EDF7', fontSize: 13 }),
        menuPortal: (b) => ({ ...b, zIndex: 9999 }),
      }}
    />
  )
}
