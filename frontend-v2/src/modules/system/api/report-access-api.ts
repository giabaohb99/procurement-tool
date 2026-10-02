import { apiDelete, apiGet, apiPost } from '@/core/api'
import type {
  GrantReportAccessInput,
  GrantReportAccessResult,
  ReportAccessItem,
} from '../types/report-access'

const BASE_URL = '/api/report-access'

/** API cấu hình «ai xem được báo cáo nào» — gác `role.read`/`role.write` ở backend. */
export const reportAccessApi = {
  /** 13 báo cáo, ĐÚNG thứ tự khóa 1..13, mỗi báo cáo kèm mọi dòng đang gán. */
  list: () => apiGet<ReportAccessItem[]>(BASE_URL),

  grant: (key: number, payload: GrantReportAccessInput) =>
    apiPost<GrantReportAccessResult>(`${BASE_URL}/${key}/grants`, payload),

  /** Thu hồi = đánh dấu `revoked_at`, không xóa dòng. */
  revoke: (accessId: number, reason: string) =>
    apiDelete<void>(`${BASE_URL}/grants/${accessId}`, { data: { reason } }),
}
