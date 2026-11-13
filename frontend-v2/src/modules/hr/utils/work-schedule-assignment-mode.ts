import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import { WORK_SCHEDULE_LEVEL_CODE, type WorkScheduleAssignment } from '../types/work-schedule'

/**
 * Ai gán lịch theo đường nào (duoc-CR-757 lượt 2).
 *
 * - `hr`: có `work_schedule.<hành động>` — Nhân sự, làm được mọi cấp, mọi đối tượng như trước.
 * - `personal`: chỉ có `work_schedule_personal.<hành động>` — Trưởng phòng, chỉ gán lịch RIÊNG (cấp Nhân sự) cho nhân
 *   viên phòng mình, không cho chính mình, chỉ chọn mẫu HR tạo sẵn.
 * - `none`: không có khóa nào.
 *
 * Có cả hai khóa thì đi đường `hr` (rộng hơn). Đây chỉ là luật HIỂN THỊ — backend tự chốt cấp, phạm vi, chính mình và
 * mẫu đang dùng ở `assignment_controller`, giao diện đoán sai thì người dùng ăn 400 / 403 kèm câu báo.
 */
export type AssignmentMode = 'hr' | 'personal' | 'none'

/** Hành động ghi trên dòng gán lịch. */
export type AssignmentAction = Extract<PermissionAction, 'create' | 'write' | 'delete'>

type CanFn = (entity: PermissionEntity, action: PermissionAction) => boolean

export const HR_ASSIGNMENT_ENTITY: PermissionEntity = 'work_schedule'
export const PERSONAL_ASSIGNMENT_ENTITY: PermissionEntity = 'work_schedule_personal'

/** Đường gán lịch của người đang đăng nhập cho MỘT hành động. */
export function resolveAssignmentMode(can: CanFn, action: AssignmentAction): AssignmentMode {
  if (can(HR_ASSIGNMENT_ENTITY, action)) return 'hr'
  if (can(PERSONAL_ASSIGNMENT_ENTITY, action)) return 'personal'
  return 'none'
}

/** Khóa quyền ứng với một đường — dùng cho cổng `PermissionGate` của khung CRUD. */
export function entityForMode(mode: AssignmentMode): PermissionEntity {
  return mode === 'personal' ? PERSONAL_ASSIGNMENT_ENTITY : HR_ASSIGNMENT_ENTITY
}

/**
 * Dòng gán mà người đi đường `personal` được đụng tới: cấp Nhân sự và KHÔNG phải hồ sơ của chính họ.
 * Người không gắn hồ sơ nhân sự (`selfEmployeeId` trống) thì chỉ xét cấp.
 */
export function isPersonallyAssignable(
  row: Pick<WorkScheduleAssignment, 'target_level' | 'target_id'>,
  selfEmployeeId: number | null | undefined,
): boolean {
  if (Number(row.target_level) !== WORK_SCHEDULE_LEVEL_CODE.EMPLOYEE) return false
  const targetId = Number(row.target_id)
  return !(selfEmployeeId && targetId === Number(selfEmployeeId))
}

/** Người đang đăng nhập: id hồ sơ nhân sự (chặn tự gán) và id tài khoản (chỉ sửa dòng mình gán). */
export interface AssignmentViewer {
  employeeId?: number | null
  userId?: number | null
}

/**
 * Dòng do CHÍNH tài khoản này gán. Thiếu `created_by` (backend cũ), `0` (dòng seed) hoặc không biết id tài khoản → không
 * phải của mình: đóng chứ không mở, backend cũng trả 403 cho trường hợp đó.
 */
export function isCreatedByViewer(
  row: Pick<WorkScheduleAssignment, 'created_by'>,
  userId: number | null | undefined,
): boolean {
  const createdBy = Number(row.created_by)
  return Boolean(userId) && createdBy > 0 && createdBy === Number(userId)
}

export interface AssignmentRowAccess {
  /** Mở hộp sửa theo đường nào; `none` = chỉ xem. */
  edit: AssignmentMode
  /** Hiện nút Xóa theo đường nào; `none` = không có nút. */
  remove: AssignmentMode
}

/**
 * Quyền trên MỘT dòng gán có sẵn. Đường `personal` chỉ áp cho dòng cấp Nhân sự, không phải hồ sơ của chính người xem,
 * VÀ do chính tài khoản đó gán — lịch Nhân sự hay Trưởng phòng khác gán thì chỉ xem. Dòng ĐÃ BẮT ĐẦU (ngày bắt đầu trước
 * `today`) thì Trưởng phòng không xóa được nữa, chỉ kết thúc bằng ngày kết thúc.
 */
