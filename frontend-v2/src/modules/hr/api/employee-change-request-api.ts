import { apiGet, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { EmployeeFamily } from '../types/employee'
import type {
  ChangeRequestPayload,
  EmployeeChangeRequest,
} from '../types/employee-change-request'

const BASE_URL = '/api/employees'

/**
 * Bóc `{items}` của các cửa «của tôi». Nhận cả mảng trần cho chắc: `/me/contacts` (bao-CR-508)
 * trả mảng trần, còn hợp đồng duoc-CR-676 chốt `{items}` — lệch một bên thì màn vẫn đúng.
 */
function unwrapItems<T>(data: { items: T[] } | T[] | null | undefined): T[] {
  if (Array.isArray(data)) return data
  return data?.items ?? []
}

/**
 * ĐỀ NGHỊ SỬA HỒ SƠ (duoc-CR-676) — nhân viên tự khai, phòng Nhân sự duyệt rồi mới áp.
 *
 * Hai cụm cửa:
 * - `/me/...` chỉ đòi ĐĂNG NHẬP, hồ sơ lấy từ phiên (cùng lý lẽ `/me/contact`, bao-CR-508);
 * - `/change-requests/...` của phòng Nhân sự, gác `employee.write` + phạm vi; duyệt yêu cầu có
 *   ô nhạy cảm còn đòi `employee_sensitive.read`, và không ai tự duyệt đề nghị của chính mình.
 *
 * ⚠️ Mọi cửa nằm DƯỚI `/api/employees/` và backend khai TRƯỚC `/{eid}` — «me» / «change-requests»
 * rơi vào `eid: int` là 422.
 */
export const employeeChangeRequestApi = {
  /** Hộ gia đình của chính mình — nguồn điền sẵn tab «Hộ gia đình» và bảng VII của bản in. */
  getMyFamilies: async () =>
    unwrapItems(await apiGet<{ items: EmployeeFamily[] } | EmployeeFamily[]>(`${BASE_URL}/me/families`)),

  /** Các đề nghị của chính mình, mới nhất trước. */
  listMine: async () =>
    unwrapItems(
      await apiGet<{ items: EmployeeChangeRequest[] } | EmployeeChangeRequest[]>(
        `${BASE_URL}/me/change-requests`,
      ),
    ),

  /** Gửi đề nghị — thân CHỈ mang ô đã đổi (xem `buildChangeRequestPayload`). */
  submitMine: (payload: ChangeRequestPayload) =>
    apiPost<EmployeeChangeRequest>(`${BASE_URL}/me/change-requests`, payload),

  /** Rút đề nghị đang chờ duyệt. */
  withdrawMine: (id: number) =>
    apiPost<EmployeeChangeRequest>(`${BASE_URL}/me/change-requests/${id}/withdraw`),

  list: (params: ListParams) =>
    apiGet<PaginatedResult<EmployeeChangeRequest>>(`${BASE_URL}/change-requests`, { params }),

  pendingCount: () => apiGet<{ count: number }>(`${BASE_URL}/change-requests/pending-count`),

  getById: (id: number) => apiGet<EmployeeChangeRequest>(`${BASE_URL}/change-requests/${id}`),

  approve: (id: number) =>
    apiPost<EmployeeChangeRequest>(`${BASE_URL}/change-requests/${id}/approve`),

  /** Lý do bắt buộc, 1..500 ký tự (`RejectIn` của backend). */
  reject: (id: number, reason: string) =>
    apiPost<EmployeeChangeRequest>(`${BASE_URL}/change-requests/${id}/reject`, { reason }),
}
