/**
 * duoc-CR-784 — ghép chữ hiển thị cho mã cảnh báo / vai trò thành phần / xu hướng của cụm Giá bao bì.
 *
 * Nhãn lấy từ bộ mã SINH TỰ ĐỘNG (`shared/constants/statuses.ts`, nguồn
 * `backend/app/core/packaging_price_codes.py`) — không viết tay danh sách. Mã lạ (máy chủ mới hơn giao
 * diện) rơi về "Mã n" chứ không thành ô trống.
 */
import {
  labelOf,
  PACKAGING_COST_TREND,
  PACKAGING_COST_WARNING,
  PACKAGING_ROLE,
  type StatusOption,
} from '@/shared/constants/statuses'

import type { PackagingWarning } from '../types/packaging-cost-types'

function labelOrFallback(
  options: readonly StatusOption[],
  code: number | null | undefined,
): string {
  if (code == null) return ''
  return labelOf(options, String(code)) || `Mã ${code}`
}

/** Nhãn vai trò thành phần (Chai, Nắp, Nhãn, Nhãn thùng, Thùng). */
export function packagingRoleLabel(role: number | null | undefined): string {
  return labelOrFallback(PACKAGING_ROLE, role)
}

export function costTrendLabel(trend: number | null | undefined): string {
  return labelOrFallback(PACKAGING_COST_TREND, trend)
}

/** Máy chủ có chỗ gửi mã trần, có chỗ gửi `{kind, role}` — quy về một khuôn. */
export function normalizeWarnings(
  warnings: readonly (number | PackagingWarning)[] | null | undefined,
): PackagingWarning[] {
  return (warnings ?? []).map((item) => (typeof item === 'number' ? { kind: item } : item))
}

/** Một cảnh báo thành chữ; gắn với thành phần thì kèm tên thành phần ("Thiếu giá thành phần: Nắp"). */
export function packagingWarningText(warning: PackagingWarning): string {
  const kind = labelOrFallback(PACKAGING_COST_WARNING, warning.kind)
  return warning.role ? `${kind}: ${packagingRoleLabel(warning.role)}` : kind
}

/** Cột Ghi chú: mọi cảnh báo nối bằng "; ", bỏ câu trùng. */
export function joinPackagingWarnings(
  warnings: readonly (number | PackagingWarning)[] | null | undefined,
): string {
  return [...new Set(normalizeWarnings(warnings).map(packagingWarningText))].join('; ')
}
