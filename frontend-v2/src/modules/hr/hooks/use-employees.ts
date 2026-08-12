import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { employeeApi } from '../api/employee-api'
import type { EmployeeFormValues } from '../schemas/employee-schema'

/**
 * Danh sách nhân viên có phân trang + lọc.
 * Whitelist lọc của backend: `code`, `full_name`, `email`, `position`,
 * `department_id`, `status`, `is_active` — gửi key ngoài danh sách này là vô ích.
 */
export function useEmployees(params: ListParams = {}) {
  const query: ListParams = {
    page: 1,
    page_size: appConfig.defaultPageSize,
    ...params,
  }

  return useQuery({
    queryKey: queryKeys.hr.employees(query),
    queryFn: () => employeeApi.list(query),
    placeholderData: keepPreviousData,
  })
}

/** Một hồ sơ nhân sự (bản chi tiết, có thêm `user_id`). */
export function useEmployee(id: number) {
  return useQuery({
    queryKey: queryKeys.hr.employee(id),
    queryFn: () => employeeApi.getById(id),
    enabled: id > 0,
  })
}

/**
 * Tạo mới HOẶC cập nhật — gộp một hook vì hai màn dùng chung một form.
 * Lỗi đã được http-client toast sẵn (không phải GET) nên ở đây chỉ lo báo
 * thành công và làm mới cache.
 */
export function useSaveEmployee() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: EmployeeFormValues }) =>
      id ? employeeApi.update(id, values) : employeeApi.create(values),

    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã cập nhật nhân sự' : 'Đã thêm nhân sự')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

export function useDeleteEmployee() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => employeeApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa nhân sự')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

/** Đổi ảnh đại diện. Ảnh nằm trên tài khoản đăng nhập nên phải nạp lại hồ sơ. */
export function useUploadEmployeeAvatar(employeeId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => employeeApi.uploadAvatar(employeeId, file),
    onSuccess: () => {
      toast.success('Đã cập nhật ảnh đại diện')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}
