import { apiGet } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'

export interface SystemAuditLogItem {
  id: number
  entity: string
  entity_id: number
  action: string
  action_label: string
  message: string
  by: string
  by_id: number | null
  at: string
}

export interface AuditLogListParams extends ListParams {
  entity?: string
  entity_id?: number
  action?: string
  search?: string
  created_by?: number
  from_date?: string
  to_date?: string
}

export const auditLogApi = {
  list: (params: AuditLogListParams) =>
    apiGet<PaginatedResult<SystemAuditLogItem>>('/api/audit-logs', { params }),

  /**
   * Nhật ký của MỘT entity, dạng mảng đơn — dùng cho thẻ lịch sử nhúng trong màn.
   *
   * ⚠️ Cùng một đường API với `list` nhưng KHÁC hình dữ liệu: backend trả mảng khi
   * lời gọi không có `page`, trả phong bì phân trang khi có. Gọi `list` rồi đọc
   * `.items` ở đây thì nhận `undefined` chứ không nhận lỗi — không chỗ nào đỏ lên,
   * chỉ thấy thẻ lịch sử rỗng vĩnh viễn.
   */
  listRecent: (entity: string, limit: number) =>
    apiGet<SystemAuditLogItem[]>('/api/audit-logs', { params: { entity, limit } }),
}
