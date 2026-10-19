import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import { aiSkillApi, aiUsageApi, myAiApi } from '../api/ai-skill-api'

/** «AI của tôi» (G8) + Tổng quan (G1) — K6, hợp đồng doc/agent-hub/06 §6. */

export function useSetupClients() {
  return useQuery({ queryKey: queryKeys.aiSkill.setupClients(), queryFn: () => myAiApi.setupClients(), staleTime: 5 * 60_000 })
}

export function useSetup(client: string) {
  return useQuery({
    queryKey: queryKeys.aiSkill.setup(client),
    queryFn: () => myAiApi.setup(client),
    enabled: client !== '',
    staleTime: 5 * 60_000,
  })
}

export function useMyKeys() {
  return useQuery({ queryKey: queryKeys.system.mcpKeys(), queryFn: () => myAiApi.myKeys() })
}

export function usePendingKeys() {
  return useQuery({ queryKey: queryKeys.aiSkill.pendingKeys(), queryFn: () => myAiApi.pendingKeys() })
}

/** Tạo / nhận khóa: KHÔNG toast khóa ra — khóa thô chỉ hiện trong khung trên màn, đúng một lần. */
export function useCreateMyKey() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (body: { name: string; scope: number; days: number }) => myAiApi.createKey(body),
    onSuccess: () => {
      toast.success('Đã tạo khóa. Chép ngay — khóa chỉ hiện một lần.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.mcpKeys() })
    },
  })
}

export function useClaimKey() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => myAiApi.claimKey(id),
    onSuccess: () => {
      toast.success('Đã nhận khóa. Chép ngay — khóa chỉ hiện một lần.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.aiSkill.pendingKeys() })
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.mcpKeys() })
    },
  })
}

export function useRemoveMyKey() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (id: number) => myAiApi.removeKey(id),
    onSuccess: () => {
      toast.success('Đã gỡ khóa.')
      void queryClient.invalidateQueries({ queryKey: queryKeys.system.mcpKeys() })
    },
  })
}

/** Kiểm tra kết nối: KHÔNG tự hỏi lại theo chu kỳ — người dùng bấm «Kiểm tra lại» sau khi hỏi AI một câu. */
export function useLastCall(keyId: number) {
  return useQuery({
    queryKey: queryKeys.aiSkill.lastCall(keyId),
    queryFn: () => myAiApi.lastCall(keyId),
    enabled: keyId > 0,
  })
}

export function useVisibleSkills() {
  return useQuery({ queryKey: queryKeys.aiSkill.visibleSkills(), queryFn: () => myAiApi.visibleSkills() })
}

/** 20 lượt gần nhất của chính mình (máy chủ tự giới hạn người thường chỉ thấy của mình). */
export function useMyRecentCalls() {
  return useQuery({
    queryKey: queryKeys.aiSkill.calls({ mine: true, size: 20 }),
    queryFn: () => aiUsageApi.listCalls({ page: 1, size: 20 }),
  })
}

export function useAiOverview(enabled: boolean) {
  return useQuery({ queryKey: queryKeys.aiSkill.overview(), queryFn: () => myAiApi.overview(), enabled })
}

/**
 * Tên của các skill trong bảng «Skill được đọc nhiều» — `ai-overview` chỉ trả `skill_id`. Mỗi id một lượt
 * `GET /skills/{id}` (tối đa 10, có cache); skill đã xóa / không đọc được thì để trống, màn tự in «Skill #id».
 */
export function useSkillTitles(ids: number[]) {
  const results = useQueries({
    queries: ids.map((id) => ({
      queryKey: queryKeys.aiSkill.skill(id),
      queryFn: () => aiSkillApi.getSkill(id),
      retry: false,
      staleTime: 5 * 60_000,
    })),
  })
  return new Map(ids.map((id, i) => [id, results[i]?.data?.title || results[i]?.data?.slug || ''] as const))
}
