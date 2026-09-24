import Select, { components as RS } from 'react-select'

type Opt = { value: string; label: string }

// Tắt gợi ý autofill/sọc của trình duyệt khi gõ trong ô select (giống SearchSelect)
const NoAutofillInput = (props: any) => <RS.Input {...props} autoComplete="off" spellCheck={false} aria-autocomplete="none" />

// Mỗi dòng trong danh sách là một ô TICK + nhãn. Ô tick chỉ để nhìn (readOnly) — bấm cả dòng
// là react-select tự đảo trạng thái chọn, không cần bắt sự kiện riêng trên ô tick.
const CheckOption = (props: any) => (
  <RS.Option {...props}>
    <span style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
      <input type="checkbox" checked={props.isSelected} readOnly tabIndex={-1}
        style={{ margin: 0, width: 15, height: 15, accentColor: 'var(--teal)', cursor: 'pointer', flex: '0 0 auto' }} />
      <span style={{ overflow: 'hidden', textOverflow: 'ellipsis' }}>{props.label}</span>
    </span>
  </RS.Option>
)

/** Ô chọn NHIỀU giá trị bằng ô tick, dùng cho BỘ LỌC (bao-CR-423).
 *
 *  Khác `SearchSelect` (một giá trị) ở ba chỗ:
 *  - Danh sách sổ ra là các dòng có ô tick; tick xong danh sách KHÔNG tự đóng, người dùng
 *    tick tiếp mấy dòng nữa rồi bấm ra ngoài;
 *  - Trong ô không bày từng "viên" (chip) — với ô lọc cao 40px thì chip tràn dòng ngay ở
 *    giá trị thứ hai. Thay vào đó ô ghi tóm tắt: một giá trị thì ghi nhãn, nhiều hơn thì
 *    ghi "<nhãn đầu> +n";
 *  - `value`/`onChange` là MẢNG chuỗi. Rỗng nghĩa là "Tất cả". Nút X xóa hết một lượt.
 *  Cố ý KHÔNG có luật "1 lựa chọn → tự gán" (bài học bao-CR-388: ở ô lọc rỗng là Tất cả).
 *  options nhận string[] hoặc {value,label}[].
 */
export default function MultiCheckSelect({
  value, options, onChange, disabled, placeholder = 'Tất cả', width,
}: {
  value: string[]
  options: (string | Opt)[]
  onChange: (v: string[]) => void
  disabled?: boolean
  placeholder?: string
  width?: number | string
}) {
  const opts: Opt[] = options.map((o) => (typeof o === 'string' ? { value: o, label: o } : o))
  const vals = (value || []).map(String)
  // Giá trị không có trong options (vd danh mục chưa tải xong) vẫn giữ, không để trắng.
  const selected: Opt[] = vals.map((v) => opts.find((o) => o.value === v) || { value: v, label: v })

  // Tóm tắt bày trong ô: react-select chỉ hiện Placeholder khi chưa gõ chữ, nên mượn
  // chỗ đó để ghi "đã chọn gì" thay vì bày chip.
  const summary = selected.length === 0 ? '' :
    selected.length === 1 ? selected[0].label : `${selected[0].label} +${selected.length - 1}`
  const title = selected.map((o) => o.label).join(', ')

  const SummaryPlaceholder = (props: any) => (
    <RS.Placeholder {...props}>
      {summary
        ? <span title={title} style={{ color: 'var(--navy)', fontWeight: 500 }}>{summary}</span>
        : props.children}
    </RS.Placeholder>
  )

  return (
    <Select
      classNamePrefix="rs"
      isMulti
      value={selected} options={opts} isDisabled={disabled} isClearable
      closeMenuOnSelect={false} blurInputOnSelect={false} hideSelectedOptions={false}
      controlShouldRenderValue={false}
      placeholder={placeholder}
      onChange={(arr: any) => onChange((arr || []).map((o: Opt) => o.value))}
      noOptionsMessage={() => 'Không có'}
      menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
      components={{ Input: NoAutofillInput, Option: CheckOption, Placeholder: SummaryPlaceholder }}
      styles={{
        container: (b) => ({ ...b, width: width ?? '100%' }),
        control: (b, state: any) => ({
          ...b,
          minHeight: 40,
          height: 40,
          boxSizing: 'border-box',
          borderRadius: 12,
          backgroundColor: '#fff',
          borderColor: state.isFocused ? 'var(--teal)' : '#E9EDF7',
          boxShadow: state.isFocused ? '0 0 0 3px rgba(0,174,239,.15)' : 'none',
          fontSize: 13.5,
          fontWeight: 500,
          color: 'var(--navy)',
          cursor: 'pointer',
          transition: 'border-color 0.2s, box-shadow 0.2s, background-color 0.2s',
          ':hover': { borderColor: state.isFocused ? 'var(--teal)' : '#cbd5e1' },
        }),
        valueContainer: (b) => ({ ...b, padding: '0 16px', flexWrap: 'nowrap', overflow: 'hidden' }),
        placeholder: (b) => ({ ...b, margin: 0, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '100%' }),
        input: (b) => ({ ...b, margin: 0, padding: 0 }),
        dropdownIndicator: (b) => ({ ...b, color: '#94a3b8', padding: '0 8px' }),
        clearIndicator: (b) => ({ ...b, color: '#94a3b8', padding: '0 8px' }),
        menu: (b) => ({ ...b, fontSize: 14, minWidth: 200 }),
        menuPortal: (b) => ({ ...b, zIndex: 9999 }),
        option: (b, state: any) => ({
          ...b,
          cursor: 'pointer',
          color: '#1e293b',
          fontWeight: state.isSelected ? 600 : 'normal',
          // Dòng đã tick không tô nền đậm như select một giá trị — ô tick đã nói rồi,
          // nền chỉ đổi khi rê chuột để còn thấy đang đứng ở dòng nào.
          backgroundColor: state.isFocused ? '#f1f5f9' : '#fff',
          ':active': { backgroundColor: '#e0f2fe' },
        }),
      }}
    />
  )
}
