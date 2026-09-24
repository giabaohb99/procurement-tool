import { matchesVietnamese } from '@/shared/utils/vn-text'
import type { DocFolderTreeNode } from '../types/document-folder'

/**
 * id của mọi TỔ TIÊN của các thư mục khớp từ khóa — dùng để tự MỞ đủ nhánh
 * chứa kết quả tìm (`folder-tree-panel.tsx`). Đọc thẳng `path` vật hóa
 * (`/1/5/9/`, tự gồm id của chính nó ở cuối) thay vì bò theo `parent_id`.
 *
 * Hàm THUẦN — tách khỏi component để test không cần dựng `TreeView`/DOM.
 */
export function ancestorIdsOfMatches(
  rows: readonly Pick<DocFolderTreeNode, 'id' | 'path'>[],
  matchedIds: ReadonlySet<string | number>,
): number[] {
  const byId = new Map(rows.map((row) => [row.id, row]))
  const ancestorIds = new Set<number>()
  for (const id of matchedIds) {
    const row = byId.get(Number(id))
    if (!row?.path) continue
    for (const part of row.path.split('/').filter(Boolean)) {
      const ancestorId = Number(part)
      if (ancestorId !== row.id) ancestorIds.add(ancestorId)
    }
  }
  return Array.from(ancestorIds)
}

/** Nhãn tên thư mục CÓ KHỚP từ khóa (bỏ dấu) — vỏ mỏng cho `filterTree`. */
export function folderNameMatches(name: string, keyword: string): boolean {
  return matchesVietnamese(name, keyword)
}
