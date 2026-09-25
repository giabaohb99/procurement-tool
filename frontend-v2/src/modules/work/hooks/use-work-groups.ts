import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { workApi } from '../api/work-api'

/**
 * Hook cho NHÓM dự án — bao-CR-482.
 *
 * Cửa API (sửa nhóm · lưu trữ · thành viên nhóm) có từ bao-CR-216 nhưng chưa màn
 * nào gọi: nhóm tạo xong là không đổi tên, không mời ai, không lưu trữ được từ
 * giao diện. Thành viên nhóm kế thừa vai trò xuống MỌI dự án bên trong (A-09),
 * nên đây chính là chỗ phân quyền cho cả cụm một lần.
 */
export function useWorkGroupMembers(groupId?: number) {
  return useQuery({
    queryKey: queryKeys.work.groupMembers(groupId ?? 0),
    queryFn: () => workApi.groupMembers(groupId as number),
    enabled: typeof groupId === 'number' && groupId > 0,
  })
}

export function useUpdateWorkGroup() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, values }: { id: number; values: Record<string, unknown> }) =>
      workApi.updateGroup(id, values),
    onSuccess: () => {
      toast.success('Đã lưu nhóm')
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.all })
    },
  })
}

export function useArchiveWorkGroup() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => workApi.archiveGroup(id),
    onSuccess: () => {
      toast.success('Đã lưu trữ nhóm')
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.all })
    },
  })
}

/** Mời vào nhóm; người đã có trong nhóm thì backend ĐỔI vai trò (cùng cửa). */
export function useAddWorkGroupMember(groupId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (values: { employee_id: number; role: number }) =>
      workApi.addGroupMember(groupId, values),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.groupMembers(groupId) })
      //  Vai trò nhóm kế thừa xuống dự án con → vai trò hiệu lực trên từng dự án
      //  đổi theo, phải nạp lại cả cụm chứ không chỉ danh sách thành viên nhóm.
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.all })
    },
  })
}

export function useRemoveWorkGroupMember(groupId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (memberId: number) => workApi.removeGroupMember(groupId, memberId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.groupMembers(groupId) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.all })
    },
  })
}
