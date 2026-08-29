import { apiGet } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type {
  PurchaseOrder,
  PurchaseRequest,
  Survey,
  SurveyRequest,
} from '../types/purchase-document'
import type { PurchaseProgressResult } from '../types/purchase-progress'
import type { SurveyProgressResult } from '../types/survey-progress-types'
import type { SurveyReportResult } from '../types/survey-report'

/**
 * Tầng API cho 4 chứng từ mua hàng + 2 báo cáo. Gom một file vì mỗi endpoint
 * chỉ là một lời gọi GET — tách sáu file rỗng ruột chỉ tốn công lần theo.
 *
 * ⚠️ Mỗi endpoint có whitelist lọc riêng ở `service.FILTERABLE` của backend.
 * Ngoài whitelist đó, controller còn tự xử vài tham số qua BẢNG CON, gửi sai
 * tên thì backend im lặng bỏ qua:
 *   YCMH  -> company_id, assignee, item_group (dòng PYC)
 *   YCBG  -> company_id, assignee, item_group (dòng YCBG)
 *   ĐMH   -> company_id, item_group, invoice_no (dòng ĐMH)
 *   KS    -> product_code (dòng sản phẩm khảo sát)
 */
export const purchaseDocumentApi = {
  listPurchaseRequests: (params: ListParams) =>
    apiGet<PaginatedResult<PurchaseRequest>>('/api/purchase-requests', { params }),

  listSurveyRequests: (params: ListParams) =>
    apiGet<PaginatedResult<SurveyRequest>>('/api/survey-requests', { params }),

  listPurchaseOrders: (params: ListParams) =>
    apiGet<PaginatedResult<PurchaseOrder>>('/api/purchase-orders', { params }),

  listSurveys: (params: ListParams) =>
    apiGet<PaginatedResult<Survey>>('/api/surveys', { params }),

  /** Báo cáo tiến độ theo từng lần giao hàng. */
  listPurchaseProgress: (params: ListParams) =>
    apiGet<PurchaseProgressResult>('/api/purchase-progress', { params }),

  /** Tiến độ báo giá theo từng dòng yêu cầu khảo sát. */
  listSurveyProgress: (params: ListParams) =>
    apiGet<SurveyProgressResult>('/api/survey-progress', { params }),

  /** Báo cáo khảo sát, cắt theo DÒNG khảo sát; kèm tổng số theo trạng thái duyệt. */
  listSurveyReportLines: (params: ListParams) =>
    apiGet<SurveyReportResult>('/api/survey-report/lines', { params }),
}
