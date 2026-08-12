import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { userAccountApi } from '../api/user-account-api'
import { EMPTY_USER_SCOPE, type UserScope } from '../types/user-account'

/**
 * Danh sách tài khoản đăng nhập, kèm lọc theo phòng ban / vai trò / tình trạng.
 *
 * `enabled=false` để khỏi gọi API khi người dùng không có quyền đọc `user`
 * (backend trả 403, không có gì để hiển thị).
 */
export function useUserAccounts(params: ListParams = {}, options: { enabled?: boolean } = {}) {
  const query: ListParams = {
    page: 1,
    page_size: appConfig.defaultPageSize,
    ...params,
  }

  return useQuery({
    queryKey: queryKeys.hr.userAccounts(query),
    queryFn: () => userAccountApi.list(query),
    placeholderData: keepPreviousData,
    enabled: options.enabled ?? true,
  })
}

export function useUserAccount(id: number) {
  return useQuery({
    queryKey: queryKeys.hr.userAccount(id),
    queryFn: () => userAccountApi.getById(id),
    enabled: id > 0,
  })
}

/** Tài khoản gắn với một nhân sự — `null` khi nhân sự chưa được cấp tài khoản. */
export function useEmployeeAccount(employeeId: number, enabled = true) {
  return useQuery({
    queryKey: queryKeys.hr.userAccounts({ employee_id: employeeId }),
    queryFn: () => userAccountApi.findByEmployee(employeeId),
    enabled: enabled && employeeId > 0,
  })
}

export function useAssignRoles(userId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (roleIds: number[]) => userAccountApi.assignRoles(userId, roleIds),
    onSuccess: () => {
      toast.success('Đã lưu vai trò')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

export function useSetUserActive() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ userId, isActive }: { userId: number; isActive: boolean }) =>
      userAccountApi.setActive(userId, isActive),
    onSuccess: (_data, variables) => {
      toast.success(variables.isActive ? 'Đã mở khóa tài khoản' : 'Đã khóa tài khoản')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

export function useDeleteUserAccount() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (userId: number) => userAccountApi.remove(userId),
    onSuccess: () => {
      toast.success('Đã xóa tài khoản')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

/**
 * Phạm vi dữ liệu của cặp (tài khoản × vai trò). Backend có thể trả thiếu
 * trường nên trộn với `EMPTY_USER_SCOPE` để phía màn hình luôn có đủ 6 mảng.
 */
export function useUserScope(userId: number, roleId: number | null) {
  return useQuery({
    queryKey: queryKeys.hr.userScope(userId, roleId ?? 0),
    queryFn: async () => {
      const scope = await userAccountApi.getScope(userId, roleId as number)
      return { ...EMPTY_USER_SCOPE, ...scope }
    },
    enabled: userId > 0 && !!roleId,
  })
}

export function useSaveUserScope(userId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ roleId, scope }: { roleId: number; scope: UserScope }) =>
      userAccountApi.setScope(userId, roleId, scope),
    onSuccess: (_data, variables) => {
      toast.success('Đã lưu phạm vi')
      void queryClient.invalidateQueries({
        queryKey: queryKeys.hr.userScope(userId, variables.roleId),
      })
    },
  })
}
