import { apiGet, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { InventoryItem, InventoryMove } from '../types/inventory'

const BASE_URL = '/api/inventory'

/**
 * Số lượng của một lần điều chỉnh là DELTA (+ tăng, − giảm), không phải tồn mới.
 *
 * `unit_price` bỏ trống (0) thì backend lấy đơn giá bình quân đang có của chính
 * bộ ba công ty · kho · mã SP đó.
 */
export interface InventoryAdjustPayload {
  company_id: number
  warehouse_code: string
  product_code: string
  product_name: string
  unit: string
  qty: number
  unit_price: number
  note: string
}

/**
 * ⚠️ Whitelist `apply_filters` của `/api/inventory` chỉ có
 * `warehouse_code · product_code · product_name` (xem `inventory/service.FILTERABLE`).
 *
 * Ba tham số còn lại — `company_id`, `item_group`, `qty_status` — controller đọc
 * TAY, nên chúng chỉ nhận giá trị trần, không dùng được cú pháp `<field>__<op>`
 * của bộ lọc nâng cao. `item_group` lọc bằng cách join `tab_product` theo mã SP.
 */
export const inventoryApi = {
  list: (params: ListParams) => apiGet<PaginatedResult<InventoryItem>>(BASE_URL, { params }),

  /** Sổ phát sinh. Lọc được `company_id`, `warehouse_code`, `product_code` — khớp CHÍNH XÁC. */
  listMoves: (params: ListParams) =>
    apiGet<PaginatedResult<InventoryMove>>(`${BASE_URL}/moves`, { params }),

  adjust: (payload: InventoryAdjustPayload) =>
    apiPost<InventoryItem>(`${BASE_URL}/adjust`, payload),
}
