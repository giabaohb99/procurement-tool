import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { inventoryCatalogApi } from '../api/inventory-catalog-api'

/** Danh mục nền đổi rất thưa — giữ 5 phút, khỏi nạp lại mỗi lần mở hộp thoại. */
const CATALOG_STALE_TIME = 5 * 60 * 1000

export function useWarehouseOptions() {
  return useQuery({
    queryKey: queryKeys.inventory.warehouses(),
    queryFn: () => inventoryCatalogApi.listWarehouses(),
    staleTime: CATALOG_STALE_TIME,
  })
}

export function useItemGroupOptions() {
  return useQuery({
    queryKey: queryKeys.inventory.itemGroups(),
    queryFn: inventoryCatalogApi.listItemGroups,
    staleTime: CATALOG_STALE_TIME,
  })
}

/** Tìm sản phẩm để điều chỉnh tồn. Chỉ chạy khi ô tìm đang mở. */
export function useProductOptions(search: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.inventory.products(search),
    queryFn: () => inventoryCatalogApi.listProducts(search),
    enabled,
    staleTime: 60 * 1000,
  })
}
