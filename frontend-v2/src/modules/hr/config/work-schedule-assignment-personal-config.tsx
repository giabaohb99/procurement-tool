import type { CrudConfig, CrudFormField, CrudRecord } from '@/shared/crud'
import { WorkScheduleLevelField } from '../components/work-schedule-level-field'
import { WorkSchedulePersonalDateField } from '../components/work-schedule-personal-date-field'
import { WorkScheduleSelectField } from '../components/work-schedule-select-field'
import { WorkScheduleTargetField } from '../components/work-schedule-target-field'
import { WORK_SCHEDULE_LEVEL_CODE, type WorkScheduleAssignment } from '../types/work-schedule'
import {
  isAllowedPersonalEffectiveFrom,
  isAllowedStartedEffectiveTo,
  PERSONAL_EFFECTIVE_FROM_HINT,
  REPLACES_PREVIOUS_HINT,
  STARTED_DELETE_HINT,
  STARTED_EDIT_HINT,
  STARTED_END_MESSAGE,
  type PersonalRowLocks,
} from '../utils/work-schedule-assignment-mode'

/** Câu nhắc dưới ô Cấp áp dụng khi Trưởng phòng gán lịch riêng. */
export const PERSONAL_ASSIGNMENT_HINT =
  'Bạn chỉ gán được lịch riêng cho nhân viên thuộc phòng mình. Mẫu lịch và lịch của cả phòng do Nhân sự cấu hình.'

const employeeLevel = WORK_SCHEDULE_LEVEL_CODE.EMPLOYEE

export interface PersonalAssignmentOptions {
  selfEmployeeId?: number
  /** Dòng đang sửa; trống khi tạo mới. */
  item?: Pick<WorkScheduleAssignment, 'effective_from' | 'effective_to'> | null
  /** Hôm nay `yyyy-mm-dd` (giờ máy người dùng = giờ VN). */
  today: string
  locks: PersonalRowLocks
}

/** Các câu nhắc trên đầu hộp: luật chung + vì sao một số ô đang khóa. */
function personalHints(locks: PersonalRowLocks): string[] {
  return [
    PERSONAL_ASSIGNMENT_HINT,
    ...(locks.started ? [STARTED_EDIT_HINT, STARTED_DELETE_HINT] : []),
    ...(locks.replaces && !locks.started ? [REPLACES_PREVIOUS_HINT] : []),
  ]
}

/**
 * Bản cấu hình hộp Thêm / Sửa cho người chỉ có `work_schedule_personal` (duoc-CR-757 lượt 2):
 *
 * - Ô **Cấp áp dụng** khóa ở Nhân sự, hiện dạng chữ chỉ xem (không phải ô chọn bị tắt).
 * - Ô **Đối tượng** lấy từ `/tools/assignable-employees`: đúng nhân viên được gán, backend đã bỏ chính người gọi.
 * - Ô **Hiệu lực từ ngày** không nhận ngày trước hôm nay (tạo mới mặc định hôm nay); giữ nguyên ngày đã lưu thì không chặn.
 * - Dòng ĐÃ BẮT ĐẦU: chỉ còn ngày kết thúc (từ hôm qua trở đi, hoặc bỏ trống) + ghi chú; nút Xóa ẩn ở hộp thoại.
 * - Dòng ĐÃ THAY LỊCH TRƯỚC ĐÓ: khóa đối tượng + ngày bắt đầu; mẫu lịch còn đổi được nếu chưa bắt đầu.
 *
 * Mọi luật trên backend chốt lại (`assignment_access.check_personal_*`); câu lỗi hiện ở toast của khung CRUD.
 * Điền sẵn từ URL (`withAssignmentPrefill`) mà khác cấp Nhân sự hoặc trỏ vào chính mình thì bỏ đối tượng đó.
 *
 * ⚠️ Gọi trong `useMemo`: `CrudFormDialog` reset biểu mẫu mỗi khi `formFields` đổi danh tính.
 */
export function withPersonalAssignmentFields(
  config: CrudConfig<WorkScheduleAssignment>,
  { selfEmployeeId, item, today, locks }: PersonalAssignmentOptions,
): CrudConfig<WorkScheduleAssignment> {
  const storedFrom = item?.effective_from ?? null
  const storedTo = item?.effective_to ?? null

  const apply = (fields: CrudFormField[]): CrudFormField[] => {
    const byName = (name: string) => fields.find((field) => field.name === name)
    const prefillLevel = Number(byName('target_level')?.defaultValue)
    const prefillTarget = Number(byName('target_id')?.defaultValue)
    const keepTarget =
      prefillLevel === employeeLevel && !(selfEmployeeId && prefillTarget === selfEmployeeId)

    return fields.map((field): CrudFormField => {
      switch (field.name) {
        case 'target_level':
          return {
            ...field,
            defaultValue: employeeLevel,
            render: ({ control, name }) => (
              <WorkScheduleLevelField
                control={control}
                name={name}
                idName="target_id"
                disabled
                focusableWhenReadOnly
                hint={personalHints(locks).map((line) => (
                  <span key={line} className="block">
                    {line}
                  </span>
                ))}
              />
            ),
          }
        case 'target_id':
          return {
            ...field,
            defaultValue: keepTarget ? field.defaultValue : 0,
            render: ({ control, name, disabled }) => (
              <WorkScheduleTargetField
                control={control}
                name={name}
                levelName="target_level"
                disabled={disabled || locks.lockTarget}
                excludeEmployeeId={selfEmployeeId}
                assignableOnly
              />
            ),
          }
        case 'target_name':
          return keepTarget ? field : { ...field, defaultValue: '' }
        case 'schedule_id':
          return {
            ...field,
            render: ({ control, name, disabled }) => (
              <WorkScheduleSelectField control={control} name={name} disabled={disabled || locks.lockSchedule} />
            ),
          }
        case 'effective_from':
          return {
            ...field,
            type: 'custom',
            defaultValue: field.defaultValue ?? today,
            render: ({ control, name }) => (
              <WorkSchedulePersonalDateField
                control={control}
                name={name}
                label={field.label}
                required
                readOnly={locks.lockStart}
                validate={(value) =>
                  isAllowedPersonalEffectiveFrom(value, today, storedFrom) || PERSONAL_EFFECTIVE_FROM_HINT
                }
                hints={locks.lockStart ? [] : [PERSONAL_EFFECTIVE_FROM_HINT, field.hint]}
              />
            ),
          }
        case 'effective_to': {
          const endMin = locks.endMin
          if (!endMin) return field
          return {
            ...field,
            type: 'custom',
            render: ({ control, name }) => (
              <WorkSchedulePersonalDateField
                control={control}
                name={name}
                label={field.label}
                validate={(value) =>
                  isAllowedStartedEffectiveTo(value, endMin, storedTo) || STARTED_END_MESSAGE
                }
                hints={[`${STARTED_END_MESSAGE}. ${field.hint ?? ''}`.trim()]}
              />
            ),
          }
        }
        default:
          return field
      }
    })
  }

  const spec = config.formFields
  const formFields = Array.isArray(spec)
    ? apply(spec)
    : (values: CrudRecord) => apply(spec(values))
  return { ...config, formFields }
}
