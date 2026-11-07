import { useEffect, useState } from 'react'
import { api } from '../api/client'

/** Số phiếu CHỜ DUYỆT theo từng mục menu — khóa = entity của mục (`purchase_order`, `survey_request`…). */
export type MenuBadgeCounts = Record<string, number>

/**
 * Nạp số đếm cho bóng đỏ trên menu trái (duoc-CR-723, phiếu hỗ trợ TK06112601).
 *
 * Gọi lại mỗi khi đổi trang (`refreshKey` = đường dẫn hiện tại): duyệt xong một phiếu rồi quay về danh sách
 * thì số trên menu phải giảm ngay, không đợi tới lượt hẹn giờ. Thêm hẹn giờ 60 giây cho trường hợp đứng yên
 * một màn mà người khác gửi phiếu mới. Lỗi mạng thì giữ số cũ, im lặng — bóng menu không đáng một toast.
 *
 * Tab đang ẨN thì bỏ lượt hẹn giờ: người ta hay để thumua mở nền cả ngày, gọi đều đặn cho một màn không ai
 * nhìn là tải thừa lên máy chủ. Quay lại tab thì nạp ngay một lần cho số khỏi cũ.
 */
export function useMenuBadges(refreshKey: string): MenuBadgeCounts {
  const [counts, setCounts] = useState<MenuBadgeCounts>({})

  useEffect(() => {
    let alive = true
    const load = () =>
      api
        .get('/api/dashboard/menu-badges')
        .then((r) => {
          if (alive) setCounts(r.data?.data || {})
        })
        .catch(() => {})
    const isVisible = () => document.visibilityState === 'visible'
    const onVisibilityChange = () => {
      if (isVisible()) load()
    }
    load()
    const timer = setInterval(() => {
      if (isVisible()) load()
    }, 60000)
    document.addEventListener('visibilitychange', onVisibilityChange)
    return () => {
      alive = false
      clearInterval(timer)
      document.removeEventListener('visibilitychange', onVisibilityChange)
    }
  }, [refreshKey])

  return counts
}
