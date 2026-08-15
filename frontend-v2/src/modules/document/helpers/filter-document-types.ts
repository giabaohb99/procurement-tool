import { getValidFilterRows } from '@/shared/conditional-filter'
import type { FilterRow, FilterState } from '@/shared/conditional-filter/types'
import type { DocumentType } from '../types/document-type'

/**
 * Áp BỘ LỌC NÂNG CAO ngay tại trình duyệt.
 *
 * ⚠️ Chỉ tồn tại vì phân hệ Văn bản chưa có backend: bình thường `useFilterQuery`
 * dịch bộ lọc thành query param rồi backend lọc (`core/filter_operators.py`).
 * Khi có `/api/document-types` thì xóa file này và đổi sang `queryParams` như
 * các màn danh sách khác — đỡ phải duy trì hai cách hiểu operator.
 */
export function filterDocumentTypes(
  items: DocumentType[],
  state: FilterState,
): DocumentType[] {
  const rows = getValidFilterRows(state.rows)
  if (rows.length === 0) return items

  return items.filter((item) =>
    state.conjunction === 'or'
      ? rows.some((row) => matches(item, row))
      : rows.every((row) => matches(item, row)),
  )
}

function matches(item: DocumentType, row: FilterRow): boolean {
  const raw = item[row.field!.name as keyof DocumentType]

  if (typeof raw === 'boolean') {
    // Ô boolean của bộ lọc trả chuỗi 'true' / 'false'.
    return raw === (row.value === true || row.value === 'true')
  }

  const text = String(raw ?? '').toLowerCase()
  const value = typeof row.value === 'string' ? row.value.toLowerCase() : row.value

  switch (row.operator) {
    case 'is':
      return text === value
    case 'is_not':
      return text !== value
    case 'contains':
      return text.includes(String(value))
    case 'not_contains':
      return !text.includes(String(value))
    case 'in':
      return toLowerList(row.value).includes(text)
    case 'not_in':
      return !toLowerList(row.value).includes(text)
    case 'is_empty':
      return text === ''
    case 'is_not_empty':
      return text !== ''
    default:
      // Operator số / ngày: danh mục này không có trường nào như vậy.
      return true
  }
}

function toLowerList(value: FilterRow['value']): string[] {
  return Array.isArray(value) ? value.map((item) => String(item).toLowerCase()) : []
}
