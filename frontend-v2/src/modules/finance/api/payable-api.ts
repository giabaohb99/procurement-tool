import { apiGet, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { Payable, PayableSummary } from '../types/payable'

const BASE_URL = '/api/payables'

/**
 * Công nợ CHỈ ĐỌC: bảng do backend sinh ngầm lúc nhận hàng, không có endpoint
 * tạo/sửa/xóa.
 *
 * Hai lời gọi ăn CHUNG bộ tham số lọc — bốn ô tổng ở đầu trang phải là tổng của
 * đúng tập dòng đang hiện, không phải tổng toàn bảng.
 *
 * ⚠️ Whitelist lọc (`service.FILTERABLE`) chỉ có: supplier_code · po_code ·
 * invoice_no · source_type · status. Các tham số còn lại controller tự đọc:
 * `company_id`, `year` (mặc định NĂM HIỆN TẠI nếu không gửi), `aging`,
 * `incur_from`/`incur_to`, `amount_from`/`amount_to`, `ids`.
 */
export const payableApi = {
  list: (params: ListParams) => apiGet<PaginatedResult<Payable>>(BASE_URL, { params }),

  summary: (params: ListParams) => apiGet<PayableSummary>(`${BASE_URL}/summary`, { params }),

  /**
   * CR-268 — kế toán cấn trừ TIỀN TREO CẤP NCC (phiếu trả trước không gắn đơn) vào
   * khoản công nợ này. `amount` 0/bỏ trống = trừ tối đa min(treo còn lại, nợ còn lại).
   * Cần quyền `payable.write` — ngoại lệ duy nhất của phân hệ "chỉ đọc" này.
   */
  offsetPrepay: (id: number, amount: number) =>
    apiPost<Payable>(`${BASE_URL}/${id}/offset-prepay`, { amount }),
}
