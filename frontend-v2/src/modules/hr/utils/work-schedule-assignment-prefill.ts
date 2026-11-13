import { appRoutes } from '@/shared/constants/app-routes'
import type { CrudConfig, CrudFormField, CrudRecord } from '@/shared/crud'
import { WORK_SCHEDULE_LEVEL_CODE, type WorkScheduleAssignment } from '../types/work-schedule'

/**
 * Mở hộp THÊM dòng gán lịch với cấp + đối tượng điền sẵn từ URL (duoc-CR-757) — để trang
 * phòng ban (và sau này pháp nhân / nhân sự) dẫn thẳng sang mà người dùng khỏi chọn lại.
 *
 * `target_level` cố ý TRÙNG tên với ô lọc nhanh "Cấp áp dụng" của danh sách: mở hộp từ trang
 * phòng ban thì bảng phía sau cũng đang lọc đúng cấp phòng ban, lưu xong thấy ngay dòng mới.
 * Hai tham số `prefill_*` mới là tín hiệu mở hộp; đóng hộp thì gỡ chúng (xem `PREFILL_PARAMS`).
 */
export const PREFILL_TARGET_ID_PARAM = 'prefill_target_id'
export const PREFILL_TARGET_NAME_PARAM = 'prefill_target_name'
const LEVEL_PARAM = 'target_level'

/** Tham số gỡ khỏi URL khi đóng hộp — giữ `target_level` vì nó còn là bộ lọc của bảng. */
export const PREFILL_PARAMS = [PREFILL_TARGET_ID_PARAM, PREFILL_TARGET_NAME_PARAM] as const

/** Cấp có ĐỐI TƯỢNG cụ thể. "Toàn hệ thống" không có đối tượng nên không điền sẵn được. */
const PREFILLABLE_LEVELS: ReadonlySet<number> = new Set([
  WORK_SCHEDULE_LEVEL_CODE.COMPANY,
  WORK_SCHEDULE_LEVEL_CODE.DEPARTMENT,
  WORK_SCHEDULE_LEVEL_CODE.EMPLOYEE,
])

/** Trần độ dài tên hiển thị lấy từ URL — chỉ để hiện trong ô chọn lúc danh sách chưa tải xong. */
const MAX_NAME_LENGTH = 200

export interface AssignmentPrefill {
  level: number
  targetId: number
  /** Tên hiện tạm trong ô Đối tượng khi danh sách chưa tải; rỗng thì ô tự hiện "#id". */
  targetName: string
}

/** Chỉ nhận số nguyên dương viết bằng chữ số trần: "12" được; "1e3", "0x1f", "-3", "1.5", " 7" bị loại. */
function parsePositiveId(raw: string | null): number | null {
  if (!raw || !/^\d{1,15}$/.test(raw)) return null
  const value = Number(raw)
  return Number.isSafeInteger(value) && value > 0 ? value : null
}

/** Đọc yêu cầu điền sẵn từ URL; thiếu / sai bất kỳ phần nào thì `null` (không mở hộp). */
export function parseAssignmentPrefill(params: URLSearchParams): AssignmentPrefill | null {
  const level = parsePositiveId(params.get(LEVEL_PARAM))
  const targetId = parsePositiveId(params.get(PREFILL_TARGET_ID_PARAM))
  if (level === null || targetId === null || !PREFILLABLE_LEVELS.has(level)) return null
  const targetName = (params.get(PREFILL_TARGET_NAME_PARAM) ?? '').trim().slice(0, MAX_NAME_LENGTH)
  return { level, targetId, targetName }
}

/** Đường dẫn sang danh sách gán lịch, mở sẵn hộp Thêm cho đúng đối tượng. */
export function buildAssignmentCreateUrl(prefill: AssignmentPrefill): string {
  const qs = new URLSearchParams({
    [LEVEL_PARAM]: String(prefill.level),
    [PREFILL_TARGET_ID_PARAM]: String(prefill.targetId),
  })
  if (prefill.targetName) qs.set(PREFILL_TARGET_NAME_PARAM, prefill.targetName)
  return `${appRoutes.hr.workScheduleAssignments}?${qs.toString()}`
}

/** Đường dẫn sang danh sách gán lịch, lọc sẵn theo một cấp. */
export function buildAssignmentListUrl(level: number): string {
  return `${appRoutes.hr.workScheduleAssignments}?${LEVEL_PARAM}=${level}`
}

/**
 * Bản cấu hình CRUD có giá trị mặc định của ba ô cấp / đối tượng / tên đối tượng thay bằng
 * phần điền sẵn. Chỉ đổi `defaultValue` — mọi luật của ô (đổi cấp thì xóa đối tượng, kiểm bắt
 * buộc…) giữ nguyên, người dùng vẫn đổi được cả hai ô.
 *
 * ⚠️ Gọi MỘT lần rồi giữ kết quả (`useState` / `useMemo`): `CrudFormDialog` reset biểu mẫu mỗi
 * khi `config.formFields` đổi danh tính, dựng lại mỗi lần render là xóa mất thứ người dùng gõ.
 */
export function withAssignmentPrefill(
  config: CrudConfig<WorkScheduleAssignment>,
  prefill: AssignmentPrefill,
): CrudConfig<WorkScheduleAssignment> {
  const overrides: Record<string, unknown> = {
    target_level: prefill.level,
    target_id: prefill.targetId,
    target_name: prefill.targetName,
  }
  const apply = (fields: CrudFormField[]) =>
    fields.map((field) =>
      field.name in overrides ? { ...field, defaultValue: overrides[field.name] } : field,
    )
  const spec = config.formFields
  const formFields = Array.isArray(spec) ? apply(spec) : (values: CrudRecord) => apply(spec(values))
  return { ...config, formFields }
}
