import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { workApi } from '../api/work-api'

/**
 * Cấu hình của một list: thành viên · cột · tag · nhãn tùy biến.
 *
 * Tách khỏi `use-work-board` vì bốn thứ này đổi hiếm nhưng đọc ở nhiều chỗ
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

export function useWorkTags(listId?: number) {
  return useQuery({
    queryKey: queryKeys.work.tags(listId ?? 0),
    queryFn: () => workApi.tags(listId as number),
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

export function useTransferWorkList(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (employeeId: number) => workApi.transferList(listId, employeeId),
    onSuccess: () => {
      toast.success('Đã chuyển quyền sở hữu')
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.all })
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

export function useCreateTag(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (values: { name: string; color?: string }) => workApi.createTag(listId, values),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.tags(listId) })
    },
  })
}

export function useDeleteTag(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (tagId: number) => workApi.deleteTag(tagId),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.tags(listId) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.board(listId) })
    },
  })
}

export function useCreateLabelField(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (values: { name: string }) => workApi.createLabelField(listId, values),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.labelFields(listId) })
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
    mutationFn: ({ fieldId, values }: { fieldId: number; values: { name: string; color?: string } }) =>
      workApi.createLabelOption(fieldId, values),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.labelFields(listId) })
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
