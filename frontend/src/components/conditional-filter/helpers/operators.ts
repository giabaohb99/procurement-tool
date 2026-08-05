import type { OperatorType } from '../types'

// Ánh xạ operator ↔ hậu tố query param (`<field>__<suffix>=<value>`).
//
// KHÁC bản FilterCN gốc: FilterCN map operator "bằng" thành param KHÔNG hậu tố (`status=abc`).
// Ở dự án này param trần đã mang nghĩa LIKE %abc% (apply_filters cũ) nên "bằng" dùng `__eq`
// để hai loại param không giẫm chân nhau. Xem app/core/filter_operators.py.

/** Operator → hậu tố param. is_empty/is_not_empty cùng dồn về `__isnull`, khác nhau ở giá trị. */
export function operatorSuffix(op: OperatorType): string {
  if (op === 'is_empty' || op === 'is_not_empty') return 'isnull'
  return op
}

/** Giá trị param cho các operator kiểm tra rỗng */
export function isnullValue(op: OperatorType): string {
  return op === 'is_empty' ? 'true' : 'false'
}

/** Hậu tố param → operator (dùng khi đọc ngược từ URL). `isnull` cần thêm giá trị để phân biệt. */
export function operatorFromSuffix(suffix: string, rawValue: string): OperatorType | null {
  if (suffix === 'isnull') return rawValue === 'true' ? 'is_empty' : 'is_not_empty'
  const known: OperatorType[] = [
    'eq', 'ne', 'contains', 'not_contains',
    'gt', 'gte', 'lt', 'lte', 'between', 'in', 'not_in',
  ]
  return known.includes(suffix as OperatorType) ? (suffix as OperatorType) : null
}

/** Tên param đầy đủ của 1 dòng lọc — cũng dùng để biết param nào do bộ lọc quản lý */
export function paramKey(fieldName: string, op: OperatorType): string {
  return `${fieldName}__${operatorSuffix(op)}`
}