export function resolveAssignmentRowAccess(
  can: CanFn,
  row: Pick<WorkScheduleAssignment, 'target_level' | 'target_id' | 'created_by' | 'effective_from'>,
  viewer: AssignmentViewer,
  today: string,
): AssignmentRowAccess {
  const ownable =
    isPersonallyAssignable(row, viewer.employeeId) && isCreatedByViewer(row, viewer.userId)
  const narrow = (mode: AssignmentMode): AssignmentMode =>
    mode === 'personal' && !ownable ? 'none' : mode
  const remove = narrow(resolveAssignmentMode(can, 'delete'))
  return {
    edit: narrow(resolveAssignmentMode(can, 'write')),
    remove: remove === 'personal' && hasStarted(row, today) ? 'none' : remove,
  }
}

/** Dòng đã bắt đầu: ngày bắt đầu TRƯỚC hôm nay (giờ VN). Bắt đầu đúng hôm nay vẫn còn sửa / xóa như chưa bắt đầu. */
export function hasStarted(row: Pick<WorkScheduleAssignment, 'effective_from'>, today: string): boolean {
  return Boolean(row.effective_from) && row.effective_from < today
}

/** Ngày `yyyy-mm-dd` dời `days` ngày, tính theo lịch (không qua UTC nên không lệch múi giờ). */
export function shiftIsoDate(iso: string, days: number): string {
  const [y, m, d] = iso.split('-').map(Number)
  const shifted = new Date(y, m - 1, d + days)
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${shifted.getFullYear()}-${pad(shifted.getMonth() + 1)}-${pad(shifted.getDate())}`
}

/** Ô nào trên hộp sửa của Trưởng phòng bị khóa — cùng luật `assignment_access.check_personal_update` của backend. */
export interface PersonalRowLocks {
  /** Đã bắt đầu: chỉ còn ngày kết thúc + ghi chú. */
  started: boolean
  /** Dòng đã thay lịch trước đó: không đổi đối tượng / ngày bắt đầu (đổi thì xóa rồi tạo lại). */
  replaces: boolean
  lockTarget: boolean
  lockSchedule: boolean
  lockStart: boolean
  /** Mốc sớm nhất của ngày kết thúc (hôm qua) khi đã bắt đầu; `null` = không chặn riêng. */
  endMin: string | null
}

const NO_LOCKS: PersonalRowLocks = {
  started: false,
  replaces: false,
  lockTarget: false,
  lockSchedule: false,
  lockStart: false,
  endMin: null,
}

/** Khóa ô của MỘT dòng đang sửa trên đường Trưởng phòng; tạo mới (không có dòng) thì không khóa gì. */
export function resolvePersonalRowLocks(
  row: Pick<WorkScheduleAssignment, 'effective_from' | 'replaces_previous'> | null | undefined,
  today: string,
): PersonalRowLocks {
  if (!row) return NO_LOCKS
  const started = hasStarted(row, today)
  const replaces = row.replaces_previous === true
  return {
    started,
    replaces,
    lockTarget: started || replaces,
    lockSchedule: started,
    lockStart: started || replaces,
    endMin: started ? shiftIsoDate(today, -1) : null,
  }
}

export const STARTED_EDIT_HINT = 'Lịch đã bắt đầu: chỉ đặt được ngày kết thúc và ghi chú.'
export const STARTED_DELETE_HINT = 'Lịch đã bắt đầu, không xóa được — hãy đặt ngày kết thúc.'
export const REPLACES_PREVIOUS_HINT =
  'Lịch này đã thay lịch trước đó: muốn đổi người hoặc ngày bắt đầu, hãy xóa rồi tạo lại.'
/** Khớp câu 422 của backend. */
export const STARTED_END_MESSAGE = 'Ngày kết thúc của lịch đã bắt đầu phải từ hôm qua trở đi'

/**
 * Ngày kết thúc của dòng đã bắt đầu: trống (không thời hạn) hoặc từ `endMin` trở đi; giữ nguyên giá trị đã lưu thì
 * không chặn (backend chỉ chốt khi ngày đổi).
 */
export function isAllowedStartedEffectiveTo(
  value: string,
  endMin: string,
  storedValue?: string | null,
): boolean {
  if (!value) return true
  if (storedValue && value === storedValue) return true
  return value >= endMin
}

/** Câu nhắc (cũng là câu báo lỗi) của ô ngày bắt đầu khi Trưởng phòng gán lịch riêng — khớp câu 422 của backend. */
export const PERSONAL_EFFECTIVE_FROM_HINT = 'Ngày hiệu lực phải từ hôm nay trở đi'

/**
 * Ngày hiệu lực Trưởng phòng được chọn: từ hôm nay trở đi (backend 422 nếu lùi). Sửa dòng mà KHÔNG đổi ngày bắt đầu đã
 * lưu thì giữ được ngày cũ — backend chỉ chốt khi tạo mới hoặc khi ngày đổi. So chuỗi `yyyy-mm-dd` là so đúng thứ tự.
 */
export function isAllowedPersonalEffectiveFrom(
  value: string,
  today: string,
  storedValue?: string | null,
): boolean {
  if (!value) return true // ô trống do luật bắt buộc báo, không báo trùng hai câu
  if (storedValue && value === storedValue) return true
  return value >= today
}
