import { Input } from '@/shared/ui/input'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { useFilterContext } from '../provider/filter-context'
import type { FilterFieldDefinition, FilterValue, OperatorType } from '../types'
import { ComboboxValue } from './combobox-value'
import { MultiSelectValue } from './multi-select-value'

interface ValueInputProps {
  rowId: string
  field: FilterFieldDefinition
  operator: OperatorType
  value: FilterValue
}

/**
 * Ô nhập giá trị, hình dạng tùy theo (kiểu trường × operator).
 *
 * Khác FilterCN gốc: ngày dùng `<input type="date">` thay cho Calendar của
 * `react-day-picker` + `date-fns`. Backend lưu ngày dạng chuỗi `YYYY-MM-DD` —
 * đúng bằng giá trị mà input date trả ra, nên không cần tầng định dạng nào.
 */
export function ValueInput({ rowId, field, operator, value }: ValueInputProps) {
  const { updateValue } = useFilterContext()
  const change = (next: FilterValue) => updateValue(rowId, next)

  // "để trống" / "có giá trị" tự nó đã đủ nghĩa.
  if (operator === 'is_empty' || operator === 'is_not_empty') return null

  const isDate = field.type === 'date' || field.type === 'datetime'
  const inputType = isDate ? 'date' : field.type === 'number' ? 'number' : 'text'

  if (operator === 'between') {
    const [from = '', to = ''] = Array.isArray(value) ? value : []
    return (
      <div className="flex min-w-0 flex-1 items-center gap-2">
        <Input
          type={inputType}
          placeholder={isDate ? 'Từ ngày' : 'Nhỏ nhất'}
          value={String(from)}
          onChange={(e) => change([e.target.value, String(to)])}
        />
        <span className="text-muted-foreground">–</span>
        <Input
          type={inputType}
          placeholder={isDate ? 'Đến ngày' : 'Lớn nhất'}
          value={String(to)}
          onChange={(e) => change([String(from), e.target.value])}
        />
      </div>
    )
  }

  if (operator === 'in' || operator === 'not_in') {
    return (
      <MultiSelectValue
        options={field.options ?? []}
        selected={Array.isArray(value) ? value.map(String) : []}
        onChange={(values) => change(values)}
      />
    )
  }

  if (field.type === 'boolean') {
    return (
      <Select
        value={value === true ? 'true' : value === false ? 'false' : ''}
        onValueChange={(next) => change(next === 'true')}
      >
        <SelectTrigger className="min-w-32 flex-1">
          <SelectValue placeholder="Chọn…" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="true">Có</SelectItem>
          <SelectItem value="false">Không</SelectItem>
        </SelectContent>
      </Select>
    )
  }

  if (field.type === 'select' && field.options) {
    return (
      <Select value={String(value ?? '')} onValueChange={change}>
        <SelectTrigger className="min-w-32 flex-1">
          <SelectValue placeholder="Chọn giá trị…" />
        </SelectTrigger>
        <SelectContent>
          {field.options.map((option) => (
            <SelectItem key={option.value} value={option.value}>
              {option.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    )
  }

  if (field.type === 'combobox' && field.fetchOptions) {
    return <ComboboxValue field={field} value={String(value ?? '')} onChange={change} />
  }

  return (
    <Input
      type={inputType}
      placeholder="Nhập giá trị…"
      value={String(value ?? '')}
      onChange={(e) => change(e.target.value)}
      className="min-w-32 flex-1"
    />
  )
}
