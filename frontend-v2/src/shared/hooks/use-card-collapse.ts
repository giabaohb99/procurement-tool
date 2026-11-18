import { createContext, useCallback, useContext, useState } from 'react'

import { readSectionOpen, writeSectionOpen } from '@/shared/utils/section-open-storage'

/**
 * Tiền tố khóa nhớ của PHẠM VI gập thẻ (vd `me`). `null` = ngoài phạm vi: thẻ không gập được.
 * Đặt bằng `CardCollapseScope` (`shared/ui/card-collapse.tsx`).
 */
export const CardCollapseContext = createContext<string | null>(null)

/** Kết quả của `useCardCollapse`: có nút gập không, đang mở không, và hàm bấm gập / mở. */
export interface CardCollapseState {
  collapsible: boolean
  open: boolean
  toggle: () => void
}

/**
 * Trạng thái gập của MỘT thẻ, theo tiêu đề thẻ (duoc-CR-772).
 *
 * Thẻ dùng chung (`FormCard`, khung người báo tin, Lịch sử thao tác) gọi hook này: nằm trong
 * `CardCollapseScope` thì `collapsible = true` và có nút chevron; ngoài phạm vi thì luôn mở, mọi màn
 * khác không đổi gì. Mặc định MỞ; người dùng gập rồi thì nhớ theo `<phạm vi>.<tiêu đề>`.
 *
 * `forceOpen` ép MỞ bất kể bản lưu — dùng khi trong thẻ đang có ô sai hoặc đang lập chứng từ mới: ô bắt
 * buộc nằm trong thẻ gập thì bấm Lưu chỉ thấy câu báo mà không thấy ô nào (bẫy thứ nhất của duoc-CR-317).
 */
export function useCardCollapse(
  title: string,
  { forceOpen = false }: { forceOpen?: boolean } = {},
): CardCollapseState {
  const scope = useContext(CardCollapseContext)
  const storageKey = scope ? `${scope}.${title}` : undefined
  const [saved, setSaved] = useState<boolean | null>(() => readSectionOpen(storageKey))

  const toggle = useCallback(() => {
    setSaved((current) => {
      const next = !(current ?? true)
      writeSectionOpen(storageKey, next)
      return next
    })
  }, [storageKey])

  //  Đang ép mở thì không cho bấm gập: nút bấm mà không có tác dụng là nút hỏng.
  return {
    collapsible: scope !== null && !forceOpen,
    open: scope === null || forceOpen || (saved ?? true),
    toggle,
  }
}
