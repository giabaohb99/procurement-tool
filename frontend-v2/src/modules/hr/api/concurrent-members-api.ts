import { apiGet } from '@/core/api'
import type { ConcurrentMembersResult } from '../types/concurrent-member'

/** Tham số của `GET /api/employee-concurrents` — `department_id` bắt buộc, backend trả 422 nếu thiếu. */
export interface ConcurrentMembersParams {
  department_id: number
  /** Chỉ lấy kiêm nhiệm ở công ty này (phòng dùng chung nhiều công ty). */
  company_id?: number
}

/** Người kiêm nhiệm ở một phòng — backend lọc theo phạm vi xem hồ sơ của người gọi (quyền `employee.read`). */
export const concurrentMembersApi = {
  list: (params: ConcurrentMembersParams) =>
    apiGet<ConcurrentMembersResult>('/api/employee-concurrents', { params }),
}
