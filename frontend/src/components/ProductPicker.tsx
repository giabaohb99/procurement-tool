import { useRef } from 'react'
import AsyncSelect from 'react-select/async'
import { api } from '../api/client'

// Ô chọn sản phẩm có tìm kiếm (gõ mã hoặc tên → LIKE trên server). Dùng cho DS cả ngàn SP.
// compact: chỉ hiện MÃ ở ô đã chọn (dùng trong bảng, nơi cột kế bên đã có tên hàng)
//          → mã hiện đủ, không bị cắt cụt bằng "…".
export default function ProductPicker({ code, name, disabled, compact, onPick }: { code?: string; name?: string; disabled?: boolean; compact?: boolean; onPick: (prod: any) => void }) {
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
  const cur = code ? { value: code, label: compact || !name ? code : `${code} — ${name}` } : null
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
          height: 'auto',   // cao theo nội dung: tên dài thì xuống dòng, không cắt cụt
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
          padding: compact ? '5px 8px' : '7px 14px',
          minHeight: 38,
        }),
        singleValue: (b, state: any) => ({
          ...b,
          margin: 0,
          color: state.isDisabled ? 'var(--ink)' : 'var(--navy)',
          position: 'static',
          transform: 'none',
          // compact (trong bảng): mã ngắn — giữ 1 dòng, KHÔNG ngắt chữ cho xấu
          whiteSpace: compact ? 'nowrap' : 'normal',
          overflowWrap: compact ? 'normal' : 'anywhere',
          lineHeight: 1.35,
        }),
        input: (b) => ({ ...b, margin: 0, padding: 0 }),
        indicatorsContainer: (b) => ({ ...b, alignSelf: 'stretch' }),
        dropdownIndicator: (b) => ({ ...b, color: '#94a3b8', padding: compact ? '0 4px' : '0 8px' }),
        clearIndicator: (b) => ({ ...b, color: '#94a3b8', padding: compact ? '0 4px' : '0 8px' }),
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
