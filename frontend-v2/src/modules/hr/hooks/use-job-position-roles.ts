import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { jobPositionRoleApi } from '../api/job-position-role-api'

/** Gói quyền mặc định của chức vụ. `enabled=false` khi thiếu `role.read` (tránh toast 403 lúc mở tab). */
export function useJobPositionRoles(positionId: number, enabled = true) {
  return useQuery({
    queryKey: queryKeys.hr.jobPositionRoles(positionId),
    queryFn: () => jobPositionRoleApi.get(positionId),
    enabled: enabled && positionId > 0,
  })
}

export function useSaveJobPositionRoles(positionId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (roleIds: number[]) => jobPositionRoleApi.save(positionId, roleIds),
    onSuccess: () => {
      toast.success('Đã lưu quyền mặc định. Chưa áp cho người đang giữ chức vụ — bấm "Áp lại" nếu cần.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.jobPositionRoles(positionId) })
    },
  })
}

export function useApplyJobPositionRoles(positionId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => jobPositionRoleApi.apply(positionId),
    onSuccess: (r) => {
      toast.success(
        `Đã áp lại cho ${r.holders} người: ${r.changed_users} tài khoản đổi ` +
          `(thêm ${r.granted}, gỡ ${r.revoked})` +
          (r.skipped_self ? ` — bỏ qua tài khoản của chính bạn` : '') +
          (r.skipped_no_permission ? ` — bỏ qua ${r.skipped_no_permission} vai trò bạn không đủ quyền cấp` : ''),
      )
      //  Quyền của nhiều tài khoản vừa đổi → quét cả nhánh hr (tài khoản, vai trò) cho khỏi hiện số cũ.
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })
}
