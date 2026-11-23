/**
 * duoc-CR-784 — nạp ĐỦ mọi sản phẩm bị ảnh hưởng cho bản in Tác động giá: lật từng trang `IMPACT_PRINT_PAGE_SIZE` dòng
 * cho tới khi đủ `products_total` hoặc chạm trần. Bảng mã đã chọn + KPI lấy ở lượt đầu (không phụ thuộc trang).
 */
import { useQuery } from '@tanstack/react-query'

import { fetchPackagingImpact } from '../api/packaging-cost-api'
import { packagingCostKeys } from '../config/packaging-cost-query-keys'
import type { PackagingImpactRequest, PackagingImpactResult } from '../types/packaging-cost-types'
import { planHistoryPrintRows } from '../utils/packaging-history-print'
import { IMPACT_PRINT_PAGE_SIZE, IMPACT_PRINT_ROW_CAP } from '../utils/packaging-impact-print'

export interface PackagingImpactPrintData extends PackagingImpactResult {
  /** Có nhiều sản phẩm hơn trần nên `products` đã bị cắt. */
  capped: boolean
}

export async function fetchAllPackagingImpact(
  request: PackagingImpactRequest,
): Promise<PackagingImpactPrintData> {
  const first = await fetchPackagingImpact({ ...request, page: 1, page_size: IMPACT_PRINT_PAGE_SIZE })
  const { rows: wanted, capped } = planHistoryPrintRows(first.products_total, IMPACT_PRINT_ROW_CAP)
  const products = [...first.products]
  //  Dừng ngay khi một trang về rỗng: tổng lệch giữa chừng thì không quay vòng vô hạn.
  for (
    let page = 2;
    products.length < wanted && (page - 1) * IMPACT_PRINT_PAGE_SIZE < IMPACT_PRINT_ROW_CAP;
    page += 1
  ) {
    const next = await fetchPackagingImpact({ ...request, page, page_size: IMPACT_PRINT_PAGE_SIZE })
    if (next.products.length === 0) break
    products.push(...next.products)
  }
  return { ...first, products: products.slice(0, wanted), capped }
}

export function usePackagingImpactPrint(request: PackagingImpactRequest) {
  return useQuery({
    queryKey: packagingCostKeys.impactPrint(request),
    queryFn: () => fetchAllPackagingImpact(request),
    //  Chưa chọn mã nào (link hỏng) thì không gọi máy chủ — trang in tự báo "chưa chọn mã".
    enabled: request.codes.length > 0,
    staleTime: Infinity,
    refetchOnWindowFocus: false,
    retry: false,
  })
}
