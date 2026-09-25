import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { agentHubApi } from '../api/agent-hub-api'

/** Liên kết Telegram của chính mình (ai-CR-038) — tab «Telegram» ở Trang cá nhân. */
export function useTelegramLinks() {
  return useQuery({
    queryKey: queryKeys.system.telegramLinks(),
    queryFn: () => agentHubApi.myLinks(),
  })
}

/** Mã một lần hiện ra trên màn — KHÔNG đưa vào cache query: làm mới trang thì mã cũ phải mất. */
export function useCreateTelegramLinkCode() {
  return useMutation({ mutationFn: () => agentHubApi.createLinkCode() })
}

export function useRemoveTelegramLink() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => agentHubApi.removeLink(id),
    onSuccess: () => {
      toast.success('Đã gỡ liên kết Telegram.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.telegramLinks() })
    },
  })
}

/** Mức chuông ERP chuyển sang một chat (ai-CR-059). */
export function useSetTelegramNotifyMode() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: ({ id, notify_mode }: { id: number; notify_mode: number }) => agentHubApi.setLinkNotifyMode(id, notify_mode),
    onSuccess: () => {
      toast.success('Đã đổi mức chuông.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.telegramLinks() })
    },
  })
}
