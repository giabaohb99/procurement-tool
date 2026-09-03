import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'

import { queryKeys } from '@/shared/constants/query-keys'
import { taskSupportApi } from '../api/task-support-api'

/**
 * Bình luận + đính kèm của một công việc.
 *
 * Mọi mutation đều làm mới **hai** chỗ: khối đang mở (bình luận / đính kèm) và
 * `board(listId)` — vì huy hiệu số bình luận nằm trên THẺ KANBAN, ngoài panel.
 * Quên vế thứ hai thì gửi xong bình luận, đóng panel lại vẫn thấy số cũ.
 */

/** Bình luận của một việc. `taskId = 0` (panel đóng) thì không gọi gì. */
export function useTaskComments(taskId: number) {
  //  Con trỏ «xem thêm bình luận cũ». Giữ ở hook chứ không ở component: nó phải
  //  nằm trong khóa truy vấn, không thì bấm xem thêm là đọc lại đúng bản cũ.
  const [beforeId, setBeforeId] = useState(0)

  const query = useQuery({
    queryKey: [...queryKeys.work.taskComments(taskId), beforeId],
    queryFn: () => taskSupportApi.listComments(taskId, beforeId),
    enabled: taskId > 0,
  })

  return {
    ...query,
    /** Lùi con trỏ về bình luận cũ nhất đang hiện để lấy thêm một trang nữa. */
    loadOlder: () => setBeforeId(query.data?.oldest_id ?? 0),
    resetPaging: () => setBeforeId(0),
  }
}

/** Người gợi ý khi gõ `@`. Chỉ gọi khi ô soạn đang thực sự mở bảng gợi ý. */
export function useTaskMentionable(taskId: number, q: string, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.work.taskMentionable(taskId, q),
    queryFn: () => taskSupportApi.listMentionable(taskId, q),
    enabled: enabled && taskId > 0,
    //  Danh sách người gần như không đổi trong một phiên gõ; hỏi lại mỗi ký tự
    //  là một tràng lượt gọi cho cùng một câu trả lời.
    staleTime: 60_000,
  })
}

export function useCreateTaskComment(taskId: number, listId: number) {
  const qc = useQueryClient()
  return useMutation({
    /**
     * Hai nhịp khi có tệp: tải tệp lấy `file_id` rồi mới gửi bình luận.
     *
     * Bắt buộc, không phải chọn lựa — backend cấm gắn tệp vào bình luận bằng
     * cửa khác (`_deny_comment`), tệp chỉ được nhận ngay lúc tạo qua `file_ids`.
     */
    mutationFn: async ({ body, files }: { body: string; files: File[] }) => {
      const uploaded = files.length ? await taskSupportApi.uploadCommentFiles(files) : []
      return taskSupportApi.createComment(
        taskId,
        body,
        uploaded.map((f) => f.file_id),
      )
    },
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.work.taskComments(taskId) })
      void qc.invalidateQueries({ queryKey: queryKeys.work.board(listId) })
      void qc.invalidateQueries({ queryKey: queryKeys.work.task(taskId) })
    },
  })
}

export function useDeleteTaskComment(taskId: number, listId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (commentId: number) => taskSupportApi.deleteComment(commentId),
    onSuccess: () => {
      void qc.invalidateQueries({ queryKey: queryKeys.work.taskComments(taskId) })
      void qc.invalidateQueries({ queryKey: queryKeys.work.board(listId) })
      void qc.invalidateQueries({ queryKey: queryKeys.work.task(taskId) })
    },
  })
}

// ── Đính kèm cấp công việc ──────────────────────────────────────────────────────

export function useTaskAttachments(taskId: number) {
  return useQuery({
    queryKey: queryKeys.work.taskAttachments(taskId),
    queryFn: () => taskSupportApi.listAttachments(taskId),
    enabled: taskId > 0,
  })
}

export function useUploadTaskAttachments(taskId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (files: File[]) => taskSupportApi.uploadAttachments(taskId, files),
    onSuccess: () =>
      void qc.invalidateQueries({ queryKey: queryKeys.work.taskAttachments(taskId) }),
  })
}

export function useDeleteTaskAttachment(taskId: number) {
  const qc = useQueryClient()
  return useMutation({
    mutationFn: (linkId: number) => taskSupportApi.deleteAttachment(linkId),
    onSuccess: () =>
      void qc.invalidateQueries({ queryKey: queryKeys.work.taskAttachments(taskId) }),
  })
}
