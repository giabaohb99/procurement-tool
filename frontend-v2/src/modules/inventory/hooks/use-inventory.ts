import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { inventoryApi } from '../api/inventory-api'
import type { InventoryItem } from '../types/inventory'

/** Danh sách tồn hiện tại. Phân trang do server làm — bảng có thể tới vài nghìn dòng. */
export function useInventoryItems(params: ListParams = {}) {
  const query: ListParams = {
    page: 1,
    page_size: appConfig.defaultPageSize,
    ...params,
  }

  return useQuery({
    queryKey: queryKeys.inventory.stock(query),
    queryFn: () => inventoryApi.list(query),
    placeholderData: keepPreviousData,
  })
}

/**
 * Sổ phát sinh của MỘT dòng tồn. Chỉ chạy khi đã mở hộp thoại chi tiết.
 *
 * Lấy 100 dòng gần nhất (backend xếp `id desc`) và không phân trang: hộp thoại
 * là chỗ tra nhanh vì sao số dư ra thế này, ai cần soi sâu hơn thì đọc chứng từ gốc.
 */
export function useInventoryMoves(item: InventoryItem | null) {
  const params: ListParams = {
    company_id: item?.company_id ?? 0,
    warehouse_code: item?.warehouse_code ?? '',
    product_code: item?.product_code ?? '',
    page: 1,
    page_size: 100,
  }

  return useQuery({
    queryKey: queryKeys.inventory.moves(params),
    queryFn: () => inventoryApi.listMoves(params),
    enabled: !!item,
  })
}

/**
 * Tồn hiện tại của ĐÚNG một bộ ba công ty · kho · mã SP — để hộp thoại điều
 * chỉnh cho thấy số dư trước khi cộng/trừ.
 *
 * Dùng `__eq` chứ không gửi tham số trần: trần thì `apply_filters` dịch thành
 * `LIKE %mã%`, lọc mã "SP01" ra luôn "SP012" và số dư hiện lên là của mã khác.
 */
export function useInventoryLine(companyId: number, warehouseCode: string, productCode: string) {
  const params: ListParams = {
    company_id: companyId,
    warehouse_code__eq: warehouseCode,
    product_code__eq: productCode,
    page: 1,
    page_size: 1,
  }

  return useQuery({
    queryKey: queryKeys.inventory.stock(params),
    queryFn: () => inventoryApi.list(params),
    enabled: companyId > 0 && !!warehouseCode && !!productCode,
  })
}

/**
 * Điều chỉnh tay. Vô hiệu cả nhánh `inventory` chứ không riêng danh sách: một
 * lần điều chỉnh đổi luôn cả sổ phát sinh đang mở trong hộp thoại chi tiết.
 */
export function useAdjustInventory() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: inventoryApi.adjust,
    onSuccess: () => {
      toast.success('Đã điều chỉnh tồn kho')
      void queryClient.invalidateQueries({ queryKey: queryKeys.inventory.all })
    },
  })
}
