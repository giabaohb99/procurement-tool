import type { PeopleFieldKind } from '../components/employee-people-editor'
import { EMPLOYEE_GENDER_OPTIONS } from '../types/employee'
import { RELATION_OPTIONS, codeLabel } from '../types/employee-codes'
import { formatDate } from '@/shared/utils/format-date'

/**
 * Một ô của bảng NGƯỜI (người báo tin / hộ gia đình) → chữ để HIỂN THỊ hoặc IN.
 *
 * Dùng ở bản in phiếu thông tin và bảng so sánh hộ gia đình của màn duyệt (duoc-CR-676). Mã `0`
 * (chưa khai) và `null` đều ra chuỗi RỖNG — in ra giấy là ô trống để điền tay, không phải chữ
 * «Chưa khai» hay «null».
 */
export function formatPeopleCell(kind: PeopleFieldKind, value: unknown): string {
  if (value === null || value === undefined) return ''
  switch (kind) {
    case 'relation':
      return Number(value) ? codeLabel(RELATION_OPTIONS, Number(value)) : ''
    case 'gender':
      return Number(value) ? codeLabel(EMPLOYEE_GENDER_OPTIONS, Number(value)) : ''
    case 'date':
      return typeof value === 'string' && value ? formatDate(value) : ''
    default:
      return String(value)
  }
}
