// Mục «Thuốc BVTV» của Tra cứu thị trường — hook TanStack Query.
import { keepPreviousData, useMutation, useQuery } from '@tanstack/react-query'

import { usePermission } from '@/core/authorization/use-permission'
import { queryKeys } from '@/shared/constants/query-keys'

import {
  createCustomsPesticide,
  deleteCustomsPesticide,
  fetchCustomsPesticide,
  fetchCustomsPesticideOptions,
  fetchCustomsPesticides,
  importCustomsPesticides,
  updateCustomsPesticide,
} from '../api/customs-pesticide-api'
import type { CustomsPesticideInput } from '../types/customs-pesticide'
import { useInvalidateCustoms } from './use-customs'

export function useCustomsPesticides(params: Record<string, unknown>, enabled = true) {
  return useQuery({
    queryKey: queryKeys.procurement.customsPesticides(params),
    queryFn: () => fetchCustomsPesticides(params),
    enabled,
    //  Đổi trang / bộ lọc giữ bảng cũ tới khi có bảng mới — không nháy trắng.
    placeholderData: keepPreviousData,
  })
}

export function useCustomsPesticideOptions() {
  return useQuery({
    queryKey: queryKeys.procurement.customsPesticideOptions(),
    queryFn: fetchCustomsPesticideOptions,
  })
}

export function useCustomsPesticide(id: number | null) {
  return useQuery({
    queryKey: queryKeys.procurement.customsPesticide(id ?? 0),
    queryFn: () => fetchCustomsPesticide(id ?? 0),
    enabled: id !== null,
  })
}

/** Nạp tệp xong thì bỏ hiệu lực CẢ màn Tra cứu thị trường: backend gắn lại hoạt chất mọi dòng hàng. */
export function useImportCustomsPesticides() {
  const invalidate = useInvalidateCustoms()
  return useMutation({ mutationFn: importCustomsPesticides, onSuccess: () => invalidate() })
}

/**
 * Thêm (`id` = null) hoặc sửa một thuốc. Bỏ hiệu lực cả màn Tra cứu thị trường: số đếm của mục
 * Pháp lý (thuốc chứa hoạt chất cấm) và ô lọc đều đọc danh mục này.
 */
export function useSaveCustomsPesticide() {
  const invalidate = useInvalidateCustoms()
  return useMutation({
    mutationFn: ({ id, body }: { id: number | null; body: CustomsPesticideInput }) =>
      id === null ? createCustomsPesticide(body) : updateCustomsPesticide(id, body),
    onSuccess: () => invalidate(),
  })
}

export function useDeleteCustomsPesticide() {
  const invalidate = useInvalidateCustoms()
  return useMutation({ mutationFn: deleteCustomsPesticide, onSuccess: () => invalidate() })
}

/** Quyền SỬA danh mục thuốc — khóa riêng `customs_pesticide` (duoc-CR-490); xem vẫn theo `customs_price.read`. */
export function usePesticidePermissions() {
  const { can } = usePermission()
  return {
    canCreate: can('customs_pesticide', 'create'),
    canEdit: can('customs_pesticide', 'write'),
    canDelete: can('customs_pesticide', 'delete'),
    //  Nạp lại cả danh mục = ghi đè hàng nghìn thuốc → cùng mức `write`.
    canImport: can('customs_pesticide', 'write'),
  }
}
