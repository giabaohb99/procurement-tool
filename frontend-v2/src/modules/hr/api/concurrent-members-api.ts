import { apiGet } from '@/core/api'
import type { ConcurrentMembersResult } from '../types/concurrent-member'

/**
 * Tham số của `GET /api/employee-concurrents` (duoc-CR-756) — cần ít nhất một trong `department_id` / `company_id`
 * (thiếu cả hai: 422). `kind` lọc theo loại: 1 Phòng ban (trang phòng ban), 2 Công ty (trang công ty); vắng = cả hai.
 */
export interface ConcurrentMembersParams {
  department_id?: number
  company_id?: number
  kind?: number
}

/** Người kiêm nhiệm ở một phòng / công ty — backend lọc theo phạm vi xem hồ sơ của người gọi (quyền `employee.read`). */
export const concurrentMembersApi = {
  list: (params: ConcurrentMembersParams) =>
    apiGet<ConcurrentMembersResult>('/api/employee-concurrents', { params }),
}
