import { toast } from 'sonner'

import { api } from '@/api/client'
import { askConfirm, askPrompt } from '@/components/confirm-dialog'
import { askNewArticle } from '@/components/create-article-dialog'
import { findNode, type HelpNode } from '@/lib/help-tree'
import type { DropPosition } from '@/lib/help-tree-dnd'

// Thao tác CRUD + sắp xếp bài viết, dùng chung cho bảng cây (/admin) và danh sách bài con (/admin/:id).
// Mọi hàm trả về id/boolean và KHÔNG tự nạp lại cây — nơi gọi tự quyết định lúc nào refresh.

/** Nhãn cấp bậc theo độ sâu trong cây. Cấp 1 và cấp 2 đều gọi chung là "Bài viết". */
export const LEVEL_LABELS = ['Mục gốc', 'Bài viết', 'Bài viết'] as const

export function levelLabel(depth: number): string {
  return LEVEL_LABELS[depth] ?? `Cấp ${depth + 1}`
}

/** Tạo bài viết mới (hỏi tiêu đề + mô tả ngắn + icon). Trả id bài vừa tạo, hoặc null nếu hủy/lỗi. */
export async function createArticle(
  parentId: number | null,
  sortOrder: number,
  depth: number,
): Promise<number | null> {
  const draft = await askNewArticle({
    title: parentId === null ? 'Thêm mục gốc' : `Thêm ${levelLabel(depth).toLowerCase()}`,
    description: 'Mô tả ngắn và icon sẽ hiển thị trên thẻ ở khu người dùng.',
  })
  if (!draft) return null
  try {
    const res = await api.post('/api/v1/help-center', {
      title: draft.title,
      summary: draft.summary,
      icon: draft.icon,
      parent_id: parentId,
      sort_order: sortOrder,
    })
    toast.success('Đã tạo bài viết')
    return res.data.data.id as number
  } catch {
    return null // interceptor đã toast lỗi
  }
}

/** Đổi tiêu đề (hỏi tên mới). Trả true nếu đã đổi. */
export async function renameArticle(node: HelpNode): Promise<boolean> {
  const title = await askPrompt({
    title: 'Đổi tiêu đề',
    message: 'Nhập tiêu đề mới:',
    defaultValue: node.title,
    required: true,
  })
  if (!title || title === node.title) return false
  try {
    await api.put(`/api/v1/help-center/${node.id}`, { title })
    toast.success('Đã đổi tiêu đề')
    return true
  } catch {
    return false
  }
}

/** Tổng số bài trong nhánh, tính cả chính nó — để cảnh báo trước khi xóa. */
function countBranch(node: HelpNode): number {
  return 1 + (node.children || []).reduce((sum, c) => sum + countBranch(c), 0)
}

/** Xóa bài viết CÙNG toàn bộ bài con/cháu bên trong (có xác nhận). */
export async function deleteArticle(node: HelpNode): Promise<boolean> {
  const total = countBranch(node)
  const ok = await askConfirm({
    title: 'Xóa bài viết',
    message: total > 1
      ? `Xóa "${node.title}" sẽ xóa luôn ${total - 1} bài viết con/cháu bên trong `
        + `(tổng ${total} bài). Thao tác này không thể hoàn tác.`
      : `Xóa "${node.title}"? Thao tác này không thể hoàn tác.`,
    confirmText: 'Xóa',
  })
  if (!ok) return false
  try {
    await api.delete(`/api/v1/help-center/${node.id}`)
    toast.success('Đã xóa bài viết')
    return true
  } catch {
    return false
  }
}

/** Chuyển bài viết sang thư mục cha khác. parentId = null -> đưa về mục gốc. */
export async function moveArticle(nodeId: number, parentId: number | null): Promise<boolean> {
  try {
    await api.put(`/api/v1/help-center/${nodeId}`, { parent_id: parentId })
    toast.success('Đã chuyển bài viết')
    return true
  } catch {
    return false // interceptor đã toast lỗi (vd chuyển vào chính bài con của nó)
  }
}

/**
 * Kéo-thả 1 bài viết tới vị trí mới: đổi thứ tự trong cùng mục HOẶC chuyển sang mục cha khác.
 *
 * Gọi sau khi `canDrop` đã xác nhận nước thả hợp lệ. Trả false khi không có gì thay đổi.
 * Cách đánh lại sort_order giống `reorderSibling`: dữ liệu cũ có thể để 0 hết nên phải
 * ghi lại theo đúng vị trí cho MỌI phần tử bị lệch.
 */
export async function dropArticle(
  tree: HelpNode[],
  dragId: number,
  targetId: number,
  position: DropPosition,
): Promise<boolean> {
  const drag = findNode(tree, dragId)
  const target = findNode(tree, targetId)
  if (!drag || !target) return false

  const newParentId = position === 'inside' ? target.id : target.parent_id
  const newParent = newParentId !== null ? findNode(tree, newParentId) : null

  // Danh sách anh em mới, đã bỏ chính node đang kéo ra
  const siblings = (newParent ? newParent.children || [] : tree).filter((n) => n.id !== dragId)

  let index = siblings.length
  if (position !== 'inside') {
    const at = siblings.findIndex((n) => n.id === targetId)
    index = position === 'before' ? at : at + 1
  }

  const next = [...siblings.slice(0, index), drag, ...siblings.slice(index)]

  const payloads = next
    .map((node, i) => ({ node, i }))
    .filter(({ node, i }) =>
      node.sort_order !== i || (node.id === dragId && node.parent_id !== newParentId))
    .map(({ node, i }) => ({
      id: node.id,
      // Chỉ node đang kéo mới đổi cha; các node còn lại chỉ cần đánh lại thứ tự
      body: node.id === dragId ? { parent_id: newParentId, sort_order: i } : { sort_order: i },
    }))

  if (payloads.length === 0) return false

  try {
    await Promise.all(
      payloads.map(({ id, body }) =>
        api.put(`/api/v1/help-center/${id}`, body, { _silent: true } as any),
      ),
    )
    toast.success(
      drag.parent_id === newParentId
        ? 'Đã đổi thứ tự hiển thị'
        : `Đã chuyển "${drag.title}" sang ${newParent ? `"${newParent.title}"` : 'mục gốc'}`,
    )
    return true
  } catch {
    toast.error('Không chuyển được bài viết, vui lòng thử lại')
    return false
  }
}

/**
 * Đổi vị trí 1 bài trong danh sách anh em (lên/xuống).
 *
 * Dữ liệu cũ có thể để sort_order = 0 hết, nên sau khi hoán đổi phải ghi lại
 * sort_order theo đúng vị trí cho MỌI phần tử bị lệch — nếu chỉ swap 2 giá trị 0 thì không đổi gì.
 */
export async function reorderSibling(
  siblings: HelpNode[],
  index: number,
  direction: -1 | 1,
): Promise<boolean> {
  const target = index + direction
  if (target < 0 || target >= siblings.length) return false

  const next = [...siblings]
  ;[next[index], next[target]] = [next[target], next[index]]

  const changed = next
    .map((node, i) => ({ node, i }))
    .filter(({ node, i }) => node.sort_order !== i)

  if (changed.length === 0) return false

  try {
    await Promise.all(
      changed.map(({ node, i }) =>
        api.put(`/api/v1/help-center/${node.id}`, { sort_order: i }, { _silent: true } as any),
      ),
    )
    return true
  } catch {
    toast.error('Không đổi được thứ tự, vui lòng thử lại')
    return false
  }
}
