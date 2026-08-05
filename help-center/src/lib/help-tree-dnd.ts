import { articleHeight, findNode, findPath, type HelpNode } from '@/lib/help-tree'

// Logic THUẦN cho thao tác kéo-thả bảng cây bài viết (không gọi API, không đụng DOM):
// suy ra vị trí thả từ toạ độ chuột và kiểm tra nước thả có hợp lệ không.
// Phần ghi xuống server nằm ở lib/help-article-actions.ts (dropArticle).

/** Cấp sâu nhất được phép (0-based): 0 = Mục gốc · 1 = Bài viết · 2 = Bài chi tiết. */
export const MAX_DEPTH = 2

export type DropPosition = 'before' | 'after' | 'inside'

export interface DropTarget {
  id: number
  position: DropPosition
}

/** Ngưỡng (theo tỉ lệ chiều cao dòng) chia vùng chèn-trước / thả-vào-trong / chèn-sau. */
const EDGE_RATIO = 0.3

/**
 * Vị trí thả suy từ toạ độ chuột trong dòng:
 * hai mép trên/dưới = chèn trước/sau (cùng cấp), khoảng giữa = thả VÀO TRONG (thành bài con).
 */
export function positionFromPointer(
  rect: DOMRect,
  clientY: number,
  allowInside: boolean,
): DropPosition {
  const ratio = rect.height > 0 ? (clientY - rect.top) / rect.height : 0
  if (!allowInside) return ratio < 0.5 ? 'before' : 'after'
  if (ratio < EDGE_RATIO) return 'before'
  if (ratio > 1 - EDGE_RATIO) return 'after'
  return 'inside'
}

/** Độ sâu của node trong cây (0 = mục gốc). -1 nếu không tìm thấy. */
export function depthOf(tree: HelpNode[], id: number): number {
  const path = findPath(tree, id)
  return path ? path.length - 1 : -1
}

/**
 * Nước thả có hợp lệ không.
 *
 * Chặn 3 trường hợp: thả vào chính nó · thả vào bài con/cháu của nó (tạo vòng lặp cây) ·
 * thả làm cấu trúc vượt quá 3 cấp (tính cả chiều cao nhánh đang kéo, không chỉ mỗi node).
 */
export function canDrop(
  tree: HelpNode[],
  dragId: number,
  targetId: number,
  position: DropPosition,
): boolean {
  if (dragId === targetId) return false

  const drag = findNode(tree, dragId)
  if (!drag || !findNode(tree, targetId)) return false

  // Target nằm trong nhánh con của node đang kéo -> chuyển vào sẽ tạo vòng lặp
  if (findNode(drag.children || [], targetId)) return false

  const targetDepth = depthOf(tree, targetId)
  if (targetDepth < 0) return false

  // 'inside' -> cha mới là target; 'before'/'after' -> cha mới là cha của target
  const newParentDepth = position === 'inside' ? targetDepth : targetDepth - 1
  return newParentDepth + 1 + articleHeight(drag) <= MAX_DEPTH
}
