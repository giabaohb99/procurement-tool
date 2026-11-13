import {
  SYSTEM_LEVEL_LABEL,
  WORK_SCHEDULE_LEVEL_CODE,
  type WorkScheduleAssignment,
} from '../types/work-schedule'

/** "Toàn hệ thống" cho cấp hệ thống (đối tượng `0` không có tên), còn lại lấy tên backend trả kèm. */
export function describeAssignmentTarget(
  row: Pick<WorkScheduleAssignment, 'target_level' | 'target_id' | 'target_name'>,
): string {
  if (row.target_level === WORK_SCHEDULE_LEVEL_CODE.SYSTEM) return SYSTEM_LEVEL_LABEL
  return row.target_name || `#${row.target_id}`
}
