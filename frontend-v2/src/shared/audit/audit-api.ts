import { apiGet } from '@/core/api'

/** Một dòng nhật ký — khớp response của `GET /api/audit-logs`. */
export interface AuditLogEntry {
  action: string
  /** Nhãn tiếng Việt do backend dựng sẵn ("Tạo mới", "Duyệt"…). */
  action_label: string
  message?: string
  entity_id: number
  /** Tên người thao tác, backend đã tra sẵn. */
  by: string
  at: string
}

/**
 * Nhật ký thao tác trên một bản ghi.
 *
 * ⚠️ Endpoint chỉ yêu cầu đăng nhập (`get_current_user`), KHÔNG kiểm tra quyền
 * theo entity — đừng dùng nó để suy ra người dùng có quyền xem bản ghi hay không.
 */
export const auditApi = {
  list: (entity: string, entityId: number, limit = 100) =>
    apiGet<AuditLogEntry[]>('/api/audit-logs', {
      params: { entity, entity_id: entityId, limit },
    }),
}
