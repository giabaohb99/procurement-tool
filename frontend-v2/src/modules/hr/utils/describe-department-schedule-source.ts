import { formatDate } from '@/shared/utils/format-date'
import { WORK_SCHEDULE_LEVEL_CODE, type EffectiveWorkSchedule } from '../types/work-schedule'

/** Câu khi chưa ai gán gì từ phòng ban trở lên. Giờ cụ thể đã nằm trong tên mẫu mặc định backend gửi
 *  (`FALLBACK_NAME`) và lưới bảy ngày, nhắc lại ở đây là trùng chữ trên cùng một dòng. */
export const DEPARTMENT_FALLBACK_SOURCE = 'Chưa gán — dùng lịch mặc định'

/**
 * Câu nói lịch của PHÒNG BAN lấy từ đâu (duoc-CR-757). Rẽ nhánh bằng mã cấp
 * `WORK_SCHEDULE_LEVEL_CODE` (1 hệ thống · 2 pháp nhân · 3 phòng ban), KHÔNG bằng số trần.
 * `is_fallback` thắng mọi thứ khác — khi đó backend gửi `level = 0`.
 */
export function describeDepartmentScheduleSource(schedule: EffectiveWorkSchedule): string {
  if (schedule.is_fallback) return DEPARTMENT_FALLBACK_SOURCE
  const target = (schedule.target_name ?? '').trim()
  switch (schedule.level) {
    case WORK_SCHEDULE_LEVEL_CODE.DEPARTMENT: {
      const from = formatDate(schedule.effective_from)
      const to = formatDate(schedule.effective_to)
      if (!from) return 'Gán riêng cho phòng này'
      return to ? `Gán riêng cho phòng này từ ${from} đến ${to}` : `Gán riêng cho phòng này từ ${from}`
    }
    case WORK_SCHEDULE_LEVEL_CODE.COMPANY:
      return target ? `Theo lịch của pháp nhân ${target}` : 'Theo lịch của pháp nhân'
    case WORK_SCHEDULE_LEVEL_CODE.SYSTEM:
      return 'Theo lịch toàn hệ thống'
    default:
      //  Cấp lạ (backend thêm cấp mới, dữ liệu trôi): nói nhãn backend gửi, không bịa nguồn.
      return schedule.level_label?.trim() || 'Không rõ nguồn'
  }
}
