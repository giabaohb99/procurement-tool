import { VALUELESS_OPERATORS } from '../constants'
import type { FilterRow } from '../types'

/** Dòng lọc đã đủ dữ liệu để gửi lên API chưa (thiếu field/operator/giá trị → bỏ qua) */
export function isValidFilterRow(row: FilterRow): boolean {
  if (!row.field || !row.operator) return false

  if (VALUELESS_OPERATORS.includes(row.operator)) return true

  if (row.operator === 'between') {
    // Cho phép hở 1 đầu (chỉ "từ" hoặc chỉ "đến"), nhưng phải có ít nhất 1 đầu
    if (!Array.isArray(row.value)) return false
    return row.value.some((v) => v !== null && v !== '')
  }

  if (row.operator === 'in' || row.operator === 'not_in') {
    return Array.isArray(row.value) && row.value.filter(Boolean).length > 0
  }

  if (Array.isArray(row.value)) return row.value.filter(Boolean).length > 0
  return row.value !== null && row.value !== ''
}

export function getValidFilterRows(rows: FilterRow[]): FilterRow[] {
  return rows.filter(isValidFilterRow)
}
