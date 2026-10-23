import { apiGet, apiPost, apiPut } from '@/core/api'
import type { PaginatedResult } from '@/shared/types/api'
import type {
  AiPlanApproveResult,
  AiPlanDetail,
  AiPlanDocument,
  AiPlanSummary,
} from '../types/ai-plan'

/**
 * Đề xuất kế hoạch AI (kh-AI1-3, doc `erp/tai-lieu-ai/22` §5.2). Chỉ CHỦ đề xuất thấy
 * và thao tác được; đề xuất của người khác trả 404 như đề xuất không tồn tại.
 */
export const aiPlanApi = {
  list: (params: { status?: number; page: number; page_size: number }) =>
    apiGet<PaginatedResult<AiPlanSummary>>('/api/ai-plans', { params }),

  get: (id: number) => apiGet<AiPlanDetail>(`/api/ai-plans/${id}`),

  /** Lưu bản sửa (chỉ khi Chờ duyệt). Lỗi 422 `PLAN_INVALID` kèm `details.problems`. */
  save: (id: number, plan: AiPlanDocument) => apiPut<AiPlanDetail>(`/api/ai-plans/${id}`, { plan }),

  /** Duyệt — gửi kèm bản đang sửa để máy chủ lưu trước rồi mới dựng bảng Dự án. */
  approve: (id: number, plan: AiPlanDocument) =>
    apiPost<AiPlanApproveResult>(`/api/ai-plans/${id}/approve`, { plan }),

  reject: (id: number, reason: string) => apiPost<AiPlanDetail>(`/api/ai-plans/${id}/reject`, { reason }),
}
