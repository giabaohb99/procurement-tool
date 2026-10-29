import { useMemo } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { CrudListPage } from '@/shared/crud'
import { buildHeadcountPlanCrudConfig } from '../config/headcount-plan-crud'
import { useCompanies } from '../hooks/use-companies'
import { useDepartments } from '../hooks/use-departments'
import { buildHeadcountPlanDepartmentOptions, buildHeadcountPlanYearOptions } from '../utils/headcount-plan-options'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'

/** Đủ chứa mọi pháp nhân / phòng của tập đoàn trong MỘT lượt gọi (cùng trần với ô lọc phòng của Báo cáo). */
const LOOKUP_PAGE_SIZE = 500

/**
 * Màn KẾ HOẠCH NHÂN SỰ `/hr/headcount-plans` (duoc-CR-690). Cấu hình dựng lại khi danh mục pháp
 * nhân / phòng về — `useMemo` theo đúng mấy thứ đó, không theo từng lượt vẽ. Chỉ nạp hai danh mục
 * của ô lọc; danh mục của form (nhân sự, chức vụ, mẫu) để trang kế hoạch tự nạp.
 */
export function HeadcountPlanListPage() {
  const { can } = usePermission()
  const canSeePayroll = can('labor_contract', 'read')
  const companies = useCompanies({ page_size: LOOKUP_PAGE_SIZE }, { enabled: can('company', 'read') })
  //  Phòng ban DÙNG CHUNG cho mọi pháp nhân — ô lọc bày mọi phòng đang dùng (chốt 28/10/2026).
  const departments = useDepartments(
    { page_size: LOOKUP_PAGE_SIZE, is_active: true },
    { enabled: can('department', 'read') },
  )
  const companyItems = companies.data?.items
  const departmentItems = departments.data?.items

  const config = useMemo(
    () =>
      buildHeadcountPlanCrudConfig({
        canSeePayroll,
        yearOptions: buildHeadcountPlanYearOptions(new Date().getFullYear()),
        companyOptions: (companyItems ?? []).map((c) => ({ value: String(c.id), label: c.name })),
        departmentOptions: buildHeadcountPlanDepartmentOptions(departmentItems ?? []),
      }),
    [canSeePayroll, companyItems, departmentItems],
  )

  return <CrudListPage config={config} toolbarClassName={LIST_TOOLBAR_STICKY_TOP} />
}
