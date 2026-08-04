import { toast } from 'sonner'

import { api } from '@/api/client'
import { askConfirm } from '@/components/confirm-dialog'

// Câu hỏi thường gặp — dùng chung quyền `help_article` với bài viết hướng dẫn.

export interface Faq {
  id: number
  question: string
  answer: string
  sort_order: number
  is_active: boolean
}

/** activeOnly = true: bỏ câu đang ẩn (trang người dùng). */
export async function fetchFaqs(activeOnly = false): Promise<Faq[]> {
  const res = await api.get('/api/v1/faq', { params: { active_only: activeOnly } })
  return res.data.data
}

export async function createFaq(data: Partial<Faq>): Promise<boolean> {
  try {
    await api.post('/api/v1/faq', data)
    toast.success('Đã thêm câu hỏi')
    return true
  } catch {
    return false // interceptor đã toast lỗi
  }
}

export async function updateFaq(id: number, data: Partial<Faq>, silent = false): Promise<boolean> {
  try {
    await api.put(`/api/v1/faq/${id}`, data, { _silent: silent } as any)
    if (!silent) toast.success('Đã cập nhật câu hỏi')
    return true
  } catch {
    return false
  }
}

export async function deleteFaq(faq: Faq): Promise<boolean> {
  const ok = await askConfirm({
    title: 'Xóa câu hỏi',
    message: `Xóa "${faq.question}"? Thao tác này không thể hoàn tác.`,
    confirmText: 'Xóa',
  })
  if (!ok) return false
  try {
    await api.delete(`/api/v1/faq/${faq.id}`)
    toast.success('Đã xóa câu hỏi')
    return true
  } catch {
    return false
  }
}

/**
 * Đổi vị trí 1 câu hỏi (lên/xuống).
 * Ghi lại sort_order theo đúng vị trí cho mọi phần tử bị lệch — dữ liệu mới đều để 0
 * nên nếu chỉ hoán đổi 2 giá trị 0 thì sẽ không đổi gì.
 */
export async function reorderFaq(list: Faq[], index: number, direction: -1 | 1): Promise<boolean> {
  const target = index + direction
  if (target < 0 || target >= list.length) return false

  const next = [...list]
  ;[next[index], next[target]] = [next[target], next[index]]

  const changed = next
    .map((faq, i) => ({ faq, i }))
    .filter(({ faq, i }) => faq.sort_order !== i)

  if (changed.length === 0) return false

  try {
    await Promise.all(changed.map(({ faq, i }) => updateFaq(faq.id, { sort_order: i }, true)))
    return true
  } catch {
    toast.error('Không đổi được thứ tự, vui lòng thử lại')
    return false
  }
}
