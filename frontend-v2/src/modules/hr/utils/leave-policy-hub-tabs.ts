import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Hai tab của màn CHÍNH SÁCH NGHỈ PHÉP (duoc-CR-750) — `/hr/leave-policy-assignments?tab=…`.
 *
 * Trước CR này hai việc nằm hai nơi: gói chính sách là tab thứ tư của *Nghỉ phép › Thiết lập*, còn phân bổ là mục
 * menu riêng "Phân bổ chính sách". Nay gom về một màn, tab nhớ trên URL.
 *
 * ⚠️ **Luật hiện tab PHẢI khớp luật của mục menu** "Chính sách nghỉ phép" ở `routes.tsx`
 * (`entities: ['leave_balance', 'leave_type']` + `action: 'write'`, tức hiện khi GHI được một trong hai khóa).
 * Mục menu cũng là hàng rào của đường dẫn, nên lệch nhau là người vào được màn mà không thấy tab nào, hoặc thấy
 * tab mà gõ URL bị chặn. Bài kiểm `leave-policy-hub-tabs.test.ts` canh hai luật này bằng nhau.
 *
 * - **Phân bổ** gác `leave_balance.write`, đúng như màn phân bổ trước CR: seed cấp `leave_balance.read` phạm vi
 *   "của tôi" cho MỌI nhân viên, gác `read` là ai cũng thấy (đại ca chốt 03/11/2026, duoc-CR-717).
 * - **Chính sách** gác `leave_type.write`, đúng như tab ở Thiết lập trước CR.
 */
export type LeavePolicyHubTab = 'assignments' | 'policies'

/** Tiêu đề màn = nhãn mục menu (thanh breadcrumb ẩn tiêu đề trùng, duoc-CR-714). Cả hai tab dùng chung. */
export const LEAVE_POLICY_HUB_TITLE = 'Chính sách nghỉ phép'

type CanFn = (entity: PermissionEntity, action: PermissionAction) => boolean

export interface LeavePolicyHubTabDef {
  key: LeavePolicyHubTab
  label: string
  entity: PermissionEntity
}

/** Thứ tự = thứ tự trên màn; tab đầu tiên người đó có quyền là tab mặc định. */
export const LEAVE_POLICY_HUB_TABS: readonly LeavePolicyHubTabDef[] = [
  { key: 'assignments', label: 'Phân bổ', entity: 'leave_balance' },
  { key: 'policies', label: 'Chính sách', entity: 'leave_type' },
]

/** Hành động cả hai tab cùng đòi — khai một chỗ để mục menu và tab không lệch nhau. */
export const LEAVE_POLICY_HUB_ACTION: PermissionAction = 'write'

/** Tên tham số URL giữ tab đang mở (cũng phải khai vào `preserveParams` của bộ lọc nâng cao). */
export const LEAVE_POLICY_HUB_TAB_PARAM = 'tab'

/** Các tab người này được thấy, theo đúng thứ tự trên màn. */
export function getVisibleLeavePolicyHubTabs(can: CanFn): LeavePolicyHubTabDef[] {
  return LEAVE_POLICY_HUB_TABS.filter((t) => can(t.entity, LEAVE_POLICY_HUB_ACTION))
}

/**
 * Tab đang mở: giá trị trên URL nếu hợp lệ VÀ người đó có quyền, ngược lại tab đầu tiên được phép.
 * `null` khi không được tab nào (route đã gác nên chỉ xảy ra nếu ai đó dựng trang này ở chỗ khác).
 */
export function resolveLeavePolicyHubTab(raw: string | null, can: CanFn): LeavePolicyHubTab | null {
  const visible = getVisibleLeavePolicyHubTabs(can)
  return visible.find((t) => t.key === raw)?.key ?? visible[0]?.key ?? null
}

/**
 * Đường dẫn tới màn, mở sẵn một tab. `extra` là các tham số khác cần giữ (vd bộ lọc của dấu trang cũ).
 * Tham số `tab` trong `extra` bị đè bằng `tab` truyền vào.
 */
export function buildLeavePolicyHubHref(tab: LeavePolicyHubTab, extra?: URLSearchParams): string {
  const params = new URLSearchParams(extra)
  params.delete(LEAVE_POLICY_HUB_TAB_PARAM)
  const rest = params.toString()
  return `${appRoutes.hr.leavePolicyAssignments}?${LEAVE_POLICY_HUB_TAB_PARAM}=${tab}${rest ? `&${rest}` : ''}`
}
