import type { FieldType, OperatorType } from './types'

/** Operator mặc định theo loại field (port từ FilterCN, cắt bớt cái không dùng ở dự án) */
export const DEFAULT_OPERATORS: Record<FieldType, OperatorType[]> = {
  text: ['contains', 'eq', 'ne', 'not_contains', 'is_empty', 'is_not_empty'],
  number: ['eq', 'ne', 'gt', 'gte', 'lt', 'lte', 'between', 'is_empty', 'is_not_empty'],
  select: ['eq', 'ne', 'in', 'not_in', 'is_empty', 'is_not_empty'],
  multiselect: ['in', 'not_in', 'is_empty', 'is_not_empty'],
  date: ['between', 'eq', 'gte', 'lte', 'gt', 'lt', 'is_empty', 'is_not_empty'],
  boolean: ['eq'],
}

export const OPERATOR_LABELS: Record<OperatorType, string> = {
  eq: 'bằng',
  ne: 'khác',
  contains: 'chứa',
  not_contains: 'không chứa',
  gt: 'lớn hơn',
  gte: 'lớn hơn hoặc bằng',
  lt: 'nhỏ hơn',
  lte: 'nhỏ hơn hoặc bằng',
  between: 'trong khoảng',
  in: 'thuộc danh sách',
  not_in: 'không thuộc',
  is_empty: 'đang trống',
  is_not_empty: 'có giá trị',
}

/** Với cột ngày, chữ "lớn hơn / nhỏ hơn" khó đọc → thay bằng ngôn ngữ ngày tháng */
const DATE_OPERATOR_LABELS: Partial<Record<OperatorType, string>> = {
  eq: 'đúng ngày',
  ne: 'khác ngày',
  gt: 'sau ngày',
  gte: 'từ ngày',
  lt: 'trước ngày',
  lte: 'đến ngày',
  between: 'trong khoảng',
}

export function operatorLabel(op: OperatorType, type?: FieldType): string {
  if (type === 'date' && DATE_OPERATOR_LABELS[op]) return DATE_OPERATOR_LABELS[op] as string
  return OPERATOR_LABELS[op] || op
}

/** Operator không cần ô nhập giá trị */
export const VALUELESS_OPERATORS: OperatorType[] = ['is_empty', 'is_not_empty']

export const BOOLEAN_OPTIONS = [
  { value: 'true', label: 'Có' },
  { value: 'false', label: 'Không' },
]

export const MAX_ROWS_DEFAULT = 8
