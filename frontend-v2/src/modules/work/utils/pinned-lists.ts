/**
 * Ghim dự án hay dùng lên đầu thanh bên (A-05).
 *
 * Lưu THEO NGƯỜI DÙNG ở `tab_user_preference` (khóa {@link PINNED_LISTS_PREF_KEY}) chứ
 * không ở `localStorage`: ghim là thói quen của một người, đổi máy vẫn phải còn.
 * Giá trị là chuỗi id cách nhau dấu phẩy — bảng tùy chọn chỉ nhận chuỗi.
 */

export const PINNED_LISTS_PREF_KEY = 'work_pinned_lists'

/** Ghim quá nhiều thì khu ghim thành bản sao của cả cây — chặn ở mức đủ dùng. */
export const MAX_PINNED_LISTS = 20

/** Chuỗi lưu -> mảng id. Bỏ phần tử rác, trùng; giữ nguyên thứ tự ghim. */
export function parsePinnedLists(raw: string | undefined | null): number[] {
  const seen = new Set<number>()
  for (const part of (raw ?? '').split(',')) {
    const id = Number(part.trim())
    if (Number.isInteger(id) && id > 0) seen.add(id)
  }
  return [...seen].slice(0, MAX_PINNED_LISTS)
}

export function serializePinnedLists(ids: number[]): string {
  return ids.join(',')
}

/** Bật/tắt ghim: ghim mới đứng CUỐI khu ghim; đủ trần thì không ghim thêm (trả nguyên). */
export function togglePinned(ids: number[], id: number): number[] {
  if (ids.includes(id)) return ids.filter((x) => x !== id)
  if (ids.length >= MAX_PINNED_LISTS) return ids
  return [...ids, id]
}

interface SidebarNode<L> {
  lists: L[]
  children: SidebarNode<L>[]
}

/** Mọi dự án trong cây thanh bên (nhóm → nhóm con → dự án, cộng dự án đứng lẻ), phẳng ra một mảng. */
export function collectSidebarLists<L extends { id: number }>(
  groups: SidebarNode<L>[],
  loose: L[],
): L[] {
  const out: L[] = [...loose]
  const walk = (nodes: SidebarNode<L>[]) => {
    for (const node of nodes) {
      out.push(...node.lists)
      walk(node.children)
    }
  }
  walk(groups)
  return out
}
