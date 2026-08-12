import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { roleApi } from '../api/role-api'
import type { RolePermissionRow } from '../types/role'

/** Danh sách vai trò — backend trả mảng thô, không phân trang. */
export function useRoles() {
  return useQuery({
    queryKey: queryKeys.hr.roles(),
    queryFn: () => roleApi.list(),
  })
}

/**
 * Entity / action / scope để dựng ma trận. Gần như bất biến trong một phiên
 * làm việc nên để `staleTime` dài, tránh gọi lại mỗi lần đổi tab.
 */
export function usePermissionMeta() {
  return useQuery({
    queryKey: queryKeys.hr.permissionMeta(),
    queryFn: () => roleApi.meta(),
    staleTime: 30 * 60 * 1000,
  })
}

/** Ma trận quyền hiện tại của một vai trò. */
export function useRolePermissions(roleId: number) {
  return useQuery({
    queryKey: queryKeys.hr.rolePermissions(roleId),
    queryFn: () => roleApi.getPermissions(roleId),
    enabled: roleId > 0,
  })
}

export function useCreateRole() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: { code: string; name: string; description?: string }) =>
      roleApi.create(payload),
    onSuccess: () => {
      toast.success('Đã tạo vai trò')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.roles() })
    },
  })
}

export function useDeleteRole() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (roleId: number) => roleApi.remove(roleId),
    onSuccess: () => {
      toast.success('Đã xóa vai trò')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}

/**
 * Lưu cả ma trận quyền của vai trò.
 *
 * ⚠️ Backend cache hồ sơ phân quyền 60 giây trong tiến trình
 * (`_PERM_CACHE`) — người đang đăng nhập có thể phải chờ tới một phút mới thấy
 * quyền mới. Đây là hành vi của server, không phải cache của react-query.
 */
export function useSaveRolePermissions() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ roleId, rows }: { roleId: number; rows: RolePermissionRow[] }) =>
      roleApi.setPermissions(roleId, rows),
    onSuccess: (_data, variables) => {
      toast.success('Đã lưu phân quyền')
      void queryClient.invalidateQueries({
        queryKey: queryKeys.hr.rolePermissions(variables.roleId),
      })
    },
  })
}
