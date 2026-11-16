import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import type { WorkRosterCell } from '../types/work-roster'
import { resolveAssignmentMode, type AssignmentMode } from './work-schedule-assignment-mode'

/**
 * Ai xếp ca được ô nào (duoc-CR-761) — luật HIỂN THỊ, khớp `shift_access.check_cells` của backend:
 *
 * - KHÔNG AI tự xếp ca cho chính mình, kể cả Nhân sự (đại ca chốt 16/11/2026).
 * - Ô đã có đơn nghỉ (chờ duyệt / đã duyệt) bị khóa: backend 409 — sửa / hủy đơn trước rồi mới xếp ca.
 * - Đường Nhân sự (`work_schedule.write|delete`): mọi người trong phạm vi, MỌI ngày.
 * - Đường Trưởng phòng (`work_schedule_personal.write|delete`, khi không có khóa Nhân sự ở hành động đó): chỉ ngày ≥
 *   hôm nay (giờ VN).
 *
 * Phạm vi phòng ban giao diện không biết chắc (kiêm nhiệm, ô "Phòng ban được xem") — backend chốt, sai thì người dùng
 * nhận danh sách ô bị từ chối. Ngày so bằng chuỗi `YYYY-MM-DD` (so chuỗi đúng thứ tự lịch).
 */

type CanFn = (entity: PermissionEntity, action: PermissionAction) => boolean

/** Vì sao ô này chỉ xem; `null` = sửa được. */
export type ShiftLockReason = 'no_permission' | 'self' | 'leave' | 'past' | null

export interface ShiftCellAccess {
  /** Đường ghi (`write`) của người xem cho ô này. */
  mode: AssignmentMode
  canWrite: boolean
  /** Gỡ ca về mẫu tuần (`delete`) — có khóa riêng, Nhân sự có thể có ghi mà không có xóa. */
  canDelete: boolean
  /**
   * Ngày đã qua HOẶC hôm nay (giờ VN) không "Về mẫu tuần" được — với MỌI người, kể cả Nhân sự (backend 422). Chỉ sửa
   * khung giờ. Độc lập với `canDelete` (quyền) để hộp xếp ca hiện nút tắt kèm lý do thay vì giấu.
   */
  resetBlocked: boolean
  lock: ShiftLockReason
}

/** Khớp câu 422 của backend khi gỡ ca ngày đã qua / hôm nay. */
export const RESET_PAST_HINT = 'Ngày đã qua (hoặc hôm nay) không về mẫu tuần được — sửa khung giờ thay vì xóa.'

export interface ShiftViewer {
  /** Hồ sơ nhân sự của người đang đăng nhập; trống = tài khoản chưa gắn hồ sơ (không thể là "chính mình"). */
  employeeId?: number | null
}

export const SHIFT_LOCK_HINT: Record<Exclude<ShiftLockReason, null>, string> = {
  no_permission: 'Bạn không có quyền xếp ca.',
  self: 'Bạn không tự xếp ca cho mình — nhờ người có quyền xếp giúp.',
  leave: 'Đã có đơn nghỉ — sửa đơn trước.',
  past: 'Ngày đã qua: Trưởng phòng chỉ xếp ca từ hôm nay trở đi.',
}

function isSelf(employeeId: number, viewer: ShiftViewer): boolean {
  const own = Number(viewer.employeeId ?? 0)
  return own > 0 && own === employeeId
}

/** Khóa của MỘT hành động cho ô (người × ngày). */
function lockFor(
  can: CanFn,
  action: 'write' | 'delete',
  employeeId: number,
  date: string,
  viewer: ShiftViewer,
  today: string,
  hasLeave: boolean,
): { mode: AssignmentMode; lock: ShiftLockReason } {
  const mode = resolveAssignmentMode(can, action)
  if (mode === 'none') return { mode, lock: 'no_permission' }
  if (isSelf(employeeId, viewer)) return { mode, lock: 'self' }
  if (hasLeave) return { mode, lock: 'leave' }
  if (mode === 'personal' && date < today) return { mode, lock: 'past' }
  return { mode, lock: null }
}

