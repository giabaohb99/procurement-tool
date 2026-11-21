/**
 * duoc-CR-784 — gọi API cụm Giá bao bì.
 *
 * Tác động giá + Bảng giá ở `/api/packaging-cost` (phase 04); báo giá, ngưỡng, định mức là ba router
 * CRUD riêng (phase 03) — báo giá và định mức đi qua lớp `shared/crud`, ở đây chỉ còn ngưỡng (một
 * dòng mỗi mã, tra theo `product_code`).
 */
import { apiGet, apiPatch, apiPost, downloadFile, httpClient } from '@/core/api'
import { filenameFromContentDisposition } from '@/core/api/download-file'

import { readBlobErrorMessage } from './customs-api'
import type {
  PackagingCodeOption,
  PackagingHhOption,
  PackagingHistoryParams,
  PackagingHistoryResult,
  PackagingImpactRequest,
  PackagingImpactResult,
  PackagingLastPricesParams,
  PackagingLastPricesResult,
  PackagingOverviewParams,
  PackagingOverviewResult,
  PackagingPriceLimit,
  PackagingPriceListParams,
  PackagingPriceListResult,
} from '../types/packaging-cost-types'

const BASE = '/api/packaging-cost'
export const PACKAGING_QUOTE_API = '/api/product-price-quotes'
export const PACKAGING_LIMIT_API = '/api/product-price-limits'
export const PACKAGING_BOM_API = '/api/packaging-boms'

/** Mã đang dùng trong định mức (~1.500) cho ô chọn nhiều — nạp một lần, lọc ở trình duyệt. */
export async function fetchPackagingCodeOptions(): Promise<PackagingCodeOption[]> {
  //  Hợp đồng chỉ nói "trả đủ" — nhận cả mảng trần lẫn khuôn `{items}` của danh sách cho chắc.
  const res = await apiGet<PackagingCodeOption[] | { items: PackagingCodeOption[] }>(
    `${BASE}/code-options`,
  )
  return Array.isArray(res) ? res : (res.items ?? [])
}

/** Tính tác động — đọc thuần, không ghi nhật ký nên được gọi bằng `useQuery`. */
export function fetchPackagingImpact(body: PackagingImpactRequest) {
  return apiPost<PackagingImpactResult>(`${BASE}/impact`, body)
}

export function fetchPackagingPriceList(params: PackagingPriceListParams) {
  return apiGet<PackagingPriceListResult>(`${BASE}/price-list`, { params })
}

/** Xuất Bảng giá — cùng bộ lọc + thứ tự đang xem, không kèm `page`. */
export async function exportPackagingPriceList(params: PackagingPriceListParams) {
  try {
    await downloadFile(`${BASE}/price-list/export`, 'bang-gia-vtbb.xlsx', { ...params })
  } catch (error) {
    throw new Error(await readBlobErrorMessage(error), { cause: error })
  }
}

export function fetchPackagingLastPrices(params: PackagingLastPricesParams) {
  return apiGet<PackagingLastPricesResult>(`${BASE}/last-prices`, { params })
}

/** Xuất Giá mua gần nhất — cùng bộ lọc, số lần `n` + thứ tự đang xem, không kèm `page`. */
export async function exportPackagingLastPrices(params: PackagingLastPricesParams) {
  try {
    await downloadFile(`${BASE}/last-prices/export`, 'gia-mua-gan-nhat.xlsx', { ...params })
  } catch (error) {
    throw new Error(await readBlobErrorMessage(error), { cause: error })
  }
}

/** Tổng hợp theo sản phẩm: mọi sản phẩm có định mức, chi phí / chai cũ so với mới + xu hướng; lọc / xếp / trang tại máy chủ. */
export function fetchPackagingProductOverview(params: PackagingOverviewParams) {
  return apiGet<PackagingOverviewResult>(`${BASE}/product-overview`, { params })
}

