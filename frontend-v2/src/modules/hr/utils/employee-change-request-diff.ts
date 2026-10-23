import {
  CHANGE_REQUEST_GROUP_FIELDS,
  EMPLOYEE_FIELD_DEFS,
  type EmployeeFieldKey,
} from '../config/employee-profile-fields'
import { toFamilyPayload } from '../config/employee-family-columns'
import type { Employee, EmployeeFamily } from '../types/employee'
import type {
  ChangeRequestFamilyRow,
  ChangeRequestGroup,
  ChangeRequestPayload,
  ChangeRequestValue,
} from '../types/employee-change-request'

/**
 * Luật «CHỈ GỬI Ô ĐÃ ĐỔI» của hộp «Đề nghị sửa thông tin» (duoc-CR-676). Hàm thuần để test trực
 * tiếp, không phải dựng hộp thoại.
 *
 * Vì sao chỉ gửi ô đã đổi: phòng Nhân sự đọc đề nghị như một danh sách «ô nào từ gì sang gì».
 * Gửi cả nhóm thì mười ô không đổi cũng thành mười dòng so sánh, và ô thật sự đổi chìm giữa đám.
 */

/** Câu chặn khi không có gì đổi — trùng ĐÚNG câu 400 của backend để hai phía nói một giọng. */
export const NO_CHANGE_MESSAGE = 'Không có thay đổi nào để gửi'

export type ChangeRequestFieldValues = Record<EmployeeFieldKey, ChangeRequestValue>

export interface ChangeRequestDraft {
  values: Partial<ChangeRequestFieldValues>
  families: EmployeeFamily[]
  note: string
}

const GROUPS: readonly ChangeRequestGroup[] = ['personal', 'bank', 'documents']

/**
 * Đưa một giá trị về dạng so sánh được:
 * - chữ: cắt khoảng trắng hai đầu (gõ thừa dấu cách không phải là «sửa»);
 * - ngày: chuỗi `YYYY-MM-DD`, rỗng → `null` (backend chỉ nhận `null` cho ô ngày bỏ trống);
 * - số / mã: số nguyên, rỗng → `0`.
 */
export function normalizeFieldValue(field: EmployeeFieldKey, value: unknown): ChangeRequestValue {
  switch (EMPLOYEE_FIELD_DEFS[field].kind) {
    case 'date':
      return typeof value === 'string' && value.trim() ? value.trim().slice(0, 10) : null
    case 'number':
    case 'code': {
      const n = Number(value ?? 0)
      return Number.isFinite(n) ? Math.trunc(n) : 0
    }
    default:
      return String(value ?? '').trim()
  }
}

/** Mọi ô tự khai được, lấy từ hồ sơ hiện tại — làm mốc «trước khi sửa» và làm nháp ban đầu. */
export function readChangeRequestValues(employee: Employee): ChangeRequestFieldValues {
  const source = employee as unknown as Record<string, unknown>
  const out = {} as ChangeRequestFieldValues
  for (const group of GROUPS) {
    for (const field of CHANGE_REQUEST_GROUP_FIELDS[group]) {
      out[field] = normalizeFieldValue(field, source[field])
    }
  }
  return out
}

/**
 * Hộ gia đình ở dạng so sánh được: bỏ dòng TRỐNG HỌ TÊN (backend bỏ qua chúng — bảng luôn dựng
 * sẵn một dòng trống, thêm dòng trống không phải là «sửa»), cắt khoảng trắng các ô chữ.
 */
export function normalizeFamilies(rows: readonly ChangeRequestFamilyRow[]): ChangeRequestFamilyRow[] {
  return toFamilyPayload(rows)
    .map((row) => ({
      ...row,
      full_name: row.full_name.trim(),
      phone: (row.phone ?? '').trim(),
      id_number: (row.id_number ?? '').trim(),
      relation: Number(row.relation) || 0,
      gender: Number(row.gender) || 0,
      date_of_birth: row.date_of_birth ? row.date_of_birth.slice(0, 10) : null,
    }))
    .filter((row) => row.full_name !== '')
}

/**
 * Thân gửi đi, hoặc `null` khi KHÔNG có ô nào đổi (nơi gọi chặn bằng `NO_CHANGE_MESSAGE`).
 *
 * - Nhóm không có ô nào đổi thì KHÔNG có mặt trong thân.
 * - Hộ gia đình đổi bất kỳ chỗ nào thì gửi CẢ danh sách (backend thay thế toàn bộ).
 * - Chỉ gõ ghi chú mà không đổi ô nào vẫn là «không có thay đổi» — ghi chú không phải dữ liệu hồ sơ.
 */
export function buildChangeRequestPayload(
  baseline: ChangeRequestFieldValues,
  baselineFamilies: readonly EmployeeFamily[],
  draft: ChangeRequestDraft,
): ChangeRequestPayload | null {
  const payload: ChangeRequestPayload = {}
  let changed = false

  for (const group of GROUPS) {
    const diff: Record<string, ChangeRequestValue> = {}
    for (const field of CHANGE_REQUEST_GROUP_FIELDS[group]) {
      if (!(field in draft.values)) continue
      const next = normalizeFieldValue(field, draft.values[field])
      if (next !== baseline[field]) diff[field] = next
    }
    if (Object.keys(diff).length > 0) {
      payload[group] = diff
      changed = true
    }
  }

  const nextFamilies = normalizeFamilies(draft.families)
  if (JSON.stringify(nextFamilies) !== JSON.stringify(normalizeFamilies(baselineFamilies))) {
    payload.families = nextFamilies
    changed = true
  }

  if (!changed) return null
  const note = draft.note.trim()
  if (note) payload.note = note
  return payload
}
