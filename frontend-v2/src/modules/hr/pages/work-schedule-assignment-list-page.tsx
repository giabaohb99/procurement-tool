import { useMemo, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { CrudListPage } from '@/shared/crud'
import { HrSetupTabs } from '../components/hr-setup-tabs'
import { WorkScheduleAssignmentFormDialog } from '../components/work-schedule-assignment-form-dialog'
import { WORK_SCHEDULE_ASSIGNMENT_CRUD_CONFIG } from '../config/work-schedule-assignment-crud'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'
import { entityForMode, resolveAssignmentMode } from '../utils/work-schedule-assignment-mode'
import {
  PREFILL_PARAMS,
  parseAssignmentPrefill,
  withAssignmentPrefill,
} from '../utils/work-schedule-assignment-prefill'

export function WorkScheduleAssignmentListPage() {
  const { can } = usePermission()
  const [searchParams, setSearchParams] = useSearchParams()
  //  duoc-CR-757 lượt 2: nút Thêm hiện cho cả Nhân sự (`work_schedule.create`) lẫn Trưởng phòng
  //  (`work_schedule_personal.create`). Khung CRUD gác nút bằng `config.entity` nên trỏ khóa theo đường của người dùng;
  //  quyền sửa / xóa từng dòng do `WorkScheduleAssignmentFormDialog` tự xét.
  const createMode = resolveAssignmentMode(can, 'create')
  const listConfig = useMemo(
    () => ({ ...WORK_SCHEDULE_ASSIGNMENT_CRUD_CONFIG, entity: entityForMode(createMode) }),
    [createMode],
  )
  //  duoc-CR-757: vào từ trang phòng ban kèm `?target_level=&prefill_target_id=` thì mở sẵn hộp
  //  Thêm với cấp + đối tượng điền sẵn. Đọc MỘT lần lúc vào trang và giữ cấu hình trong state:
  //  dựng lại mỗi lần render là hộp reset biểu mẫu (xem `withAssignmentPrefill`).
  const [prefillConfig, setPrefillConfig] = useState(() => {
    const prefill = parseAssignmentPrefill(searchParams)
    return prefill ? withAssignmentPrefill(WORK_SCHEDULE_ASSIGNMENT_CRUD_CONFIG, prefill) : null
  })

  //  Đóng hộp (Hủy hoặc lưu xong) thì gỡ tham số điền sẵn khỏi URL — tải lại trang không mở lại
  //  hộp. Giữ `target_level`: nó còn là bộ lọc "Cấp áp dụng" của bảng.
  const closePrefill = () => {
    setPrefillConfig(null)
    setSearchParams(
      (current) => {
        const next = new URLSearchParams(current)
        for (const key of PREFILL_PARAMS) next.delete(key)
        return next
      },
      { replace: true },
    )
  }

  return (
    <>
      <CrudListPage
        config={listConfig}
        topContent={<HrSetupTabs />}
        compactHeader
        toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
      />
      {prefillConfig && createMode !== 'none' && (
        <WorkScheduleAssignmentFormDialog
          open
          config={prefillConfig}
          onOpenChange={(open) => {
            if (!open) closePrefill()
          }}
        />
      )}
    </>
  )
}
