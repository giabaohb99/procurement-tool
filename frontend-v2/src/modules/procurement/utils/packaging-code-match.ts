/**
 * duoc-CR-784 — tìm mã bao bì kiểu bản mẫu (`smartMatcher` của `Bao cao gia NVL san xuat`).
 *
 * Gõ TÊN NHÓM ("chai", "nắp", "nhãn, thùng") = lọc theo nhóm — để bấm "Chọn tất cả" là chọn cả nhóm.
 * Còn lại = tìm không dấu, mọi từ phải có mặt trong mã / tên / nhóm ("nắp 0085" ra NAP0085).
 * Nhóm lấy từ chính dữ liệu (`item_group` của danh mục sản phẩm), không gõ cứng danh sách.
 */
import { PACKAGING_ROLE } from '@/shared/constants/statuses'
import { stripDiacritics } from '@/shared/utils/vn-text'

import type { PackagingCodeOption } from '../types/packaging-cost-types'

/** Trần số mã một lượt tính (`POST /impact` nhận `codes: str[1..500]`). */
export const PACKAGING_MAX_CODES = 500

const fold = (text: string) => stripDiacritics(text).trim()

/**
 * Một cụm chữ ứng với nhóm nào: trùng hẳn tên nhóm trước ("nhan" = Nhãn, không phải Nhãn thùng), rồi
 * mới tới chữ đầu của tên nhóm ("nhan" không lấy nhầm vì đã khớp hẳn ở bước một).
 */
function resolveGroup(term: string, groups: readonly string[]): string | null {
  const exact = groups.find((group) => fold(group) === term)
  if (exact) return exact
  return groups.find((group) => fold(group).split(/\s+/)[0] === term) ?? null
}

/** Trả hàm lọc cho từ khóa `query` trên tập nhóm `groups`. Từ khóa rỗng = lấy hết. */
export function buildPackagingCodeMatcher(
  query: string,
  groups: readonly string[],
): (option: PackagingCodeOption) => boolean {
  const folded = fold(query)
  if (!folded) return () => true

  const parts = folded
    .split(',')
    .map((part) => part.trim())
    .filter(Boolean)
  const matchedGroups = parts.map((part) => resolveGroup(part, groups))
  if (matchedGroups.length > 0 && matchedGroups.every(Boolean)) {
    const wanted = new Set(matchedGroups)
    return (option) => wanted.has(option.group)
  }

  const terms = folded.split(/[\s,]+/).filter(Boolean)
  return (option) => {
    const haystack = fold(`${option.code} ${option.name} ${option.group}`)
    return terms.every((term) => haystack.includes(term))
  }
}

/**
 * Thứ tự bày trong ô chọn: nhóm thành phần của định mức trước (chai → nắp → nhãn → nhãn thùng →
 * thùng, đúng thứ tự cột của bảng sản phẩm), nhóm khác sau, cùng nhóm thì theo mã.
 */
const GROUP_ORDER = ['chai', 'nap', 'nhan', 'nhan thung', 'thung']

export function sortPackagingCodeOptions(
  options: readonly PackagingCodeOption[],
): PackagingCodeOption[] {
  const rank = (group: string) => {
    const index = GROUP_ORDER.indexOf(fold(group))
    return index < 0 ? GROUP_ORDER.length : index
  }
  return [...options].sort((a, b) => rank(a.group) - rank(b.group) || a.code.localeCompare(b.code))
}

/** Các nhóm có mặt trong danh sách, giữ thứ tự của `sortPackagingCodeOptions`. */
export function collectPackagingGroups(options: readonly PackagingCodeOption[]): string[] {
  return [
    ...new Set(
      sortPackagingCodeOptions(options)
        .map((option) => option.group)
        .filter(Boolean),
    ),
  ]
}

/**
 * Nhóm dùng để HIỂU từ khóa: nhóm có trong dữ liệu + năm tên vai trò định mức (bộ mã sinh TS). Thêm tên vai
 * trò để gõ "thùng" luôn được hiểu là nhóm Thùng — kể cả khi chưa mã thùng nào vào định mức (dữ liệu
 * DATA_CHAI hiện chưa có cột thùng, Q6); không có thì từ khóa rơi về tìm chữ và ra nhầm cả trăm mã Nhãn
 * thùng (tên nhóm của chúng chứa chữ "thùng").
 */
export function collectSearchGroups(options: readonly PackagingCodeOption[]): string[] {
  return [
    ...new Set([...PACKAGING_ROLE.map((role) => role.label), ...collectPackagingGroups(options)]),
  ]
}
