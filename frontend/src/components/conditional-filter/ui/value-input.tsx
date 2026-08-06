import Select from 'react-select'
import DateInput from '../../DateInput'
import NumberInput from '../../NumberInput'
import SearchSelect from '../../SearchSelect'
import { BOOLEAN_OPTIONS, VALUELESS_OPERATORS } from '../constants'
import { useFilterContext } from '../provider/filter-context'
import type { FilterRow, SelectOption } from '../types'

/** Ô nhập giá trị — đổi theo (kiểu field × operator). Dùng lại đúng các input sẵn có của app
 *  (DateInput dd/mm/yyyy, NumberInput định dạng VN, SearchSelect) nên nhìn không lệch phần còn lại. */
export default function ValueInput({ row }: { row: FilterRow }) {
  const { updateValue, optionsOf } = useFilterContext()
  const { field, operator } = row
  if (!field || !operator) return <div className="cf-value cf-value-empty">—</div>
  if (VALUELESS_OPERATORS.includes(operator)) return <div className="cf-value cf-value-empty" />

  const set = (v: any) => updateValue(row.id, v)
  const pair = Array.isArray(row.value) ? row.value : ['', '']
  const single = Array.isArray(row.value) ? '' : (row.value || '')
  const options = optionsOf(field)

  // ── Trong khoảng: 2 ô từ / đến ────────────────────────────────────────────────
  if (operator === 'between') {
    const setPair = (i: 0 | 1, v: string) => set(i === 0 ? [v, pair[1] || ''] : [pair[0] || '', v])
    return (
      <div className="cf-value cf-value-pair">
        {field.type === 'date' ? (
          <>
            <DateInput value={pair[0] || ''} onChange={(v) => setPair(0, v)} placeholder="Từ ngày" />
            <span className="cf-dash">→</span>
            <DateInput value={pair[1] || ''} onChange={(v) => setPair(1, v)} placeholder="Đến ngày" />
          </>
        ) : (
          <>
            <NumberInput value={Number(pair[0]) || 0} onChange={(n) => setPair(0, n ? String(n) : '')} placeholder="Từ" />
            <span className="cf-dash">→</span>
            <NumberInput value={Number(pair[1]) || 0} onChange={(n) => setPair(1, n ? String(n) : '')} placeholder="Đến" />
          </>
        )}
      </div>
    )
  }

  // ── Thuộc / không thuộc danh sách: chọn nhiều ────────────────────────────────
  if (operator === 'in' || operator === 'not_in') {
    const selected = (Array.isArray(row.value) ? row.value : []).map(
      (v) => options.find((o) => o.value === v) || { value: v, label: v },
    )
    return (
      <div className="cf-value">
        <Select
          isMulti classNamePrefix="rs" options={options} value={selected}
          placeholder="Chọn một hoặc nhiều…" noOptionsMessage={() => 'Không có'}
          menuPortalTarget={typeof document !== 'undefined' ? document.body : null}
          onChange={(opts: any) => set((opts || []).map((o: SelectOption) => o.value))}
          styles={{ menuPortal: (b) => ({ ...b, zIndex: 9999 }), control: (b) => ({ ...b, minHeight: 38, borderRadius: 10 }) }}
        />
      </div>
    )
  }

  // ── Một giá trị ──────────────────────────────────────────────────────────────
  if (field.type === 'boolean') {
    return (
      <div className="cf-value">
        <SearchSelect value={single as string} options={BOOLEAN_OPTIONS} placeholder="Chọn…" onChange={set} />
      </div>
    )
  }
  if (field.type === 'date') {
    return <div className="cf-value"><DateInput value={single as string} onChange={set} placeholder="dd/mm/yyyy" /></div>
  }
  if (field.type === 'number') {
    return (
      <div className="cf-value">
        <NumberInput value={Number(single) || 0} onChange={(n) => set(n ? String(n) : '')} placeholder="Nhập số…" />
      </div>
    )
  }
  // select/multiselect dùng "bằng/khác" vẫn là chọn 1 giá trị
  if ((field.type === 'select' || field.type === 'multiselect') && options.length > 0) {
    return (
      <div className="cf-value">
        <SearchSelect value={single as string} options={options} placeholder="Chọn…" onChange={set} />
      </div>
    )
  }
  return (
    <div className="cf-value">
      <input value={single as string} placeholder={`Nhập ${field.label.toLowerCase()}…`}
        onChange={(e) => set(e.target.value)} />
    </div>
  )
}
