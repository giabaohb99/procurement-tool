import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import { botChangesApi } from '../api/bot-changes-api'

/**
 * Sổ thay đổi do bot ghi (ai-CR-185) — tab "Bot đã ghi gì" ở Trang cá nhân.
 *
 * `all = true` gọi `all=1` (của mọi người): nơi gọi PHẢI gác bằng `can('agent_group', 'read')` trước,
 * backend trả 403 cho người thiếu khóa.
 */
export function useBotChanges(limit: number, all: boolean) {
  return useQuery({
    queryKey: queryKeys.system.botChanges({ limit, all }),
    queryFn: () => botChangesApi.list(limit, all),
  })
}

/** Một dòng kèm ảnh `before` / `after` — chỉ nạp khi hộp chi tiết đang mở (`id` khác null). */
export function useBotChange(id: number | null) {
  return useQuery({
    queryKey: queryKeys.system.botChange(id ?? 0),
    queryFn: () => botChangesApi.get(id ?? 0),
    enabled: id !== null,
  })
}

/**
 * Hoàn tác một dòng. Thành công → toast `summary` của dòng ngược + làm tươi cả cây `bot-changes`
 * (dòng gốc đổi trạng thái, dòng ngược xuất hiện). Lỗi → toast đúng `message` trong phong bì
 * (API gọi `_silent` nên ở đây là chỗ DUY NHẤT hiện lỗi).
 */
export function useUndoChange() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => botChangesApi.undo(id),
    onSuccess: (result) => {
      toast.success(result.summary || 'Đã hoàn tác.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.botChangesAll() })
    },
    onError: (err) => toast.error(extractErrorMessage(err)),
  })
}
