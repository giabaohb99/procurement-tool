import type { ConditionFieldDef } from '../config/condition-fields'
import { describeRow, toArray, type ConditionRow } from './node-condition'

/** Ghép các dòng thành một câu, nối bằng "và" — đúng cách backend đọc chúng. */
export function cauDieuKien(
  rows: ConditionRow[],
  fields: ConditionFieldDef[],
  layLuaChon: (field: ConditionFieldDef) => { id: number; label: string }[],
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

