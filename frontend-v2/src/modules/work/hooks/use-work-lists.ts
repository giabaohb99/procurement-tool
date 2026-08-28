import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { workApi } from '../api/work-api'

/** Cây điều hướng bên trái (A-05) — nhóm → nhóm con → list, kèm list đứng lẻ. */
export function useWorkSidebar(includeArchived = false) {
  return useQuery({
    queryKey: queryKeys.work.sidebar(includeArchived),
    queryFn: () => workApi.sidebar(includeArchived),
  })
}

/** Danh sách phẳng mọi list mình thấy — dùng cho ô chọn, không cho sidebar. */
export function useWorkLists(includeArchived = false) {
  return useQuery({
    queryKey: queryKeys.work.lists(includeArchived),
    queryFn: () => workApi.lists(includeArchived),
  })
}

/** Bảng liệt kê DỰ ÁN — như `useWorkLists` nhưng kèm chủ sở hữu + thành viên. */
export function useWorkProjects(includeArchived = false) {
  return useQuery({
    queryKey: queryKeys.work.projects(includeArchived),
    queryFn: () => workApi.lists(includeArchived, true),
  })
}

export function useWorkList(id?: number) {
  return useQuery({
    queryKey: queryKeys.work.list(id ?? 0),
    queryFn: () => workApi.getList(id as number),
    enabled: typeof id === 'number' && id > 0,
  })
}

export function useCreateWorkList() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (values: { name: string; description?: string; group_id?: number | null }) =>
      workApi.createList(values),
    onSuccess: () => {
      toast.success('Đã tạo danh sách công việc')
      //  Reset cả cụm: list mới làm đổi sidebar, danh sách phẳng lẫn số đếm.
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.all })
    },
  })
}

export function useCreateWorkGroup() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (values: { name: string; parent_id?: number | null }) =>
      workApi.createGroup(values),
    onSuccess: () => {
      toast.success('Đã tạo nhóm')
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.all })
    },
  })
}

export function useUpdateWorkList() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, values }: { id: number; values: Record<string, unknown> }) =>
      workApi.updateList(id, values),
    onSuccess: () => {
      toast.success('Đã lưu danh sách')
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.all })
    },
  })
}

export function useArchiveWorkList() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => workApi.archiveList(id),
    onSuccess: () => {
      toast.success('Đã lưu trữ danh sách')
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.all })
    },
  })
}
