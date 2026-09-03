import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { workApi } from '../api/work-api'
import type { WorkBoard } from '../types/work'

/**
 * Cấu hình của một list: thành viên · cột · nhãn tùy biến.
 *
 * Tách khỏi `use-work-board` vì ba thứ này đổi hiếm nhưng đọc ở nhiều chỗ
 * (thẻ, panel chi tiết, hộp thoại) — để chung một khóa với bảng là mỗi lần kéo
 * thả lại nạp lại cả danh mục.
 */

export function useWorkMembers(listId?: number) {
  return useQuery({
    queryKey: queryKeys.work.members(listId ?? 0),
    queryFn: () => workApi.members(listId as number),
    enabled: typeof listId === 'number' && listId > 0,
  })
}

export function useWorkLabelFields(listId?: number) {
  return useQuery({
    queryKey: queryKeys.work.labelFields(listId ?? 0),
    queryFn: () => workApi.labelFields(listId as number),
    enabled: typeof listId === 'number' && listId > 0,
  })
}

export function useAddWorkMember(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (values: { employee_id: number; role: number }) =>
      workApi.addMember(listId, values),
    onSuccess: () => {
      toast.success('Đã mời vào danh sách')
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.members(listId) })
    },
  })
}

/**
 * Đổi vai trò của người ĐÃ ở trong dự án.
 *
 * Dùng chung endpoint với lời mời — `list_service.add_member` là upsert: gặp
 * người đã có thì ghi đè `role` chứ không báo trùng. Tách thành hook riêng chỉ
 * vì hai câu thông báo khác nhau; hiện «Đã mời vào danh sách» khi vừa hạ một
 * người từ Quản trị xuống Khách xem thì đọc như bấm nhầm nút.
 *
 * Dọn cả cụm `work.all` chứ không riêng danh sách thành viên: đổi vai trò của
 * CHÍNH MÌNH làm đổi `my_role` của bảng, tức đổi luôn những nút được phép bấm.
 */
export function useSetWorkMemberRole(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (values: { employee_id: number; role: number }) =>
      workApi.addMember(listId, values),
    onSuccess: () => {
      toast.success('Đã đổi vai trò')
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.all })
    },
  })
}

export function useRemoveWorkMember(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (memberId: number) => workApi.removeMember(listId, memberId),
    onSuccess: () => {
      toast.success('Đã gỡ thành viên')
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.members(listId) })
    },
  })
}

export function useCreateSection(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (values: { name: string; color?: string; sort_order?: number }) =>
      workApi.createSection(listId, values),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.board(listId) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.sections(listId) })
    },
  })
}

/**
 * Kéo đổi thứ tự CỘT.
 *
 * **Cập nhật lạc quan**: cột phải nằm yên chỗ mới ngay lúc buông tay. Không có
 * nhánh này thì cột bật về chỗ cũ rồi mới nhảy sang chỗ mới khi máy chủ trả lời
 * — đúng cái nháy đã phải vá cho thẻ.
 */
export function useMoveSection(listId: number) {
  const queryClient = useQueryClient()
  const boardKey = queryKeys.work.board(listId)

  return useMutation({
    mutationFn: ({ sectionId, beforeSectionId }: { sectionId: number; beforeSectionId: number | null }) =>
      workApi.moveSection(sectionId, beforeSectionId),

    onMutate: async ({ sectionId, beforeSectionId }) => {
      await queryClient.cancelQueries({ queryKey: boardKey })
      const snapshot = queryClient.getQueryData<WorkBoard>(boardKey)
      if (snapshot) {
        const rest = snapshot.sections.filter((s) => s.id !== sectionId)
        const moved = snapshot.sections.find((s) => s.id === sectionId)
        const at = beforeSectionId === null ? -1 : rest.findIndex((s) => s.id === beforeSectionId)
        if (moved) {
          const pos = at === -1 ? rest.length : at
          queryClient.setQueryData<WorkBoard>(boardKey, {
            ...snapshot,
            sections: [...rest.slice(0, pos), moved, ...rest.slice(pos)],
          })
        }
      }
      return { snapshot }
    },

    onError: (_err, _vars, context) => {
      if (context?.snapshot) queryClient.setQueryData(boardKey, context.snapshot)
      toast.error('Không xếp lại được cột, đã trả về như cũ')
    },

    onSettled: () => {
      void queryClient.invalidateQueries({ queryKey: boardKey })
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.sections(listId) })
    },
  })
}

export function useUpdateSection(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, values }: { id: number; values: Record<string, unknown> }) =>
      workApi.updateSection(id, values),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.board(listId) })
    },
  })
}

/** Xóa cột. Cột còn việc thì backend đòi `moveTo` — hộp thoại phải hỏi trước. */
export function useDeleteSection(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, moveTo }: { id: number; moveTo?: number }) =>
      workApi.deleteSection(id, moveTo),
    onSuccess: () => {
      toast.success('Đã xóa cột')
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.board(listId) })
    },
  })
}

export function useCreateLabelField(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (values: { name: string; field_type?: number }) =>
      workApi.createLabelField(listId, values),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.labelFields(listId) })
    },
  })
}

export function useUpdateLabelField(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      fieldId,
      values,
    }: {
      fieldId: number
      values: { name?: string; field_type?: number }
    }) => workApi.updateLabelField(fieldId, values),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.labelFields(listId) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.board(listId) })
    },
  })
}

export function useDeleteLabelField(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (fieldId: number) => workApi.deleteLabelField(fieldId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.labelFields(listId) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.board(listId) })
    },
  })
}

export function useCreateLabelOption(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      fieldId,
      values,
    }: {
      fieldId: number
      values: { name: string; color?: string; sort_order?: number }
    }) => workApi.createLabelOption(fieldId, values),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.labelFields(listId) })
    },
  })
}

export function useUpdateLabelOption(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      optionId,
      values,
    }: {
      optionId: number
      values: { name?: string; color?: string; sort_order?: number }
    }) => workApi.updateLabelOption(optionId, values),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.labelFields(listId) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.board(listId) })
    },
  })
}

export function useDeleteLabelOption(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (optionId: number) => workApi.deleteLabelOption(optionId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.labelFields(listId) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.board(listId) })
    },
  })
}
