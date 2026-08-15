import { useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { supplierApi } from '../api/supplier-api'
import type { SupplierFormValues } from '../schemas/supplier-schema'

/**
 * Tạo mới HOẶC cập nhật nhà cung cấp — gộp một hook vì màn hình dùng chung một form.
 * Có `id` là sửa, không có là thêm mới.
 *
 * Lỗi đã được http-client toast sẵn (đây là mutation, không phải GET) nên ở đây
 * chỉ lo báo thành công và làm mới danh sách.
 */
export function useSaveSupplier() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: SupplierFormValues }) =>
      id ? supplierApi.update(id, values) : supplierApi.create(values),

    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã cập nhật nhà cung cấp' : 'Đã thêm nhà cung cấp')
      // Invalidate theo tầng gốc để bắt hết mọi biến thể tham số của danh sách.
      void queryClient.invalidateQueries({ queryKey: queryKeys.production.all })
    },
  })
}
