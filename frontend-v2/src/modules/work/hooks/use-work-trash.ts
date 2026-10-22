import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { workTaskApi } from '../api/work-task-api'

/** Việc đã xóa của dự án. Chỉ gọi khi hộp thùng rác đang mở (`enabled`). */
export function useWorkTrash(listId: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.work.trash(listId),
    queryFn: () => workTaskApi.trash(listId),
    enabled: enabled && listId > 0,
  })
}

export function useRestoreTask(listId: number) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (taskId: number) => workTaskApi.restore(taskId),
    onSuccess: () => {
      toast.success('Đã khôi phục công việc')
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.trash(listId) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.board(listId) })
      void queryClient.invalidateQueries({ queryKey: queryKeys.work.lists(false) })
    },
  })
}
