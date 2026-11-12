import { useSearchParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { CrudListPage } from '@/shared/crud'
import { ForbiddenPage } from '@/shared/ui/forbidden-page'
import { HrSetupTabs } from '../components/hr-setup-tabs'
import { LEAVE_POLICY_CRUD_CONFIG } from '../config/leave-policy-crud'
import { LEAVE_POLICY_HUB_TAB_PARAM, resolveLeavePolicyHubTab } from '../utils/leave-policy-hub-tabs'
import { LIST_TOOLBAR_STICKY_TOP } from '../utils/list-sticky'
import { LeavePolicyAssignmentListPage } from './leave-policy-assignment-list-page'

/**
 * NGHỈ PHÉP › CHÍNH SÁCH NGHỈ PHÉP — `/hr/leave-policy-assignments?tab=assignments|policies` (duoc-CR-750).
 *
 * Gom hai việc vào một màn: tab **Phân bổ** (ai áp gói nào, từ–đến, Kết thúc / Xóa) và tab **Chính sách** (danh
 * sách gói). Tab nhớ trên URL; vắng hoặc sai / không có quyền thì mở tab đầu tiên người đó được thấy.
 *
 * ⚠️ **Mỗi tab là CẢ một màn danh sách có sẵn, không phải phần thân nhúng dưới một tiêu đề chung** — nút đầu trang
 * tự đổi theo tab mà không phải chép khung bảng nào. Từ duoc-CR-754 hai tab KHÔNG còn thanh riêng: chúng là hai tab
 * **Phân bổ chính sách** · **Gói chính sách** của dải Thiết lập phẳng (`utils/hr-setup-tab-list.ts`).
 *
 * Đổi tab = đổi `?tab=` và BỎ bộ lọc của tab cũ (link của dải tab không mang tham số khác): hai bảng có bộ lọc
 * khác nhau trên cùng chuỗi truy vấn (`q`, `sort_by`, `is_active`…), giữ lại là bảng kia mở ra đã bị lọc sẵn.
 *
 * Hàng rào route: mục menu "Chính sách nghỉ phép" ở `routes.tsx`. Đường cũ `/hr/leave-policies` chuyển hướng về
 * tab Chính sách (`leave-policies-legacy-redirect.tsx`).
 */
export function LeavePolicyHubPage() {
  const { can } = usePermission()
  const [searchParams] = useSearchParams()
  const active = resolveLeavePolicyHubTab(searchParams.get(LEAVE_POLICY_HUB_TAB_PARAM), can)

  //  Route đã gác bằng đúng luật này nên nhánh này chỉ chạy khi trang bị dựng ở chỗ khác — vẫn chặn tử tế.
  if (!active) return <ForbiddenPage />

  return active === 'policies' ? (
    <CrudListPage
      config={LEAVE_POLICY_CRUD_CONFIG}
      topContent={<HrSetupTabs />}
      compactHeader
      toolbarClassName={LIST_TOOLBAR_STICKY_TOP}
    />
  ) : (
    <LeavePolicyAssignmentListPage topContent={<HrSetupTabs />} compactHeader toolbarClassName={LIST_TOOLBAR_STICKY_TOP} />
  )
}
