import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { workTaskApi } from '../api/work-task-api'
import type { WorkBoard, WorkTask } from '../types/work'
import { WORK_TASK_STATUS } from '../types/work'
import { applyMove, type KanbanDropPlace } from '../utils/kanban-drop'
import { applyReorder } from '../utils/subtask-drop'

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

/**
 * Tick hoàn thành một VIỆC CON trong panel chi tiết (C-01).
 *
 * Tách khỏi `useUpdateTask` vì việc con KHÔNG nằm trong payload bảng (C-05), nên
 * dùng hàm kia thì hỏng cả hai đầu: `onMutate` dò `snapshot.tasks` — toàn task
 * cha — nên không khớp dòng nào; còn `onSettled` làm mới khóa `task(subtaskId)`
 * trong khi panel đang mở đọc `task(parentId)`. Hệ quả người dùng thấy: bấm ô
 * tick không có gì nhúc nhích, dù máy chủ ĐÃ ghi — mở lại panel mới thấy đổi.
 *
 * Ở đây ảnh lạc quan vá thẳng vào `subtasks` của TASK CHA và đếm lại `n/m` để
 * thanh tiến độ nhích cùng nhịp với ô tick.
 */
export function useToggleSubtask(listId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ subtaskId, done }: { parentId: number; subtaskId: number; done: boolean }) =>
      workTaskApi.update(subtaskId, {
        status: done ? WORK_TASK_STATUS.DONE : WORK_TASK_STATUS.OPEN,
      }),

    onMutate: async ({ parentId, subtaskId, done }) => {
      const parentKey = queryKeys.work.task(parentId)
      await queryClient.cancelQueries({ queryKey: parentKey })
      const snapshot = queryClient.getQueryData<WorkTask>(parentKey)
      if (snapshot?.subtasks) {
        const subtasks = snapshot.subtasks.map((s) =>
          s.id === subtaskId
            ? { ...s, status: done ? WORK_TASK_STATUS.DONE : WORK_TASK_STATUS.OPEN }
            : s,
        )
        queryClient.setQueryData<WorkTask>(parentKey, {
          ...snapshot,
          subtasks,
          subtask_done: subtasks.filter((s) => s.status === WORK_TASK_STATUS.DONE).length,
          subtask_total: subtasks.length,
        })
      }
      return { parentKey, snapshot }
    },

    onError: (_err, _vars, context) => {
      if (context?.snapshot) queryClient.setQueryData(context.parentKey, context.snapshot)
      toast.error('Không lưu được việc con, đã trả về như cũ')
    },

    onSettled: (_data, _err, variables) => invalidateTask(queryClient, listId, variables.parentId),
  })
}

/**
 * Kéo xếp lại VIỆC CON trong cụm của một việc cha (khung nhìn Danh sách).
 *
 * Cùng endpoint `move` với kéo thẻ kanban nhưng `section_id` để rỗng — việc con
 * không thuộc cột nào (C-05), máy chủ nhận thế là xếp lại trong cụm của cha.
 *
 * Ảnh lạc quan vá vào `subtasks` của khóa `task(parentId)` chứ không vào bảng,
 * vì đó chính là khóa mà các dòng việc con đang đọc — cùng lý do với
 * {@link useToggleSubtask}.
 */
export function useMoveSubtask(listId: number) {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({
      subtaskId,
      beforeTaskId,
    }: {
      parentId: number
      subtaskId: number
      beforeTaskId: number | null
    }) => workTaskApi.move(subtaskId, null, beforeTaskId),

    onMutate: async ({ parentId, subtaskId, beforeTaskId }) => {
      const parentKey = queryKeys.work.task(parentId)
      await queryClient.cancelQueries({ queryKey: parentKey })
      const snapshot = queryClient.getQueryData<WorkTask>(parentKey)
      if (snapshot?.subtasks) {
        queryClient.setQueryData<WorkTask>(parentKey, {
          ...snapshot,
          subtasks: applyReorder(snapshot.subtasks, subtaskId, beforeTaskId),
        })
      }
      return { parentKey, snapshot }
    },

    onError: (_err, _vars, context) => {
      if (context?.snapshot) queryClient.setQueryData(context.parentKey, context.snapshot)
      toast.error('Không xếp lại được việc con, đã trả về như cũ')
    },

    onSettled: (_data, _err, variables) => invalidateTask(queryClient, listId, variables.parentId),
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

export function useSetTaskLabel(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({
      taskId,
      fieldId,
      value,
    }: {
      taskId: number
      fieldId: number
      /** Đa hình theo kiểu trường — xem `workTaskApi.setLabel`. */
      value: unknown
    }) => workTaskApi.setLabel(taskId, fieldId, value),
    onSuccess: (_data, variables) => invalidateTask(queryClient, listId, variables.taskId),
  })
}
