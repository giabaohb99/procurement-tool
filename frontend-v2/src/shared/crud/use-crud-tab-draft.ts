import { createContext, useCallback, useContext, useState } from 'react'

/**
 * BẢN NHÁP CỦA TAB CON sống qua lượt đổi tab (review M4 của duoc-CR-717).
 *
 * Radix hủy mount `TabsContent` của tab ẩn, nên thẻ con giữ bản nháp bằng `useState` (dòng của chính sách
 * nghỉ phép, hạn mức theo nhóm của loại nghỉ…) MẤT SẠCH khi người dùng sang tab "Thông tin" xem lại một ô
 * rồi quay về — không cảnh báo, nút "Lưu …" của thẻ lại xám như chưa sửa gì. Bật `forceMount` cho mọi tab
 * thì tab nào cũng gọi API ngay lúc mở trang, nên giữ nháp Ở TRÊN tab thay vì giữ tab sống.
 *
 * `CrudDetailPage` bọc cả trang bằng `CrudTabDraftProvider` (khóa theo `:id`): rời trang hay sang bản ghi
 * khác là bản nháp đi theo — chỉ đổi TAB mới giữ. Thẻ con gọi `useCrudTabDraft(khóa)` thay cho `useState`;
 * khóa nên kèm loại + id bản ghi (`policy-lines:8`). Dựng ngoài provider (bài kiểm dựng thẻ đứng riêng) thì
 * hook rơi về state cục bộ, hành vi y như `useState`.
 */
export interface CrudTabDraftStore {
  drafts: Record<string, unknown>
  setDraft: (key: string, value: unknown) => void
}

export const CrudTabDraftContext = createContext<CrudTabDraftStore | null>(null)

/**
 * `[draft, setDraft]` như `useState<T | null>(null)` — `null` = chưa đụng gì (hiện bản của máy chủ).
 * Trong `CrudTabDraftProvider` thì bản nháp sống qua lượt đổi tab.
 */
export function useCrudTabDraft<T>(key: string): [T | null, (value: T | null) => void] {
  const store = useContext(CrudTabDraftContext)
  const [local, setLocal] = useState<T | null>(null)
  const storeSet = store?.setDraft
  const set = useCallback(
    (value: T | null) => (storeSet ? storeSet(key, value) : setLocal(value)),
    [storeSet, key],
  )
  if (!store) return [local, set]
  return [(store.drafts[key] as T | undefined) ?? null, set]
}
