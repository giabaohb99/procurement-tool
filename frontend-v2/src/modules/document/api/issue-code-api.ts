import { apiGet, apiPatch } from '@/core/api'
import type { IssueCodeGroups, IssueCodeUpdateInput } from '../types/issue-code'

const BASE_URL = '/api/issue-codes'

/**
 * Mã đưa vào số hiệu — đường RIÊNG chỉ chạm đúng cột mã.
 *
 * Không gọi `PATCH /api/companies/{id}` hay `/api/departments/{id}`: hai đường
 * đó gác bằng quyền Nhân sự, mà người khai quy tắc đánh số là văn thư. Đường
 * này gác bằng `doc_type.write` — chính quyền đang mở trang Quy tắc đánh số —
 * và cũng chỉ ghi được đúng cột mã.
 */
export const issueCodeApi = {
  list: () => apiGet<IssueCodeGroups>(BASE_URL),

  update: (payload: IssueCodeUpdateInput) =>
    apiPatch<{ cu: string; moi: string; da_cap_so: boolean }>(BASE_URL, payload),
}
