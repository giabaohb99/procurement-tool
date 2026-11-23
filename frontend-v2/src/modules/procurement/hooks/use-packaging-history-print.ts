/**
 * duoc-CR-784 — nạp ĐỦ mọi dòng Lịch sử mua hàng cho bản in: đi từng trang `HISTORY_PRINT_PAGE_SIZE` dòng cho tới khi đủ
 * `total` của máy chủ hoặc chạm trần `HISTORY_PRINT_ROW_CAP`. KPI + biểu đồ lấy ở lượt đầu (máy chủ tính trên TOÀN BỘ
 * tập đã lọc, không phụ thuộc trang), nên không cần gom lại.
 */
import { useQuery } from '@tanstack/react-query'

import { fetchPackagingHistory } from '../api/packaging-cost-api'
import { packagingCostKeys } from '../config/packaging-cost-query-keys'
import type { PackagingHistoryParams, PackagingHistoryResult } from '../types/packaging-cost-types'
import {
  HISTORY_PRINT_PAGE_SIZE,
  HISTORY_PRINT_ROW_CAP,
  planHistoryPrintRows,
} from '../utils/packaging-history-print'

export interface PackagingHistoryPrintData extends PackagingHistoryResult {
  /** Bộ lọc có nhiều dòng hơn trần nên `items` đã bị cắt. */
  capped: boolean
}

export async function fetchAllPackagingHistory(
  params: PackagingHistoryParams,
): Promise<PackagingHistoryPrintData> {
  const first = await fetchPackagingHistory({ ...params, page: 1, page_size: HISTORY_PRINT_PAGE_SIZE })
  const { rows: wanted, capped } = planHistoryPrintRows(first.total)
  const items = [...first.items]
  //  Dừng ngay khi một trang về rỗng: tổng của máy chủ lệch (dòng bị xóa giữa chừng) thì không quay vòng vô hạn.
  for (
    let page = 2;
    items.length < wanted && (page - 1) * HISTORY_PRINT_PAGE_SIZE < HISTORY_PRINT_ROW_CAP;
    page += 1
  ) {
    const next = await fetchPackagingHistory({ ...params, page, page_size: HISTORY_PRINT_PAGE_SIZE })
    if (next.items.length === 0) break
    items.push(...next.items)
  }
  return { ...first, items: items.slice(0, wanted), capped }
}

export function usePackagingHistoryPrint(params: PackagingHistoryParams) {
  return useQuery({
    queryKey: packagingCostKeys.historyPrint(params),
    queryFn: () => fetchAllPackagingHistory(params),
    //  Bản in là ảnh chụp một lần: lấy lại khi cửa sổ lấy lại tiêu điểm (hộp thoại in đóng) làm bảng nhảy giữa lúc in.
    staleTime: Infinity,
    refetchOnWindowFocus: false,
    retry: false,
  })
}
