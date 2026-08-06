import { useEffect, useState } from 'react'

// Theo dõi một media query trong React. Dùng cho những chỗ bố cục KHÔNG chỉ đổi CSS mà đổi cả
// hành vi (sidebar khu người dùng: ở màn rộng là một cột đẩy nội dung sang, ở màn hẹp là ngăn
// kéo phủ lên trên) — chỗ đó phải biết bề ngang trong JS chứ không ẩn/hiện bằng class được.

export function useMediaQuery(query: string): boolean {
  const [matches, setMatches] = useState(() => window.matchMedia(query).matches)

  useEffect(() => {
    const mql = window.matchMedia(query)
    const onChange = () => setMatches(mql.matches)
    onChange() // query đổi giữa chừng thì phải đồng bộ lại ngay
    mql.addEventListener('change', onChange)
    return () => mql.removeEventListener('change', onChange)
  }, [query])

  return matches
}

/** Bề ngang từ đây trở lên mới đủ chỗ cho sidebar dạng cột (Tailwind `lg`). */
export const DESKTOP_QUERY = '(min-width: 1024px)'

/** Bề ngang từ đây trở lên mới đủ chỗ cho CẢ sidebar lẫn mục lục (Tailwind `xl`). */
export const WIDE_QUERY = '(min-width: 1280px)'
