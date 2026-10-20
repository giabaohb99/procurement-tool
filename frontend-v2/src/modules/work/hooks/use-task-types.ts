import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { workTaskTypeApi } from '../api/task-type-api'

/** Danh mục loại việc đang dùng — đổi hiếm nên giữ 5 phút, đủ cho một phiên làm việc. */
export function useActiveTaskTypes() {
  return useQuery({
    queryKey: queryKeys.work.taskTypes(),
    queryFn: async () => (await workTaskTypeApi.listActive()).items,
    staleTime: 5 * 60 * 1000,
  })
}

/**
 * Đánh giá kết quả một việc đã xong (duoc-CR-656).
 *
 * Không làm lạc quan: «Phải làm lại» mở lại việc và đổi cột/trạng thái ở nhiều chỗ, nên chờ máy chủ
 * rồi làm mới còn hơn vá tay rồi giật lùi. Lỗi (403 khi không phải người giao…) hiện nguyên câu của máy chủ.
 */
export function useSetTaskOutcome(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ taskId, outcome }: { taskId: number; outcome: number }) =>
      workTaskTypeApi.setOutcome(taskId, outcome),
    onSuccess: (_data, variables) => {
      toast.success('Đã lưu đánh giá')
      //  Cùng ba khóa với `invalidateTask` của `use-work-board` (hàm đó không export).
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.board(listId) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.lists(false) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.task(variables.taskId) })
    },
  })
}
