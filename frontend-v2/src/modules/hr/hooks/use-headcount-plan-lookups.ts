import { useMemo } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { buildHeadcountPlanDepartmentOptions, buildHeadcountPlanYearOptions } from '../utils/headcount-plan-options'
import { useCompanies } from './use-companies'
import { useDepartments } from './use-departments'
import { useEmployees } from './use-employees'
import { useHrCostGroups } from './use-hr-cost-templates'
import { useJobPositions } from './use-job-positions'

/** Đủ chứa mọi pháp nhân / phòng / nhân sự của tập đoàn trong MỘT lượt (cùng trần với các ô chọn khác). */
const LOOKUP_PAGE_SIZE = 500
const EMPLOYEE_PAGE_SIZE = 1000

/**
 * Mọi DANH MỤC mà trang kế hoạch cần, gom một chỗ. Mỗi danh mục tự TẮT khi người xem thiếu quyền đọc
 * nó — cứ mount là gọi thì người chỉ có `headcount_plan` ăn toast 403 ngay lúc mở trang (bẫy CR-106).
 * Nhóm chi phí chỉ để khoản mới tự xếp nhóm — trang không hiện nhóm.
 */
export function useHeadcountPlanLookups(currentYear: number) {
  const { can } = usePermission()
  const companies = useCompanies({ page_size: LOOKUP_PAGE_SIZE }, { enabled: can('company', 'read') })
  const departments = useDepartments(
    { page_size: LOOKUP_PAGE_SIZE, is_active: true },
    { enabled: can('department', 'read') },
  )
  const employees = useEmployees(
    { page_size: EMPLOYEE_PAGE_SIZE, is_active: true },
    { enabled: can('employee', 'read') },
  )
  const positions = useJobPositions(can('job_position', 'read'))
  const groups = useHrCostGroups(can('headcount_plan', 'read'))

  const companyItems = companies.data?.items
  const departmentItems = departments.data?.items
  const employeeItems = employees.data?.items
  const positionItems = positions.data?.items
  const groupItems = groups.data?.items

  return useMemo(
    () => ({
      yearOptions: buildHeadcountPlanYearOptions(currentYear).map((o) => ({ value: String(o.value), label: o.label })),
      companyOptions: (companyItems ?? []).map((c) => ({ value: String(c.id), label: c.name })),
      departmentOptions: buildHeadcountPlanDepartmentOptions(departmentItems ?? []).map((o) => ({
        value: String(o.value),
        label: o.label,
      })),
      approverOptions: (employeeItems ?? []).map((e) => ({ value: String(e.id), label: `${e.full_name} (${e.code})` })),
      positions: (positionItems ?? []).map((p) => ({ id: p.id, name: p.name })),
      groups: groupItems ?? [],
    }),
    [currentYear, companyItems, departmentItems, employeeItems, positionItems, groupItems],
  )
}
