import { useEffect } from 'react'
import Select, { components as RS } from 'react-select'

type Opt = { value: string; label: string }

// Tắt gợi ý autofill/sọc của trình duyệt khi gõ trong ô select
const NoAutofillInput = (props: any) => <RS.Input {...props} autoComplete="off" spellCheck={false} aria-autocomplete="none" />

const rsComponents = (table: boolean) =>
  table ? { Input: NoAutofillInput, IndicatorSeparator: () => null } : { Input: NoAutofillInput }

/** Select có tìm kiếm (gõ để lọc). Danh sách ngắn/dài đều dùng được.
 *  - Chỉ 1 lựa chọn duy nhất → tự gán.
 *  - Trống → để rỗng (không hiện "—").
 *  - variant="table": gọn cho ô trong bảng (không nút X, viền trong suốt khi rảnh, gõ là sổ).
 *  - colorMap: {giá trị → mã màu} → hiển thị như badge có màu (dùng cho cột trạng thái).
 *  options nhận string[] hoặc {value,label}[].
 */
export default function SearchSelect({
  value, options, onChange, disabled, placeholder = '', width, variant = 'form', colorMap,
}: {
  value?: string
  options: (string | Opt)[]
  onChange: (v: string) => void
  disabled?: boolean
  placeholder?: string
  width?: number | string
  variant?: 'form' | 'table'
  colorMap?: Record<string, string>
}) {
  const opts: Opt[] = options.map((o) => (typeof o === 'string' ? { value: o, label: o } : o))
  const table = variant === 'table'
  const color = colorMap && value ? colorMap[value] : undefined

  // Chỉ có đúng 1 lựa chọn và chưa chọn gì → tự gán luôn
  useEffect(() => {
    if (!disabled && !value && opts.length === 1) onChange(opts[0].value)
  }, [opts.length, value, disabled])

  const cur = opts.find((o) => o.value === value) || null
  return (
    <Select
      value={cur} options={opts} isDisabled={disabled} isClearable={!table}
      placeholder={placeholder}
      onChange={(o: any) => onChange(o ? o.value : '')}
      noOptionsMessage={() => 'Không có'}
      menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
      components={rsComponents(table)}
      styles={{
        container: (b) => ({ ...b, width: width ?? '100%' }),
        control: (b, state: any) => table ? ({
          ...b, minHeight: 30, borderRadius: color ? 999 : 8, fontSize: 12.5, boxShadow: 'none', cursor: 'pointer',
          backgroundColor: color ? `${color}1a` : (state.isFocused ? '#fff' : 'transparent'),
          border: color ? `1px solid ${color}` : (state.isFocused ? '1px solid #cbd5e1' : '1px solid transparent'),
          ':hover': { border: color ? `1px solid ${color}` : '1px solid #cbd5e1' },
        }) : ({ ...b, minHeight: 40, borderRadius: 12, borderColor: '#E9EDF7', fontSize: 14 }),
        valueContainer: (b) => table ? ({ ...b, padding: '0 6px' }) : b,
        singleValue: (b) => color ? ({ ...b, color, fontWeight: 600 }) : b,
        input: (b) => table ? ({ ...b, margin: 0, padding: 0 }) : b,
        dropdownIndicator: (b) => table ? ({ ...b, padding: 2, color: color || '#94a3b8' }) : b,
        menu: (b) => ({ ...b, fontSize: table ? 12.5 : 14, minWidth: 160 }),
        menuPortal: (b) => ({ ...b, zIndex: 9999 }),
        option: (b, state: any) => ({
          ...b, cursor: 'pointer', color: '#1e293b',
          backgroundColor: state.isSelected ? '#e0f2fe' : state.isFocused ? '#f1f5f9' : '#fff',
        }),
      }}
    />
  )
}
