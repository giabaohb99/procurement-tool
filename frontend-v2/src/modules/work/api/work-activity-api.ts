import { apiGet } from '@/core/api'

import type { WorkActivityActor, WorkActivityPage } from '../types/activity'

/**
 * Dòng hoạt động cấp dự án (D-09).
 *
 * ⚠️ **Không** dùng `/api/audit-logs` cho màn này: đường đó dùng chung cả hệ,
 * chỉ đòi đăng nhập và KHÔNG kiểm quyền theo entity (xem cảnh báo ở
 * `shared/audit/audit-api.ts`), lại chỉ lọc được đúng một `entity_id` — mà một
 * dự án có nhiều việc.
 */
export const workActivityApi = {
  list: (
    listId: number,
    params: { kind?: number | null; by?: number | null; offset?: number; limit?: number } = {},
  ) =>
    apiGet<WorkActivityPage>(`/api/work/lists/${listId}/activities`, {
      params: {
        //  Bỏ hẳn khóa khi không lọc: gửi `kind=null` là chuỗi "null" trên URL,
        //  backend ép kiểu hỏng và trả 422.
        ...(params.kind ? { kind: params.kind } : {}),
        ...(params.by ? { by: params.by } : {}),
        offset: params.offset ?? 0,
        limit: params.limit ?? 30,
      },
    }),

  actors: (listId: number) =>
    apiGet<WorkActivityActor[]>(`/api/work/lists/${listId}/activity-actors`),
}
