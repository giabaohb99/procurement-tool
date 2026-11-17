import { createContext, useCallback, useContext, useState } from 'react'

import { readSectionOpen, writeSectionOpen } from '@/shared/utils/section-open-storage'

/**
 * Tiền tố khóa nhớ của PHẠM VI gập thẻ (vd `me`). `null` = ngoài phạm vi: thẻ không gập được.
 * Đặt bằng `CardCollapseScope` (`shared/ui/card-collapse.tsx`).
 */
export const CardCollapseContext = createContext<string | null>(null)

/**
 * Trạng thái gập của MỘT thẻ, theo tiêu đề thẻ (duoc-CR-772).
 *
 * Thẻ dùng chung (`FormCard`, khung người báo tin, Lịch sử thao tác) gọi hook này: nằm trong
 * `CardCollapseScope` thì `collapsible = true` và có nút chevron; ngoài phạm vi thì luôn mở, mọi màn
 * khác không đổi gì. Mặc định MỞ; người dùng gập rồi thì nhớ theo `<phạm vi>.<tiêu đề>`.
 */
export function useCardCollapse(title: string) {
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

  return { collapsible: scope !== null, open: scope === null || (saved ?? true), toggle }
}
