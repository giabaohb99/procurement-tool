import type { ConditionFieldDef } from '../config/condition-fields'
import { describeRow, toArray, type ConditionRow } from './node-condition'

/** Ghép các dòng thành một câu, nối bằng "và" — đúng cách backend đọc chúng. */
export function cauDieuKien(
  rows: ConditionRow[],
  fields: ConditionFieldDef[],
  //  `id` nhận cả chuỗi vì nơi gọi đưa thẳng `MultiPickerOption[]` sang, mà ô
  //  chọn nhiều nay cho phép khóa dạng chuỗi (mục là một CẶP). Ở đây chỉ so
  //  sánh và đổi ra nhãn nên rộng hơn không hại gì.
  layLuaChon: (field: ConditionFieldDef) => { id: number | string; label: string }[],
): string {
  return rows
    .map((row) => {
      const field = fields.find((item) => item.name === row.field)
      if (!field) return ''
      const options = layLuaChon(field)
      const nhan = (id: number) => options.find((item) => item.id === id)?.label ?? String(id)
      const giaTri = toArray(row.value)
        .filter((id) => id > 0)
        .map(nhan)
        .join(', ')
      return describeRow(row.op, field.label, giaTri || '…')
    })
    .filter(Boolean)
    .join(' và ')
}

