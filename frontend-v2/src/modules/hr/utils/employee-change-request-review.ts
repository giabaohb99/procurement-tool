import { CHANGE_REQUEST_GROUP_LABELS } from '../config/employee-profile-fields'
import type {
  ChangeRequestFamilies,
  ChangeRequestGroup,
  ChangeRequestItem,
  EmployeeChangeRequest,
} from '../types/employee-change-request'
import { normalizeFamilies } from './employee-change-request-diff'
import { CHANGE_REQUEST_STATUS } from './employee-change-request-status'
import { extractErrorMessage } from '@/core/api/response-envelope'

/**
 * Luật hiển thị phía PHÒNG NHÂN SỰ của đề nghị sửa hồ sơ (duoc-CR-676) — hàm thuần để test.
 */

/** So hai giá trị kiểu «nhìn bằng mắt»: `null` / `''` coi như nhau, số và chữ số coi như nhau. */
function sameValue(a: unknown, b: unknown): boolean {
  return String(a ?? '') === String(b ?? '')
}

/**
 * Hồ sơ đã bị sửa SAU lúc nhân viên gửi (hiện tại ≠ lúc gửi). Ô bị che thì cả hai về `null` —
 * không so được, trả `false` chứ không đoán.
 */
export function isChangedSinceSubmit(item: ChangeRequestItem): boolean {
  if (item.masked) return false
  return !sameValue(item.current, item.before)
}

/**
 * Hộ gia đình trên hồ sơ đã đổi SAU lúc gửi (review M3). Bị che, hoặc backend chưa gửi `current`,
 * thì không so được → `false`. So sau khi chuẩn hóa (bỏ dòng trống tên, cắt khoảng trắng).
 */
export function isFamiliesChangedSinceSubmit(families: ChangeRequestFamilies | null): boolean {
  if (!families || families.masked || !families.current || !families.before) return false
  return (
    JSON.stringify(normalizeFamilies(families.current)) !==
    JSON.stringify(normalizeFamilies(families.before))
  )
}

/**
 * Câu báo khi Duyệt / Từ chối bị máy chủ từ chối. 409 = đề nghị đã được người khác xử lý, hoặc
 * hộ gia đình đã đổi sau lúc gửi — kèm hướng đi tiếp thay vì để người duyệt bấm lại mãi.
 */
export function describeDecisionError(error: unknown): string {
  const message = extractErrorMessage(error)
  const status = (error as { response?: { status?: number } } | null)?.response?.status
  if (status === 409) {
    return `${message.replace(/[.\s]+$/, '')}. Màn đã tải lại dữ liệu mới nhất — nếu hồ sơ đã đổi sau lúc gửi, hãy từ chối và nhờ nhân viên gửi lại đề nghị.`
  }
  return message
}

const GROUP_ORDER: readonly ChangeRequestGroup[] = ['personal', 'bank', 'documents']

/** Các nhóm có mặt trong đề nghị, đúng thứ tự tab — cột «Nhóm thay đổi» của danh sách. */
export function listChangedGroups(request: EmployeeChangeRequest): string[] {
  const present = new Set(request.items.map((item) => item.group))
  const labels = GROUP_ORDER.filter((group) => present.has(group)).map(
    (group) => CHANGE_REQUEST_GROUP_LABELS[group],
  )
  if (request.families) labels.push(CHANGE_REQUEST_GROUP_LABELS.families)
  return labels
}

/** Số «trường» đổi: mỗi ô phẳng là một, cả bảng hộ gia đình tính là một. */
export function countChangedFields(request: EmployeeChangeRequest): number {
  return request.items.length + (request.families ? 1 : 0)
}

/**
 * Câu giải thích vì sao người đang xem KHÔNG bấm được Duyệt / Từ chối một đề nghị đang chờ.
 * `can_decide` do backend tính; ở đây chỉ đoán LÝ DO để nói thành lời, theo đúng hai chốt backend
 * (không tự duyệt · ô nhạy cảm cần `employee_sensitive.read`). Không đoán ra thì nói chung chung.
 * Trả `''` khi bấm được hoặc đề nghị không còn chờ.
 */
export function describeWhyCannotDecide(
  request: EmployeeChangeRequest,
  viewer: { employeeId: number; canReadSensitive: boolean },
): string {
  if (request.status !== CHANGE_REQUEST_STATUS.PENDING || request.can_decide) return ''
  if (viewer.employeeId > 0 && viewer.employeeId === request.employee_id) {
    return 'Đây là đề nghị sửa hồ sơ của chính bạn — một người khác trong phòng Nhân sự phải duyệt.'
  }
  if (request.has_sensitive && !viewer.canReadSensitive) {
    return 'Đề nghị có ô thông tin nhạy cảm (CCCD, ngân hàng, ngày sinh…) — cần quyền xem thông tin nhạy cảm mới duyệt được.'
  }
  return 'Bạn không có quyền duyệt đề nghị này.'
}
