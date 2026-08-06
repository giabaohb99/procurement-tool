import { toast } from 'sonner'

import { api } from '@/api/client'

// Cấu hình hiển thị trang chủ khu người dùng — 4 khung CỐ ĐỊNH đã seed sẵn ở backend
// (`tab_help_home_section`), chỉ đổi được tiêu đề / ẩn-hiện / thứ tự, KHÔNG thêm-xóa khung.
// Hai khung `quick_start` và `categories` gắn thêm được danh sách bài viết (`tab_help_home_item`).

export const HOME_SECTION = {
  QUICK: 'quick_start',
  CATEGORIES: 'categories',
  FAQ: 'faq',
  TIPS: 'tips',
} as const

/**
 * Loại phần tử mỗi khung nhận — backend quyết định (`item_kind` trong response) và chặn thẳng
 * (400) nếu gửi sai loại:
 *   article -> bài viết HDSD        (Bắt đầu ngay · Các Phân hệ)
 *   faq     -> câu hỏi thường gặp   (Không tìm thấy điều bạn cần?)
 *   custom  -> thẻ tự do nhập tay   (Mẹo tra cứu)
 */
export type HomeItemKind = 'article' | 'faq' | 'custom'

export interface HelpHomeItem {
  id: number
  article_id: number | null
  article_title: string | null
  article_summary: string | null
  article_icon: string | null
  faq_id: number | null
  faq_question: string | null
  /** Thẻ tự do: tiêu đề · mô tả · slug icon (xem lib/help-icons.ts). */
  title: string | null
  description: string | null
  icon: string | null
  /** Ảnh minh họa góc phải của tile — chỉ khung "Bắt đầu ngay" dùng. */
  background_image: string | null
  /** Slug nền gradient (xem lib/help-home-skins.ts), backend chỉ lưu chuỗi. */
  gradient: string | null
  sort_order: number
}

export interface HelpHomeSection {
  id: number
  key: string
  title: string
  is_visible: boolean
  sort_order: number
  item_kind: HomeItemKind
  items: HelpHomeItem[]
}

export interface HelpHomeItemPayload {
  article_id?: number
  faq_id?: number
  title?: string | null
  description?: string | null
  icon?: string | null
  gradient?: string | null
  background_image?: string | null
  sort_order?: number
}

export async function fetchHomeSections(): Promise<HelpHomeSection[]> {
  const res = await api.get('/api/v1/help-center/home')
  return res.data.data
}

export async function updateHomeSection(
  sectionId: number,
  data: { title?: string; is_visible?: boolean; sort_order?: number },
  silent = false,
): Promise<boolean> {
  try {
    await api.put(`/api/v1/help-center/home/sections/${sectionId}`, data,
      silent ? ({ _silent: true } as never) : undefined)
    return true
  } catch {
    return false // interceptor đã toast lỗi (trừ khi silent)
  }
}

export async function addHomeItem(
  sectionId: number,
  data: HelpHomeItemPayload,
): Promise<boolean> {
  try {
    await api.post(`/api/v1/help-center/home/sections/${sectionId}/items`, data)
    toast.success('Đã thêm vào khung')
    return true
  } catch {
    return false
  }
}

export async function updateHomeItem(
  itemId: number,
  data: HelpHomeItemPayload,
  silent = false,
): Promise<boolean> {
  try {
    await api.put(`/api/v1/help-center/home/items/${itemId}`, data,
      silent ? ({ _silent: true } as never) : undefined)
    return true
  } catch {
    return false
  }
}

export async function deleteHomeItem(itemId: number): Promise<boolean> {
  try {
    await api.delete(`/api/v1/help-center/home/items/${itemId}`)
    toast.success('Đã bỏ bài viết khỏi khung')
    return true
  } catch {
    return false
  }
}

/**
 * Đổi thứ tự 1 phần tử trong danh sách (khung hoặc bài trong khung).
 * Ghi lại sort_order cho MỌI phần tử bị lệch — dữ liệu cũ có thể để 0 hết nên chỉ hoán đổi
 * hai giá trị 0 sẽ không đổi gì (giống reorderSibling ở help-article-actions).
 */
export async function reorderHome<T extends { id: number; sort_order: number }>(
  list: T[],
  index: number,
  direction: -1 | 1,
  save: (id: number, sortOrder: number) => Promise<boolean>,
): Promise<boolean> {
  const target = index + direction
  if (target < 0 || target >= list.length) return false

  const next = [...list]
  ;[next[index], next[target]] = [next[target], next[index]]

  const changed = next
    .map((item, i) => ({ item, i }))
    .filter(({ item, i }) => item.sort_order !== i)

  if (changed.length === 0) return false

  const results = await Promise.all(changed.map(({ item, i }) => save(item.id, i)))
  if (results.some((ok) => !ok)) {
    toast.error('Không đổi được thứ tự, vui lòng thử lại')
    return false
  }
  return true
}
