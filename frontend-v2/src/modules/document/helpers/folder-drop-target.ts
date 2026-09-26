import { FOLDER_ACCESS_LEVEL } from '../types/document-folder'

/**
 * Cấp SÂU NHẤT một cây thư mục văn bản được phép chạm tới, tính cả gốc — PHẢI
 * khớp `MAX_DEPTH` ở `backend/.../doc_catalog/folder_constants.py`. Mở từ 7
 * lên 100 ngày 26/09/2026 (ngang trần Google Drive).
 */
export const MAX_FOLDER_DEPTH = 100

export interface FolderDragSource {
  id: number
  /** `/1/5/9/` — vật hóa, TỰ GỒM id của chính nó ở cuối (đúng quy ước backend). */
  path: string
  depth: number
  /**
   * Cấp SÂU NHẤT đang có trong nhánh đang kéo, tính cả chính nó — dùng để
   * chặn "vượt trần cấp" SAU KHI chuyển cha, không chỉ xét mỗi bản thân node kéo.
   * Bỏ trống = coi nhánh chỉ có một cấp (node kéo không có con).
   */
  deepestDescendantDepth?: number
}

export interface FolderDropCandidate {
  id: number
  path: string
  depth: number
  /** Mức quyền hiệu lực CỦA NGƯỜI ĐANG KÉO trên chính thư mục đích này. */
  myLevel: number
}

/**
 * Thư mục ĐÍCH có nhận được thư mục đang kéo hay không — hàm THUẦN, không đọc
 * API/state nào, để `TreeView` (native DnD) và hộp thoại «Chuyển tới…» dùng
 * chung đúng MỘT luật thay vì hai bản chép lệch nhau.
 *
 * Bốn điều kiện: chính nó · con cháu của chính nó · vượt {@link MAX_FOLDER_DEPTH}
 * cấp sau khi chuyển · mức quyền của người kéo trên đích < Đóng góp. Điều kiện
 * «khác pháp nhân» đã BỎ 24/09/2026 (đại ca chốt: chuyển đâu tùy người dùng).
 */
export function isValidFolderDropTarget(
  source: FolderDragSource,
  target: FolderDropCandidate,
): boolean {
  if (target.id === source.id) return false
  //  `target.path` bắt đầu bằng `source.path` nghĩa là target CHÍNH LÀ source
  //  hoặc là con cháu của nó (path tự gồm id chính nó ở cuối) — thả vào đó là
  //  tự làm cha của chính mình hoặc tạo vòng lặp.
  if (target.path.startsWith(source.path)) return false

  const deepest = source.deepestDescendantDepth ?? source.depth
  const depthAfterMove = target.depth + 1 + (deepest - source.depth)
  if (depthAfterMove > MAX_FOLDER_DEPTH) return false

  if (target.myLevel < FOLDER_ACCESS_LEVEL.contribute) return false

  return true
}

export interface FolderReorderSource {
  id: number
  parentId: number
}

export interface FolderReorderCandidate {
  id: number
  parentId: number
  /** Mức quyền hiệu lực CỦA NGƯỜI ĐANG KÉO trên thư mục CHA CHUNG (không phải trên chính dòng đích). */
  parentMyLevel: number
}

/**
 * Thả TRƯỚC/SAU một dòng (đổi THỨ TỰ, không đổi cha) có hợp lệ không — hàm
 * THUẦN, cùng vai trò với {@link isValidFolderDropTarget} nhưng luật khác hẳn:
 * backend `_ensure_reorder_access` đòi quyền QUẢN LÝ trên THƯ MỤC CHA CHUNG
 * (không phải trên chính dòng đích như đổi cha), và chỉ nhận anh em CÙNG một
 * cha — đổi cha phải đi đường kéo-thả-vào hoặc hộp thoại «Chuyển tới…».
 */
export function isValidFolderReorderTarget(
  source: FolderReorderSource,
  target: FolderReorderCandidate,
): boolean {
  if (target.id === source.id) return false
  if (target.parentId !== source.parentId) return false
  return target.parentMyLevel >= FOLDER_ACCESS_LEVEL.manage
}

/**
 * Thứ tự MỚI của các anh em cùng cha sau khi kéo `sourceId` tới trước/sau
 * `targetId` — hàm THUẦN, chỉ đổi VỊ TRÍ trong mảng, không đụng `sort_order`
 * thật (nơi gọi tự đánh số lại theo CHỈ SỐ của mảng trả về, xem
 * `use-folder-drag-move.ts`).
 *
 * `orderedSiblingIds` phải là thứ tự HIỂN THỊ hiện tại (đã sắp theo
 * `sort_order` rồi tên, cùng luật `compareSiblings` của `build-folder-tree.ts`)
 * — kể cả `sourceId`. Thiếu `sourceId`/`targetId` trong mảng, hoặc kéo vào
 * chính nó, thì trả nguyên mảng gốc (không đoán, không nổ) — nơi gọi tự biết
 * không có gì đổi khi so mảng ra với mảng vào.
 */
export function reorderSiblingIds(
  orderedSiblingIds: readonly number[],
  sourceId: number,
  targetId: number,
  position: 'before' | 'after',
): number[] {
  if (sourceId === targetId) return [...orderedSiblingIds]
  if (!orderedSiblingIds.includes(sourceId) || !orderedSiblingIds.includes(targetId)) {
    return [...orderedSiblingIds]
  }

  const withoutSource = orderedSiblingIds.filter((id) => id !== sourceId)
  const targetIndex = withoutSource.indexOf(targetId)
  const insertAt = position === 'before' ? targetIndex : targetIndex + 1
  withoutSource.splice(insertAt, 0, sourceId)
  return withoutSource
}

/**
 * Cấp SÂU NHẤT trong nhánh của `source` (kể cả chính nó), đọc từ danh sách
 * PHẲNG `/tree` đã nạp — dùng để lấp `deepestDescendantDepth` ở trên khi kéo
 * một thư mục CÓ CON (dòng cháu sâu hơn phải chặn "vượt 6 cấp" cùng lúc,
 * không chỉ tính theo cấp của chính node đang kéo).
 */
export function deepestDescendantDepth(
  rows: readonly { id: number; path: string; depth: number }[],
  source: { id: number; path: string; depth: number },
): number {
  let max = source.depth
  for (const row of rows) {
    if (row.id !== source.id && row.path.startsWith(source.path) && row.depth > max) {
      max = row.depth
    }
  }
  return max
}
