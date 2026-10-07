import { matchesVietnamese } from '@/shared/utils/vn-text'

import type { LaborContractPlaceholder } from '../types/labor-contract'

/** Chuỗi người soạn mẫu gõ vào Word: `{{ ho_ten }}`. */
export function formatPlaceholderToken(key: string): string {
  return `{{ ${key} }}`
}

/**
 * Gom biến theo `group`, giữ thứ tự nhóm xuất hiện đầu tiên và thứ tự biến backend trả.
 * Danh mục do backend giữ — hàm này KHÔNG lọc, KHÔNG sắp lại, và chịu được `null`.
 */
export function groupPlaceholders(
  items: readonly LaborContractPlaceholder[] | null | undefined,
): { group: string; items: LaborContractPlaceholder[] }[] {
  const groups = new Map<string, LaborContractPlaceholder[]>()
  for (const item of items ?? []) {
    const name = item.group || 'Khác'
    const list = groups.get(name)
    if (list) list.push(item)
    else groups.set(name, [item])
  }
  return [...groups].map(([group, list]) => ({ group, items: list }))
}

/**
 * Lọc biến theo ô tìm của khung «Chèn biến» (duoc-CR-606): khớp mã biến HOẶC nhãn, KHÔNG phân biệt
 * hoa thường lẫn dấu — gõ «luong» phải ra «Lương cơ bản». Chuỗi rỗng / toàn khoảng trắng = giữ hết.
 */
export function filterPlaceholders(
  items: readonly LaborContractPlaceholder[] | null | undefined,
  query: string,
): LaborContractPlaceholder[] {
  return (items ?? []).filter((item) => matchesVietnamese([item.key, item.label], query))
}
