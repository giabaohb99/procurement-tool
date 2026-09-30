import {
  describeRow,
  isValueFreeOp,
  toArray,
  type ConditionField,
  type ConditionRow,
} from './condition-rule'

/** Ghép các dòng thành một câu, nối bằng "và" — đúng cách backend đọc chúng. */
export function conditionText<F extends ConditionField>(
  rows: ConditionRow[],
  fields: F[],
  //  `id` nhận cả chuỗi vì nơi gọi có thể đưa thẳng `MultiPickerOption[]` sang,
  //  mà ô chọn nhiều cho phép khóa dạng chuỗi (mục là một CẶP). Ở đây chỉ so
  //  sánh và đổi ra nhãn nên rộng hơn không hại gì.
  getOptions: (field: F) => { id: number | string; label: string }[],
): string {
  return rows
    .map((row) => {
      const field = fields.find((item) => item.name === row.field)
      if (!field) return ''
      return describeRow(row.op, field.label, valueText(row, field, getOptions) || '…')
    })
    .filter(Boolean)
    .join(' và ')
}

function valueText<F extends ConditionField>(
  row: ConditionRow,
  field: F,
  getOptions: (field: F) => { id: number | string; label: string }[],
): string {
  if (isValueFreeOp(row.op)) return ''
  if (field.kind === 'bool') return typeof row.value === 'boolean' ? (row.value ? 'Có' : 'Không') : ''
  if (field.kind === 'number') return typeof row.value === 'number' ? String(row.value) : ''

  const options = getOptions(field)
  const nhan = (id: number) => options.find((item) => item.id === id)?.label ?? String(id)
  return toArray(row.value)
    .filter((id) => id > 0)
    .map(nhan)
    .join(', ')
}
