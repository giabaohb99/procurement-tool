import { useMemo } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { CrudListPage } from '@/shared/crud'
import { buildHeadcountPlanCrudConfig } from '../config/headcount-plan-crud'
import { useCompanies } from '../hooks/use-companies'
import { useDepartments } from '../hooks/use-departments'
import { buildHeadcountPlanYearOptions } from '../utils/headcount-plan-options'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'

/** Đủ chứa mọi pháp nhân / phòng của tập đoàn trong MỘT lượt gọi (cùng trần với ô lọc phòng của Báo cáo). */
const LOOKUP_PAGE_SIZE = 500

/**
 * Màn KẾ HOẠCH NHÂN SỰ `/hr/headcount-plans` (duoc-CR-689). Cấu hình dựng lại khi danh mục
 * pháp nhân / phòng về — `useMemo` theo đúng mấy thứ đó, KHÔNG
 * theo từng lượt vẽ: hộp thoại Thêm/Sửa `reset` biểu mẫu mỗi khi `config.formFields` đổi danh
 * tính, dựng mới mỗi lượt vẽ là đang gõ dở thì mất chữ.
 */
export function HeadcountPlanListPage() {
  const { can } = usePermission()
  const canSeePayroll = can('labor_contract', 'read')
  const companies = useCompanies({ page_size: LOOKUP_PAGE_SIZE }, { enabled: can('company', 'read') })
  const companyItems = companies.data?.items
  //  Phòng ban DÙNG CHUNG cho mọi pháp nhân (không có ánh xạ phòng ↔ pháp nhân) — ô chọn bày mọi
  //  phòng đang dùng; backend chỉ bắt phòng có thật (chốt 28/10/2026).
  const departments = useDepartments(
    { page_size: LOOKUP_PAGE_SIZE, is_active: true },
    { enabled: can('department', 'read') },
  )
  const departmentItems = departments.data?.items

  const config = useMemo(() => {
    const year = new Date().getFullYear()
    return buildHeadcountPlanCrudConfig({
      canSeePayroll,
      yearOptions: buildHeadcountPlanYearOptions(year),
      companyOptions: (companyItems ?? []).map((c) => ({ value: String(c.id), label: c.name })),
      departments: departmentItems ?? [],
      defaultYear: year,
    })
  }, [canSeePayroll, companyItems, departmentItems])

  return <CrudListPage config={config} toolbarClassName={LIST_TOOLBAR_STICKY_TOP} />
}