/** `hasLeave` = ô có đơn nghỉ chờ duyệt / đã duyệt (khối `leave` của ô lưới). */
export function resolveShiftCellAccess(
  can: CanFn,
  employeeId: number,
  date: string,
  viewer: ShiftViewer,
  today: string,
  hasLeave = false,
): ShiftCellAccess {
  const write = lockFor(can, 'write', employeeId, date, viewer, today, hasLeave)
  const remove = lockFor(can, 'delete', employeeId, date, viewer, today, hasLeave)
  return {
    mode: write.mode,
    canWrite: write.lock === null,
    canDelete: remove.lock === null,
    resetBlocked: date <= today,
    lock: write.lock,
  }
}

/**
 * Ô đang bị đơn nghỉ GIỮ NGÀY (chờ duyệt / đã duyệt): cờ `leave_hold` của backend (phủ cả ngày lễ, ngày nghỉ, theo giờ,
 * đơn người xem không đọc được) hoặc — với backend chưa có cờ — khối `leave` của ô. Thiếu cả hai = không giữ.
 */
export function isLeaveHeld(cell: Pick<WorkRosterCell, 'leave' | 'leave_hold'> | null | undefined): boolean {
  return Boolean(cell?.leave_hold || cell?.leave)
}

/** Người xem có đường xếp ca nào không — quyết định có bật hộp xếp ca / chọn dòng / nút Chép tuần trước. */
export function canArrangeShifts(can: CanFn): boolean {
  return resolveAssignmentMode(can, 'write') !== 'none'
}

/**
 * Nhân sự trên trang mà người xem có thể đưa vào một lượt ghi hàng loạt: bỏ chính mình (mọi đường — backend từ chối cả
 * lượt nếu có). Không lọc theo ngày — ngày do từng lượt tự lọc.
 */
export function pickArrangeableEmployeeIds(
  can: CanFn,
  employeeIds: readonly number[],
  viewer: ShiftViewer,
): number[] {
  const mode = resolveAssignmentMode(can, 'write')
  if (mode === 'none') return []
  return employeeIds.filter((id) => !isSelf(id, viewer))
}

/** Mã loại kiêm nhiệm "Phòng ban" (`ConcurrentKind.DEPARTMENT` — bộ mã `concurrent_kind`). */
const CONCURRENT_KIND_DEPARTMENT = 1

/**
 * Phòng của Trưởng phòng theo hồ sơ đăng nhập: phòng chính + phòng kiêm nhiệm loại Phòng ban có bật công tắc phạm vi
 * (cùng nguồn `dept_ids` backend dựng ở `get_perm_profile`). Gần đúng phạm vi khóa `work_schedule_personal` — backend
 * vẫn là nơi chốt.
 */
export function viewerDepartmentIds(
  user: { department_id?: number; concurrents?: { kind: number; department_id: number; counts_scope: boolean }[] } | null | undefined,
): number[] {
  const ids = [
    Number(user?.department_id ?? 0),
    ...(user?.concurrents ?? [])
      .filter((c) => c.kind === CONCURRENT_KIND_DEPARTMENT && c.counts_scope)
      .map((c) => Number(c.department_id)),
  ]
  return [...new Set(ids.filter((id) => id > 0))]
}

/**
 * Dòng mặc định của "Chép tuần trước" khi KHÔNG tick dòng nào: mọi dòng sửa được trên trang. Đường Trưởng phòng thu
 * hẹp về người thuộc phòng của mình (`departmentIds`) — trang có thể đang xem "Tất cả phòng ban", chép cho người phòng
 * khác chỉ ăn từ chối cả lượt.
 */
export function pickCopyWeekDefaultIds(
  can: CanFn,
  items: readonly { employee_id: number; department_id: number }[],
  viewer: ShiftViewer,
  departmentIds: readonly number[],
): number[] {
  const ids = new Set(pickArrangeableEmployeeIds(can, items.map((i) => i.employee_id), viewer))
  const personal = resolveAssignmentMode(can, 'write') === 'personal'
  const depts = new Set(departmentIds)
  return items
    .filter((i) => ids.has(i.employee_id) && (!personal || depts.has(i.department_id)))
    .map((i) => i.employee_id)
}

/** Ngày trong danh sách mà người xem ghi được (đường Trưởng phòng bỏ ngày đã qua). */
export function pickArrangeableDates(can: CanFn, dates: readonly string[], today: string): string[] {
  const mode = resolveAssignmentMode(can, 'write')
  if (mode === 'none') return []
  if (mode === 'hr') return [...dates]
  return dates.filter((d) => d >= today)
}
