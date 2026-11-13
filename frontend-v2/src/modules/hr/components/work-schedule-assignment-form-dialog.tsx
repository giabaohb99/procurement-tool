import { useMemo } from 'react'

import { useAuthStore } from '@/core/auth/auth-store'
import { usePermission } from '@/core/authorization/use-permission'
import { CrudFormDialog, type CrudFormDialogProps } from '@/shared/crud'
import { toDateInputValue } from '@/shared/utils/format-date'
import { withPersonalAssignmentFields } from '../config/work-schedule-assignment-personal-config'
import type { WorkScheduleAssignment } from '../types/work-schedule'
import {
  entityForMode,
  resolveAssignmentMode,
  resolveAssignmentRowAccess,
  resolvePersonalRowLocks,
  type AssignmentRowAccess,
} from '../utils/work-schedule-assignment-mode'
import { WorkScheduleAssignmentViewDialog } from './work-schedule-assignment-view-dialog'

const VIEW_ONLY_PERSONAL_REASON =
  'Bạn chỉ sửa được lịch riêng do chính mình gán cho nhân viên thuộc phòng mình (không gồm chính bạn). Lịch của cả phòng, pháp nhân, toàn hệ thống do Nhân sự cấu hình.'
const VIEW_ONLY_REASON = 'Bạn chỉ có quyền xem dòng gán lịch này.'

/**
 * Hộp Thêm / Sửa dòng gán lịch (duoc-CR-757 lượt 2) — chọn một trong ba đường theo quyền và theo TỪNG dòng:
 *
 * - **Nhân sự** (`work_schedule.<hành động>`): đúng khuôn `CrudFormDialog` cũ, không đổi gì.
 * - **Trưởng phòng** (chỉ `work_schedule_personal`): cùng khuôn, cấp khóa ở Nhân sự, không chọn được chính mình,
 *   ngày bắt đầu từ hôm nay, nút Xóa gác bằng khóa riêng. Sửa / xóa chỉ dòng cấp Nhân sự, không phải hồ sơ của chính
 *   họ, và do CHÍNH tài khoản họ gán (`created_by`). Dòng đã bắt đầu: chỉ còn ngày kết thúc + ghi chú, không xóa; dòng
 *   đã thay lịch trước đó: khóa đối tượng + ngày bắt đầu (`resolvePersonalRowLocks`).
 * - **Chỉ xem**: dòng ngoài tầm (cấp phòng / pháp nhân / toàn hệ thống, lịch của chính mình, lịch người khác gán) mở
 *   hộp chỉ xem.
 *
 * Backend chốt lại mọi luật; hộp chỉ tránh cho người dùng gõ xong mới ăn 403.
 */
export function WorkScheduleAssignmentFormDialog(props: CrudFormDialogProps<WorkScheduleAssignment>) {
  const { config, item, open, onOpenChange } = props
  const { can } = usePermission()
  const selfEmployeeId = useAuthStore((s) => s.user?.employee_id)
  const selfUserId = useAuthStore((s) => s.user?.id)
  //  Hôm nay theo giờ máy người dùng (công ty ở VN) — chốt thật vẫn là `vn_today()` của backend.
  const today = toDateInputValue(new Date())

  const access: AssignmentRowAccess = item
    ? resolveAssignmentRowAccess(can, item, { employeeId: selfEmployeeId, userId: selfUserId }, today)
    : { edit: resolveAssignmentMode(can, 'create'), remove: 'none' }

  //  Giữ danh tính ổn định: `CrudFormDialog` reset biểu mẫu mỗi khi `config.formFields` đổi.
  const formConfig = useMemo(() => {
    const base =
      access.edit === 'personal'
        ? withPersonalAssignmentFields(config, {
            selfEmployeeId,
            item,
            today,
            locks: resolvePersonalRowLocks(item, today),
          })
        : config
    return {
      ...base,
      //  Khung chung gác nút Xóa bằng `config.entity` → trỏ đúng khóa của đường được phép xóa dòng này.
      entity: entityForMode(access.remove),
      deleteInForm: Boolean(config.deleteInForm) && access.remove !== 'none',
    }
  }, [config, selfEmployeeId, item, today, access.edit, access.remove])

  if (item && access.edit === 'none') {
    const hasPersonalKey = can('work_schedule_personal', 'write') || can('work_schedule_personal', 'create')
    return (
      <WorkScheduleAssignmentViewDialog
        open={open}
        onOpenChange={onOpenChange}
        item={item}
        reason={hasPersonalKey ? VIEW_ONLY_PERSONAL_REASON : VIEW_ONLY_REASON}
      />
    )
  }

  return <CrudFormDialog {...props} config={formConfig} />
}
