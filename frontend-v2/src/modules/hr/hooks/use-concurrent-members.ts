import { useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { concurrentMembersApi, type ConcurrentMembersParams } from '../api/concurrent-members-api'

/**
 * Người kiêm nhiệm ở một phòng ban (bảng "Kiêm nhiệm tại phòng này", `kind=1`) hoặc một công ty (bảng "Kiêm nhiệm tại
 * công ty này", `kind=2`). Chỉ gọi khi có id phòng hoặc id công ty `> 0` — backend trả 422 khi thiếu cả hai. `enabled`
 * để màn tự tắt khi thiếu quyền `employee.read` — 403 trên GET không bật toast nên cứ gọi thì bảng chỉ lặng lẽ rỗng.
 */
export function useConcurrentMembers(params: ConcurrentMembersParams, options: { enabled?: boolean } = {}) {
  const hasTarget = (params.department_id ?? 0) > 0 || (params.company_id ?? 0) > 0
  return useQuery({
    queryKey: queryKeys.hr.concurrentMembers(params),
    queryFn: () => concurrentMembersApi.list(params),
    enabled: hasTarget && (options.enabled ?? true),
  })
}
