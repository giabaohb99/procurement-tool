import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { departmentApi } from '../api/department-api'
import type { DepartmentFormValues } from '../schemas/department-schema'
import type { DepartmentCompanyInput } from '../types/department'

/**
 * Các CẶP (phòng ban × pháp nhân) của những pháp nhân đang chọn.
 *
 * Chưa chọn pháp nhân nào thì KHÔNG gọi: một danh sách phòng ban không kèm pháp
 * nhân là thứ không dùng được ở nơi gọi (phạm vi áp dụng của văn bản), bày ra
 * chỉ mời người ta chọn nhầm.
 */
export function useDepartmentsByCompanies(companyIds: number[]) {
  return useQuery({
    queryKey: queryKeys.hr.departmentsByCompanies(companyIds),
    queryFn: () => departmentApi.byCompanies(companyIds),
    enabled: companyIds.length > 0,
    //  Giữ danh sách cũ trong lúc nạp danh sách mới: bỏ tick một pháp nhân là ô
    //  chọn phòng ban chớp trắng rồi hiện lại, ngay dưới tay người đang bấm.
    placeholderData: keepPreviousData,
  })
}

/**
 * Danh sách phòng ban. Tham số tìm kiếm là `q` (tên phòng ban HOẶC tên trưởng
 * bộ phận), không phải `name` — xem chú thích ở `department-api.ts`.
 *
 * `enabled`: backend gác `department.read`. Màn nào chỉ MƯỢN danh mục này
 * (hộp thoại phạm vi ở màn Phân quyền) phải tự tắt khi thiếu quyền — cứ mount
 * là gọi thì người dùng ăn 403, mà 403 trên GET không bật toast nên ô chỉ hiện
 * rỗng và họ tưởng "chưa khai phòng ban nào". Cùng khuôn với `useCompanies` /
 * `useEmployees`.
 */
export function useDepartments(params: ListParams = {}, options: { enabled?: boolean } = {}) {
  const query: ListParams = {
    page: 1,
    page_size: appConfig.defaultPageSize,
    ...params,
  }

  return useQuery({
    queryKey: queryKeys.hr.departments(query),
    queryFn: () => departmentApi.list(query),
    placeholderData: keepPreviousData,
    enabled: options.enabled ?? true,
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
