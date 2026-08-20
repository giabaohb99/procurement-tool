import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { companyApi } from '../api/company-api'
import type { CompanyFormValues } from '../schemas/company-schema'

/**
 * Danh sách công ty. Lọc được cả mã số hiệu và cấp pháp nhân.
 *
 * `enabled`: backend chặn `company.read`. Màn nào chỉ mượn danh sách này để đổi
 * `company_id` thành tên (vd tab Hợp đồng của NCC) thì phải tự tắt khi thiếu
 * quyền, kẻo người dùng ăn một toast 403 chẳng liên quan gì tới việc đang làm.
 */
export function useCompanies(params: ListParams = {}, options: { enabled?: boolean } = {}) {
  const query: ListParams = {
    page: 1,
    page_size: appConfig.defaultPageSize,
    ...params,
  }

  return useQuery({
    queryKey: queryKeys.hr.companies(query),
    queryFn: () => companyApi.list(query),
    placeholderData: keepPreviousData,
    enabled: options.enabled ?? true,
  })
}

export function useCompany(id: number) {
  return useQuery({
    queryKey: queryKeys.hr.company(id),
    queryFn: () => companyApi.getById(id),
    enabled: id > 0,
  })
}

export function useSaveCompany() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: CompanyFormValues }) =>
      id ? companyApi.update(id, values) : companyApi.create(values),

    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã cập nhật công ty' : 'Đã thêm công ty')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

export function useDeleteCompany() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => companyApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa công ty')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

export function useUploadCompanyLogo(companyId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (file: File) => companyApi.uploadLogo(companyId, file),
    onSuccess: () => {
      toast.success('Đã cập nhật logo')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}
