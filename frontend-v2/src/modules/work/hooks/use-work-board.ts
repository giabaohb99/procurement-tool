import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { workTaskApi } from '../api/work-task-api'
import type { WorkBoard, WorkTask } from '../types/work'
import { applyMove, type KanbanDropPlace } from '../utils/kanban-drop'

/** Bảng kanban của một list: cột + task cha, một lượt gọi (D-01). */
export function useWorkBoard(listId?: number) {
  return useQuery({
    queryKey: queryKeys.work.board(listId ?? 0),
    queryFn: () => workTaskApi.board(listId as number),
    enabled: typeof listId === 'number' && listId > 0,
  })
}

export function useWorkTask(taskId?: number) {
  return useQuery({
    queryKey: queryKeys.work.task(taskId ?? 0),
    queryFn: () => workTaskApi.get(taskId as number),
    enabled: typeof taskId === 'number' && taskId > 0,
  })
}

/** Mọi khóa cần làm mới sau khi đụng vào một task. */
function invalidateTask(
  queryClient: ReturnType<typeof useQueryClient>,
  listId: number,
  taskId?: number,
) {
  void queryClient.invalidateQueries({ queryKey: queryKeys.work.board(listId) })
  void queryClient.invalidateQueries({ queryKey: queryKeys.work.lists(false) })
  if (taskId) void queryClient.invalidateQueries({ queryKey: queryKeys.work.task(taskId) })
}

export function useCreateTask(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (values: Parameters<typeof workTaskApi.create>[0]) =>
      workTaskApi.create(values),
    onSuccess: () => invalidateTask(queryClient, listId),
  })
}

/**
 * Sửa task — dùng cho cả kéo thả (`section_id` + `sort_order`) lẫn tick hoàn thành.
 *
 * **Cập nhật lạc quan**: thả thẻ là nó nằm yên chỗ mới ngay, API chạy sau
 * (§4 của `05-giao-dien.md`). Lỗi thì trả bảng về đúng ảnh chụp trước đó và
 * báo bằng toast — không để thẻ đứng sai chỗ mà người dùng tưởng đã lưu.
 */
export function useUpdateTask(listId: number) {
  const queryClient = useQueryClient()
  const boardKey = queryKeys.work.board(listId)

  return useMutation({
    mutationFn: ({ id, values }: { id: number; values: Record<string, unknown> }) =>
      workTaskApi.update(id, values),

    onMutate: async ({ id, values }) => {
      await queryClient.cancelQueries({ queryKey: boardKey })
      const snapshot = queryClient.getQueryData<WorkBoard>(boardKey)
      if (snapshot) {
        queryClient.setQueryData<WorkBoard>(boardKey, {
          ...snapshot,
          tasks: snapshot.tasks.map((t) => (t.id === id ? { ...t, ...values } as WorkTask : t)),
        })
      }
      return { snapshot }
    },

    onError: (_err, _vars, context) => {
      if (context?.snapshot) queryClient.setQueryData(boardKey, context.snapshot)
      toast.error('Không lưu được thay đổi, đã trả về như cũ')
    },

    onSettled: (_data, _err, variables) => invalidateTask(queryClient, listId, variables.id),
  })
}

/**
 * Kéo thả kanban — đổi cột và/hoặc thứ tự trong cột.
 *
 * Tách khỏi `useUpdateTask` vì đây KHÔNG phải một phép sửa trường: máy chủ đánh
 * số lại cả cột đích, nên ảnh lạc quan cũng phải đánh số lại y hệt
 * (`applyMove`). Vá mỗi `sort_order` của một thẻ như trước thì thẻ đứng đúng chỗ
 * một nhịp rồi nhảy đi khi refetch về.
 */
export function useMoveTask(listId: number) {
  const queryClient = useQueryClient()
  const boardKey = queryKeys.work.board(listId)

  return useMutation({
    mutationFn: ({ taskId, place }: { taskId: number; place: KanbanDropPlace }) =>
      workTaskApi.move(taskId, place.sectionId, place.beforeTaskId),

    onMutate: async ({ taskId, place }) => {
      await queryClient.cancelQueries({ queryKey: boardKey })
      const snapshot = queryClient.getQueryData<WorkBoard>(boardKey)
      if (snapshot) {
        queryClient.setQueryData<WorkBoard>(boardKey, {
          ...snapshot,
          tasks: applyMove(snapshot.tasks, taskId, place),
        })
      }
      return { snapshot }
    },

    onError: (_err, _vars, context) => {
      if (context?.snapshot) queryClient.setQueryData(boardKey, context.snapshot)
      toast.error('Không chuyển được thẻ, đã trả về như cũ')
    },

    onSettled: (_data, _err, variables) => invalidateTask(queryClient, listId, variables.taskId),
  })
}

export function useDeleteTask(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (taskId: number) => workTaskApi.remove(taskId),
    onSuccess: () => {
      toast.success('Đã xóa công việc')
      invalidateTask(queryClient, listId)
    },
  })
}

export function useCreateSubtask(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId, title }: { taskId: number; title: string }) =>
      workTaskApi.createSubtask(taskId, { title }),
    onSuccess: (_data, variables) => invalidateTask(queryClient, listId, variables.taskId),
  })
}

export function useSetAssignees(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId, picIds }: { taskId: number; picIds: number[] }) =>
      workTaskApi.setAssignees(taskId, picIds),
    onSuccess: (_data, variables) => invalidateTask(queryClient, listId, variables.taskId),
  })
}

export function useSetTaskTags(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId, tagIds }: { taskId: number; tagIds: number[] }) =>
      workTaskApi.setTags(taskId, tagIds),
    onSuccess: (_data, variables) => invalidateTask(queryClient, listId, variables.taskId),
  })
}

export function useSetTaskLabel(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      taskId,
      fieldId,
      optionId,
    }: {
      taskId: number
      fieldId: number
      optionId: number | null
    }) => workTaskApi.setLabel(taskId, fieldId, optionId),
    onSuccess: (_data, variables) => invalidateTask(queryClient, listId, variables.taskId),
  })
}
