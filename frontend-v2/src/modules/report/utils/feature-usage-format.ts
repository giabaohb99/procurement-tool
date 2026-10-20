import { UI_ACTION, UI_FORM } from '@/shared/constants/statuses'

import type { FeatureRow } from '../types/feature-usage'
import { labelRouteInApp } from './usage-route-label'

const labelOf = (options: readonly { value: string; label: string }[], code: number) =>
  options.find((o) => o.value === String(code))?.label ?? `Mã ${code}`

export const actionName = (code: number) => labelOf(UI_ACTION, code)
export const formName = (code: number) => labelOf(UI_FORM, code)

/** «Phân hệ › Màn» của một route mẫu; route không nhận ra hiện nguyên route. */
export function screenName(route: string): string {
  const l = labelRouteInApp(route)
  return l.module ? `${l.module} › ${l.screen}` : l.screen
}

/** Phần trăm người dùng trên số người hoạt động; mẫu số 0 → null (không hiện 0%). */
export function userShare(users: number, activeUsers: number): number | null {
  return activeUsers > 0 ? Math.min(1, users / activeUsers) : null
}

/** Tỷ lệ bỏ dở = lượt bỏ / lượt mở biểu mẫu; chưa ai mở → null. */
export function abandonRate(row: Pick<FeatureRow, 'uses' | 'abandons'>): number | null {
  return row.uses > 0 ? Math.min(1, row.abandons / row.uses) : null
}

/** Chức năng/biểu mẫu CHƯA AI DÙNG: các mã trong danh mục trừ các mã đã thấy (backend trả sẵn). */
export function unusedNames(codes: number[], name: (code: number) => string): string[] {
  return codes.map(name).sort((a, b) => a.localeCompare(b, 'vi'))
}
