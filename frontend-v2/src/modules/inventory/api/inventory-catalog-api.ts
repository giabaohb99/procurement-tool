import { apiGet } from '@/core/api'
import type { PaginatedResult } from '@/shared/types/api'

/**
 * Danh mục nền mà màn Tồn kho cần: KHO, PHÂN LOẠI, SẢN PHẨM.
 *
 * Phân hệ Thu mua có một bản sao gần giống trong
 * `procurement/api/purchase-request-support-api.ts` (phục vụ form YCMH). Không
 * gọi chéo sang đó: kho là danh mục của chính phân hệ này, và một module đọc
 * ruột module khác là chỗ về sau gỡ không ra. Khi màn Danh mục kho / Sản phẩm
 * lên v2, hai bản này gộp về chủ sở hữu thật của từng danh mục.
 */

export interface WarehouseOption {
  id: number
  code: string
  name: string
}

export interface ItemGroupOption {
  id: number
  code: string
  name: string
}

export interface ProductOption {
  id: number
  code: string
  name: string
  item_group: string
  unit: string
}

export const inventoryCatalogApi = {
  /**
   * Toàn bộ kho, KHÔNG lọc `is_active`: kho ngừng dùng vẫn có thể còn tồn, lọc
   * đi thì người dùng không chọn được để soi số dư còn kẹt lại.
   */
  listWarehouses: (search = '') =>
    apiGet<PaginatedResult<WarehouseOption>>('/api/warehouses', {
      params: { page: 1, page_size: 300, name: search || undefined },
    }),

  listItemGroups: () =>
    apiGet<PaginatedResult<ItemGroupOption>>('/api/item-groups', {
      params: { page: 1, page_size: 500 },
    }),

  listProducts: (search = '') =>
    apiGet<PaginatedResult<ProductOption>>('/api/products', {
      params: { page: 1, page_size: 30, search, is_active: true },
    }),
}
