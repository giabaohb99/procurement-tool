/**
 * duoc-CR-784 — nạp ĐỦ mọi dòng cho các BẢN IN cụm Giá bao bì (bản v1): lật từng trang `PRINT_PAGE_SIZE` dòng cho tới khi đủ
 * `total` của máy chủ hoặc chạm trần `PRINT_ROW_CAP`. KPI + biểu đồ + bảng mã đã chọn lấy ở lượt đầu (máy chủ tính trên TOÀN
 * BỘ tập đã lọc, không phụ thuộc trang). Gọi kèm `_silent` để lỗi không bật toast — trang in tự hiện câu lỗi.
 */
import { api } from './client'
import type {
  PackagingHistoryParams, PackagingHistoryResult, PackagingImpactRequest, PackagingImpactResult,
} from './packaging-cost-types'
import { PRINT_PAGE_SIZE, PRINT_ROW_CAP, planPrintRows } from '../utils/packaging-print'

const BASE = '/api/packaging-cost'

/** Câu lỗi người đọc được từ một lỗi axios: ưu tiên câu của backend, rồi câu của axios. */
export const printErrorMessage = (e: any): string =>
  e?.response?.data?.error?.message || e?.message || 'Lỗi không xác định'

/** Số lượt nạp tối đa — chặn vòng lặp khi tổng của máy chủ lệch giữa chừng. */
const MAX_PAGES = Math.ceil(PRINT_ROW_CAP / PRINT_PAGE_SIZE)

export type PackagingHistoryPrintData = PackagingHistoryResult & { capped: boolean }
export type PackagingImpactPrintData = PackagingImpactResult & { capped: boolean }

export async function fetchAllHistory(params: PackagingHistoryParams): Promise<PackagingHistoryPrintData> {
  const get = async (page: number): Promise<PackagingHistoryResult> =>
    (await api.get(`${BASE}/history`, { params: { ...params, page, page_size: PRINT_PAGE_SIZE }, _silent: true } as any)).data.data
  const first = await get(1)
  const { rows, capped } = planPrintRows(first.total)
  const items = [...first.items]
  for (let page = 2; items.length < rows && page <= MAX_PAGES; page++) {
    const next = await get(page)
    if (next.items.length === 0) break
    items.push(...next.items)
  }
  return { ...first, items: items.slice(0, rows), capped }
}

export async function fetchAllImpact(request: PackagingImpactRequest): Promise<PackagingImpactPrintData> {
  const post = async (page: number): Promise<PackagingImpactResult> =>
    (await api.post(`${BASE}/impact`, { ...request, page, page_size: PRINT_PAGE_SIZE }, { _silent: true } as any)).data.data
  const first = await post(1)
  const { rows, capped } = planPrintRows(first.products_total)
  const products = [...first.products]
  for (let page = 2; products.length < rows && page <= MAX_PAGES; page++) {
    const next = await post(page)
    if (next.products.length === 0) break
    products.push(...next.products)
  }
  return { ...first, products: products.slice(0, rows), capped }
}
