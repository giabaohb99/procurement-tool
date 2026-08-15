import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { departmentApi } from '../api/department-api'
import type { DepartmentFormValues } from '../schemas/department-schema'
import type { DepartmentCompanyInput } from '../types/department'

/**
 * Danh sách phòng ban. Tham số tìm kiếm là `q` (tên phòng ban HOẶC tên trưởng
 * bộ phận), không phải `name` — xem chú thích ở `department-api.ts`.
 */
export function useDepartments(params: ListParams = {}) {
  const query: ListParams = {
    page: 1,
    page_size: appConfig.defaultPageSize,
    ...params,
  }

  return useQuery({
    queryKey: queryKeys.hr.departments(query),
    queryFn: () => departmentApi.list(query),
    placeholderData: keepPreviousData,
  })
}

export function useDepartment(id: number) {
  return useQuery({
    queryKey: queryKeys.hr.department(id),
    queryFn: () => departmentApi.getById(id),
    enabled: id > 0,
  })
}

export function useSaveDepartment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: DepartmentFormValues }) =>
      id ? departmentApi.update(id, values) : departmentApi.create(values),

    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã cập nhật phòng ban' : 'Đã thêm phòng ban')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

export function useDeleteDepartment() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => departmentApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa phòng ban')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

export function useDepartmentCompanies(id: number) {
  return useQuery({
    queryKey: queryKeys.hr.departmentCompanies(id),
    queryFn: () => departmentApi.listCompanies(id),
    enabled: id > 0,
  })
}

export function useSaveDepartmentCompanies(id: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (items: DepartmentCompanyInput[]) => departmentApi.replaceCompanies(id, items),
    onSuccess: () => {
      toast.success('Đã cập nhật pháp nhân áp dụng')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.departmentCompanies(id) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.department(id) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.departments() })
    },
  })
}
