import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { botMemoryApi, type BotMemory } from '../api/bot-memory-api'

/** Trí nhớ bot giữ về chính mình (ai-CR-138) — tab «Bot nhớ gì về tôi» ở Trang cá nhân. */
export function useBotMemory() {
  return useQuery({
    queryKey: queryKeys.system.botMemory(),
    queryFn: () => botMemoryApi.get(),
  })
}

/** Mọi thao tác ghi đều trả lại ảnh chụp sổ mới — đặt thẳng vào cache, khỏi gọi lại. */
export function useBotMemoryAction<TArgs>(fn: (args: TArgs) => Promise<BotMemory>, done: string) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: (data) => {
      queryClient.setQueryData(queryKeys.system.botMemory(), data)
      toast.success(done)
    },
  })
}
