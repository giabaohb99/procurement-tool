import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { agentHubApi } from '../api/agent-hub-api'

/** Khóa Gemini cá nhân (ai-CR-053) — tab «Khóa AI» ở Trang cá nhân. Bot Telegram/Zalo dùng khóa này cho chính mình. */
export function useAiKey() {
  return useQuery({
    queryKey: queryKeys.system.aiKey(),
    queryFn: () => agentHubApi.myAiKey(),
  })
}

export function useSetAiKey() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (key: string) => agentHubApi.setAiKey(key),
    onSuccess: () => {
      toast.success('Đã lưu khóa Gemini. Bot sẽ dùng khóa này cho bạn.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.aiKey() })
    },
  })
}

export function useRemoveAiKey() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: () => agentHubApi.removeAiKey(),
    onSuccess: () => {
      toast.success('Đã gỡ khóa Gemini.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.aiKey() })
    },
  })
}

/** Khóa kết nối MCP cá nhân (ai-CR-063). Khóa thô chỉ nằm trong kết quả mutation, KHÔNG vào cache. */
export function useMcpKeys() {
  return useQuery({
    queryKey: queryKeys.system.mcpKeys(),
    queryFn: () => agentHubApi.myMcpKeys(),
  })
}

export function useCreateMcpKey() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: { name: string; scope: number; days: number }) => agentHubApi.createMcpKey(body),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.mcpKeys() })
    },
  })
}

export function useRemoveMcpKey() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => agentHubApi.removeMcpKey(id),
    onSuccess: () => {
      toast.success('Đã gỡ khóa MCP.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.mcpKeys() })
    },
  })
}