/** Xuất Tổng hợp theo sản phẩm — cùng bộ lọc + thứ tự đang xem, không kèm `page`. */
export async function exportPackagingProductOverview(params: PackagingOverviewParams) {
  try {
    await downloadFile(`${BASE}/product-overview/export`, 'tong-hop-theo-san-pham.xlsx', { ...params })
  } catch (error) {
    throw new Error(await readBlobErrorMessage(error), { cause: error })
  }
}

/** Lịch sử mua hàng: từng lần mua + KPI + biểu đồ; lọc / xếp / phân trang tại máy chủ. */
export function fetchPackagingHistory(params: PackagingHistoryParams) {
  return apiGet<PackagingHistoryResult>(`${BASE}/history`, { params })
}

/** Xuất Lịch sử mua hàng — cùng bộ lọc + thứ tự đang xem, không kèm `page`. */
export async function exportPackagingHistory(params: PackagingHistoryParams) {
  try {
    await downloadFile(`${BASE}/history/export`, 'lich-su-mua-hang.xlsx', { ...params })
  } catch (error) {
    throw new Error(await readBlobErrorMessage(error), { cause: error })
  }
}

/** Sản phẩm (mã HH) có định mức bao bì — nạp một lần cho ô chọn của chế độ "Theo mã sản phẩm". */
export async function fetchPackagingHhOptions(): Promise<PackagingHhOption[]> {
  const res = await apiGet<{ items: PackagingHhOption[] }>(`${BASE}/hh-options`)
  return res.items ?? []
}

/**
 * Xuất màn Tác động (2 sheet). Đường là POST (thân giống `/impact`) nên không dùng được
 * `downloadFile` (chỉ GET) — tự tải blob rồi bấm hộ một thẻ `<a>`.
 */
export async function exportPackagingImpact(body: PackagingImpactRequest) {
  try {
    const response = await httpClient.post<Blob>(`${BASE}/impact/export`, body, {
      responseType: 'blob',
    })
    const disposition = response.headers['content-disposition']
    const filename =
      filenameFromContentDisposition(typeof disposition === 'string' ? disposition : undefined) ??
      'tac-dong-gia-bao-bi.xlsx'
    const objectUrl = URL.createObjectURL(response.data)
    try {
      const anchor = document.createElement('a')
      anchor.href = objectUrl
      anchor.download = filename
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
    } finally {
      URL.revokeObjectURL(objectUrl)
    }
  } catch (error) {
    throw new Error(await readBlobErrorMessage(error), { cause: error })
  }
}

/** Ngưỡng của MỘT mã; chưa đặt thì `null`. */
export async function fetchPackagingPriceLimit(code: string): Promise<PackagingPriceLimit | null> {
  const res = await apiGet<{ items: PackagingPriceLimit[] }>(PACKAGING_LIMIT_API, {
    params: { product_code: code, page_size: 50 },
  })
  //  `apply_filters` lọc LIKE với cột chuỗi nên lấy nhiều dòng rồi so đúng mã: chỉ lấy 1 dòng thì mã dài hơn có dòng mới
  //  hơn (`NAP00851`) che mất dòng của `NAP0085`, hộp thoại tưởng chưa có ngưỡng và tạo trùng (máy chủ trả 400).
  return res.items.find((item) => item.product_code === code) ?? null
}

export interface PackagingPriceLimitPayload {
  product_code: string
  floor_price: number | null
  ceiling_price: number | null
  note: string
}

/** Có rồi thì sửa, chưa có thì tạo (mỗi mã đúng một dòng ngưỡng). */
export function savePackagingPriceLimit(id: number | null, payload: PackagingPriceLimitPayload) {
  return id
    ? apiPatch<PackagingPriceLimit>(`${PACKAGING_LIMIT_API}/${id}`, payload)
    : apiPost<PackagingPriceLimit>(PACKAGING_LIMIT_API, payload)
}
