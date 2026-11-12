import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { employeeConcurrentApi } from '../api/employee-concurrent-api'
import type { EmployeeConcurrentPayload } from '../types/employee-concurrent'

/**
 * Dòng kiêm nhiệm của MỘT hồ sơ. `0` = chưa biết id (đang tải trang chi tiết).
 * Dùng chung cho tab Kiêm nhiệm, hộp đổi pháp nhân và câu hỏi Áp quá trình công tác — cùng khóa nên chỉ gọi một lần.
 */
export function useEmployeeConcurrents(employeeId: number, options: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: queryKeys.hr.employeeConcurrents(employeeId),
    queryFn: () => employeeConcurrentApi.list(employeeId),
    enabled: employeeId > 0 && (options.enabled ?? true),
  })
}

/**
 * Thêm hoặc sửa một dòng. Đổi kiêm nhiệm là đổi PHẠM VI DỮ LIỆU của người này (và nhãn ở phòng đích), nên nạp lại
 * cả nhánh `hr`. Lỗi 400/403/409 đã được `httpClient` bày toast đúng câu backend — ở đây không khai `onError`.
 */
export function useSaveEmployeeConcurrent(employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, payload }: { id?: number; payload: EmployeeConcurrentPayload }) =>
      id
        ? employeeConcurrentApi.update(employeeId, id, payload)
        : employeeConcurrentApi.create(employeeId, payload),
    onSuccess: (_result, variables) => {
      toast.success(variables.id ? 'Đã cập nhật kiêm nhiệm' : 'Đã thêm kiêm nhiệm')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

export function useDeleteEmployeeConcurrent(employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => employeeConcurrentApi.remove(employeeId, id),
    onSuccess: () => {
      toast.success('Đã xóa dòng kiêm nhiệm')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}
