import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { assistantApi } from '../api/assistant-api'
import type { ChatRequest } from '../types/assistant'

/** Nhà cung cấp + model mặc định. Gần như bất biến trong phiên nên không tự nạp lại. */
export function useProviders() {
  return useQuery({
    queryKey: queryKeys.assistant.providers(),
    queryFn: () => assistantApi.providers(),
    staleTime: Infinity,
    // Bật/tắt trợ lý trả 403; đừng thử lại vô ích rồi mới hiện thông báo.
    retry: false,
  })
}

/**
 * Danh sách hội thoại của chính người dùng (server xếp mới trước).
 * `enabled`: bong bóng chat chỉ nạp khi người dùng MỞ nó — đừng gọi ngầm ở mọi trang.
 */
export function useConversations(options: { enabled?: boolean } = {}) {
  return useQuery({
    queryKey: queryKeys.assistant.conversations(),
    queryFn: () => assistantApi.conversations().then((r) => r.items),
    enabled: options.enabled ?? true,
  })
}

/** Chi tiết một hội thoại kèm tin. `id <= 0` = chưa chọn, không gọi. */
export function useConversation(id: number) {
  return useQuery({
    queryKey: queryKeys.assistant.conversation(id),
    queryFn: () => assistantApi.conversation(id),
    enabled: id > 0,
  })
}

/**
 * Gửi một câu hỏi. Mutation THUẦN — việc nạp lại cache do trang tự lo, vì trang
 * cần nạp xong chi tiết hội thoại TRƯỚC khi bỏ tin đang chờ, kẻo nháy mất câu
 * vừa gửi. Trang gọi bằng `mutateAsync` để điều phối đúng thứ tự.
 */
export function useSendMessage() {
  return useMutation({
    mutationFn: (body: ChatRequest) => assistantApi.chat(body),
  })
}

/** Xóa một hội thoại và làm mới danh sách. */
export function useDeleteConversation() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => assistantApi.remove(id),
    onSuccess: () => {
      void queryClient.invalidateQueries({
        queryKey: queryKeys.assistant.conversations(),
      })
      toast.success('Đã xóa hội thoại')
    },
  })
}
