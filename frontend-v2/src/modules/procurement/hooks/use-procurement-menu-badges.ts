import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

import { queryKeys } from '@/shared/constants/query-keys'
import { procurementDashboardApi } from '../api/procurement-dashboard-api'

/**
 * Số phiếu chờ duyệt cho viên số trên menu Thu mua (duoc-CR-723, phiếu hỗ trợ TK06112601).
 *
 * MỘT query cho cả bốn viên số (cùng khóa nên TanStack gộp). Nạp lại khi:
 * - đổi trang — duyệt xong một phiếu rồi quay về danh sách thì số phải giảm ngay;
 * - mỗi 60 giây, CHỈ khi tab đang hiện (`refetchIntervalInBackground` mặc định tắt) — thumua hay mở nền cả
 *   ngày, gọi đều cho một màn không ai nhìn là tải thừa; quay lại tab thì `refetchOnWindowFocus` nạp ngay.
 *
 * ⚠️ `cancelRefetch: false`: bốn viên số cùng chạy hiệu ứng đổi trang; để mặc định thì mỗi lời gọi HỦY lượt
 * đang bay rồi bắn lượt mới — bốn yêu cầu cho một lần chuyển trang. Tắt đi thì ba lời gọi sau dùng lại lượt đầu.
 */
export function useProcurementMenuBadges() {
  const { pathname } = useLocation()
  const query = useQuery({
    queryKey: queryKeys.procurement.menuBadges(),
    queryFn: () => procurementDashboardApi.getMenuBadges(),
    refetchInterval: 60_000,
  })
  const { refetch } = query

  useEffect(() => {
    void refetch({ cancelRefetch: false })
  }, [pathname, refetch])

  return query
}
