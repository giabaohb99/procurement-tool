import type { NavContext } from '@/app/router/module-visibility'
import { visibleNavChildren } from '@/app/router/module-visibility'
import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import { appRoutes } from '@/shared/constants/app-routes'
import { hrSetupNavItem } from '../config/hr-setup-nav-item'
import {
  buildLeavePolicyHubHref,
  getVisibleLeavePolicyHubTabs,
  LEAVE_POLICY_HUB_TAB_PARAM,
  resolveLeavePolicyHubTab,
  type LeavePolicyHubTab,
} from './leave-policy-hub-tabs'

type CanFn = (entity: PermissionEntity, action: PermissionAction) => boolean

/** Một tab của dải Thiết lập: nhãn, đích bấm, và luật "đang sáng" theo đường dẫn + query hiện tại. */
export interface HrSetupTab {
  key: string
  label: string
  to: string
  isActive: (pathname: string, search: URLSearchParams) => boolean
}

/** Nhãn hai tab của màn Chính sách nghỉ phép khi trải phẳng ra dải Thiết lập (nhãn ngắn "Phân bổ" / "Chính sách" của
 *  màn cũ không đứng một mình được giữa chín tab). */
const POLICY_HUB_FLAT_LABELS: Record<LeavePolicyHubTab, string> = {
  assignments: 'Phân bổ chính sách',
  policies: 'Gói chính sách',
}

/** Ba màn của mục "Loại nghỉ và ngày lễ" — luật quyền giữ nguyên như thanh tab con cũ (`leave-section-tabs`). */
const LEAVE_SETUP_SCREENS: { key: string; label: string; path: string; visible: (can: CanFn) => boolean }[] = [
  { key: 'leave-types', label: 'Loại nghỉ', path: appRoutes.hr.leaveTypes, visible: (can) => can('leave_type', 'write') },
  { key: 'holidays', label: 'Lịch ngày lễ', path: appRoutes.hr.holidays, visible: (can) => can('holiday', 'write') },
  //  duoc-CR-715: dùng chung khóa `leave_type` (không thêm khóa).
  { key: 'leave-blocks', label: 'Ngày cấm nghỉ', path: appRoutes.hr.leaveBlocks, visible: (can) => can('leave_type', 'write') },
]

function onPath(pathname: string, path: string): boolean {
  return pathname === path || pathname.startsWith(`${path}/`)
}

/**
 * Dải tab PHẲNG của mục Thiết lập Nhân sự (duoc-CR-753) — một hàng, không tab lồng trong tab (theo cách Frappe HRMS:
 * mỗi danh mục một trang phẳng; chỉ form Cài đặt nhân sự có nhóm ô bên trong).
 *
 * Đi theo thứ tự mục con của `hrSetupNavItem` (cùng luật quyền với menu và hàng rào route), rồi TRẢI hai mục gom nhiều
 * màn: "Chính sách nghỉ phép" → Phân bổ chính sách · Gói chính sách (luật `getVisibleLeavePolicyHubTabs`); "Loại nghỉ và
 * ngày lễ" → Loại nghỉ · Lịch ngày lễ · Ngày cấm nghỉ. Thêm màn cấu hình thì sửa `hr-setup-nav-item.tsx`.
 */
export function buildHrSetupTabs(can: CanFn, navCtx: NavContext = {}): HrSetupTab[] {
  const tabs: HrSetupTab[] = []
  for (const child of visibleNavChildren(hrSetupNavItem, can, navCtx)) {
    if (child.path === appRoutes.hr.leavePolicyAssignments) {
      for (const def of getVisibleLeavePolicyHubTabs(can)) {
        tabs.push({
          key: `policy-hub-${def.key}`,
          label: POLICY_HUB_FLAT_LABELS[def.key],
          to: buildLeavePolicyHubHref(def.key),
          isActive: (pathname, search) => policyHubTabActive(def.key, pathname, search, can),
        })
      }
    } else if (child.path === appRoutes.hr.leaveTypes) {
      for (const screen of LEAVE_SETUP_SCREENS.filter((s) => s.visible(can))) {
        tabs.push({
          key: screen.key,
          label: screen.label,
          to: screen.path,
          isActive: (pathname) => onPath(pathname, screen.path),
        })
      }
    } else {
      const paths = [child.path, ...(child.matchPaths ?? [])]
      tabs.push({
        key: child.path,
        label: child.label,
        to: child.path,
        isActive: (pathname) => paths.some((p) => onPath(pathname, p)),
      })
    }
  }
  return tabs
}

/** Tab nào của màn Chính sách nghỉ phép đang mở: trang gói (`/hr/leave-policies/*`) thuộc Gói chính sách, trang hàng
 *  loạt thuộc Phân bổ, còn màn gộp thì đọc `?tab=` qua đúng luật của màn (`resolveLeavePolicyHubTab`). */
function policyHubTabActive(key: LeavePolicyHubTab, pathname: string, search: URLSearchParams, can: CanFn): boolean {
  if (onPath(pathname, appRoutes.hr.leavePolicies)) return key === 'policies'
  if (onPath(pathname, appRoutes.hr.leavePolicyBulkAssign)) return key === 'assignments'
  if (pathname !== appRoutes.hr.leavePolicyAssignments) return false
  return resolveLeavePolicyHubTab(search.get(LEAVE_POLICY_HUB_TAB_PARAM), can) === key
}
