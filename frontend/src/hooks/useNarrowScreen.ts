import { useEffect, useState } from 'react'

/** Ngưỡng màn hẹp của bản v1 — cùng `@media (max-width: 820px)` trong index.css (menu thành drawer, bảng cuộn ngang). */
export const NARROW_SCREEN_MAX_WIDTH = 820

/**
 * `true` khi cửa sổ rộng ≤ 820px. Dùng để chọn CÁCH VẼ (bảng ↔ thẻ) chứ không chỉ đổi kiểu: chỉ một nhánh được dựng
 * nên ô nhập trong thẻ (vd giá giả định) không bị nhân đôi trong DOM. Theo dõi `matchMedia` nên xoay màn / kéo cửa sổ
 * đổi theo ngay.
 */
export function useNarrowScreen(): boolean {
  const query = `(max-width: ${NARROW_SCREEN_MAX_WIDTH}px)`
  const [narrow, setNarrow] = useState(() => typeof window !== 'undefined' && !!window.matchMedia && window.matchMedia(query).matches)

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return
    const mql = window.matchMedia(query)
    const onChange = () => setNarrow(mql.matches)
    onChange()
    mql.addEventListener('change', onChange)
    return () => mql.removeEventListener('change', onChange)
  }, [query])

  return narrow
}
