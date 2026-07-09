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
      classNamePrefix="rs"
      value={cur} isDisabled={disabled} isClearable cacheOptions defaultOptions
      loadOptions={loadOptions} placeholder="Gõ mã/tên để tìm..."
      noOptionsMessage={({ inputValue }) => (inputValue ? 'Không tìm thấy' : 'Gõ để tìm sản phẩm')}
      loadingMessage={() => 'Đang tìm...'}
      onChange={(o: any) => onPick(o?.prod || null)}
      menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
      styles={{
        control: (b, state: any) => ({
          ...b,
          minHeight: 40,
          height: 40,
          borderRadius: 12,
          borderColor: state.isFocused ? 'var(--teal)' : '#E9EDF7',
          boxShadow: state.isFocused ? '0 0 0 3px rgba(0,174,239,.15)' : 'none',
          fontSize: 13.5,
          fontWeight: 500,
          backgroundColor: state.isDisabled ? '#f6f8fa' : '#fff',
          transition: 'border-color 0.2s, box-shadow 0.2s',
          ':hover': {
            borderColor: state.isFocused ? 'var(--teal)' : (state.isDisabled ? '#E9EDF7' : '#cbd5e1')
          }
        }),
        valueContainer: (b) => ({
          ...b,
          padding: '0 16px',
          height: 38,
        }),
        singleValue: (b, state: any) => ({
          ...b,
          margin: 0,
          color: state.isDisabled ? 'var(--ink)' : 'var(--navy)',
          position: 'absolute',
          top: '50%',
          transform: 'translateY(-50%)',
        }),
        input: (b) => ({ ...b, margin: 0, padding: 0 }),
        indicatorsContainer: (b) => ({ ...b, height: 38 }),
        dropdownIndicator: (b) => ({ ...b, color: '#94a3b8', padding: '0 8px' }),
        clearIndicator: (b) => ({ ...b, color: '#94a3b8', padding: '0 8px' }),
        menu: (b) => ({ ...b, fontSize: 14, minWidth: 160 }),
        menuPortal: (b) => ({ ...b, zIndex: 9999 }),
        option: (b, state: any) => ({
          ...b, cursor: 'pointer', color: '#1e293b',
          backgroundColor: state.isSelected ? '#e0f2fe' : state.isFocused ? '#f1f5f9' : '#fff',
        }),
      }}
    />
  )
}
