import { useCallback } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import type { ConditionChoice } from '@/shared/condition-builder/condition-rule'

import {
  DEFAULT_CENTRAL_DEPT_CODE,
  type PrDispatchConditionField,
} from '../config/pr-dispatch-condition-fields'

/**
 * Lựa chọn của từng ô điều kiện bỏ qua điều phối (bao-CR-528).
 *
 * `centralDeptCode` = mã phòng thu mua mặc định đang cấu hình; phòng đó bị gỡ
 * khỏi ô «Phòng xử lý» vì bối cảnh phiếu đưa nó vào dưới dạng «để trống».
 *
 * Ba danh mục mượn của phân hệ Nhân sự tự tắt khi thiếu quyền đọc — cứ mount là
 * gọi thì người chỉ có quyền cấu hình ăn toast 403 ngay lúc mở tab.
 */
export function usePrDispatchConditionChoices(centralDeptCode: string) {
  const { can } = usePermission()
  const { data: departments } = useDepartments(
    { page_size: 500 },
    { enabled: can('department', 'read') },
  )
  const { data: companies } = useCompanies(
    { page_size: 200, is_active: true },
    { enabled: can('company', 'read') },
  )
  const { data: employees } = useEmployees(
    { page_size: 500 },
    { enabled: can('employee', 'read') },
  )
  const centralCode = centralDeptCode.trim() || DEFAULT_CENTRAL_DEPT_CODE

  return useCallback(
    (field: PrDispatchConditionField): ConditionChoice[] => {
      switch (field.source) {
        case 'handler_department':
        case 'department':
          return (departments?.items ?? [])
            .filter((item) => item.is_active)
            .filter((item) => field.source === 'department' || item.code !== centralCode)
            .map((item) => ({ id: item.id, label: item.name, hint: item.code }))
        case 'company':
          return (companies?.items ?? []).map((item) => ({
            id: item.id,
            label: item.name,
            hint: item.code,
          }))
        case 'employee':
          return (employees?.items ?? []).map((item) => ({
            id: item.id,
            label: item.full_name,
            hint: item.code,
          }))
        case 'none':
          return []
      }
    },
    [centralCode, companies?.items, departments?.items, employees?.items],
  )
}
