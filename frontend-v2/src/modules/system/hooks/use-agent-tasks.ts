import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { agentHubApi, type AgentTaskListParams } from '../api/agent-hub-api'

/** Việc của bot Agent Hub (ai-CR-036). Dữ liệu đổi theo nhịp bot chạy nên làm tươi 30 giây. */
export function useAgentTasks(params: AgentTaskListParams) {
  return useQuery({
    queryKey: queryKeys.system.agentTasks(params as Record<string, unknown>),
    queryFn: () => agentHubApi.list(params),
    placeholderData: keepPreviousData,
    staleTime: 30 * 1000,
  })
}

export function useAgentTask(id: number) {
  return useQuery({
    queryKey: queryKeys.system.agentTask(id),
    queryFn: () => agentHubApi.detail(id),
    enabled: id > 0,
  })
}

export function useAgentStats(days: number) {
  return useQuery({
    queryKey: queryKeys.system.agentStats(days),
    queryFn: () => agentHubApi.stats(days),
    staleTime: 60 * 1000,
  })
}
