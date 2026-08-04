import { toast } from 'sonner'

import { api } from '@/api/client'
import { askConfirm, askPrompt } from '@/components/confirm-dialog'
import type { HelpNode } from '@/lib/help-tree'

// Thao tác CRUD + sắp xếp bài viết, dùng chung cho bảng cây (/admin) và danh sách bài con (/admin/:id).
// Mọi hàm trả về id/boolean và KHÔNG tự nạp lại cây — nơi gọi tự quyết định lúc nào refresh.

/** Nhãn cấp bậc theo độ sâu trong cây. */
export const LEVEL_LABELS = ['Mục gốc', 'Bài viết', 'Bài chi tiết'] as const

export function levelLabel(depth: number): string {
  return LEVEL_LABELS[depth] ?? `Cấp ${depth + 1}`
}

/** Tạo bài viết mới (hỏi tiêu đề). Trả id bài vừa tạo, hoặc null nếu hủy/lỗi. */
export async function createArticle(
  parentId: number | null,
  sortOrder: number,
  depth: number,
): Promise<number | null> {
  const title = await askPrompt({
    title: parentId === null ? 'Thêm mục gốc' : `Thêm ${levelLabel(depth).toLowerCase()}`,
    message: 'Nhập tiêu đề cho bài viết mới:',
    placeholder: 'VD: Hướng dẫn tạo Yêu cầu mua hàng',
    required: true,
  })
  if (!title) return null
  try {
    const res = await api.post('/api/v1/help-center', {
      title, parent_id: parentId, sort_order: sortOrder,
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

/** Xóa bài viết (có xác nhận). Backend chặn nếu còn bài con. */
export async function deleteArticle(node: HelpNode): Promise<boolean> {
  const childCount = node.children?.length || 0
  const ok = await askConfirm({
    title: 'Xóa bài viết',
    message: childCount
      ? `"${node.title}" đang chứa ${childCount} bài viết con. Phải xóa hết bài con trước.`
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
