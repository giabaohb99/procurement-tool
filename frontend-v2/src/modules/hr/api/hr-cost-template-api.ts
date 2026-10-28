import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { PaginatedResult } from '@/shared/types/api'

import type { HrCostGroup, HrCostTemplate, HrCostTemplatePayload } from '../types/hr-cost'

/** Nhóm chi phí — `make_crud_router` (đọc `headcount_plan.read`, ghi `headcount_plan.write`). */
export const HR_COST_GROUP_API_PATH = '/api/hr-cost-groups'
/** Mẫu khoản chi phí — list / get / create / patch / delete + `POST /{id}/duplicate`. */
export const HR_COST_TEMPLATE_API_PATH = '/api/hr-cost-templates'

/** Đủ chứa mọi nhóm / mẫu của tập đoàn trong một lượt (danh mục vài chục dòng). */
const LOOKUP_PAGE_SIZE = 500

export const hrCostApi = {
  listGroups: () =>
    apiGet<PaginatedResult<HrCostGroup>>(HR_COST_GROUP_API_PATH, {
      params: { page_size: LOOKUP_PAGE_SIZE, sort_by: 'sort_order', sort_dir: 'asc' },
    }),

  listTemplates: (params: Record<string, unknown> = {}) =>
    apiGet<PaginatedResult<HrCostTemplate>>(HR_COST_TEMPLATE_API_PATH, {
      params: { page_size: LOOKUP_PAGE_SIZE, ...params },
    }),

  getTemplate: (id: number) => apiGet<HrCostTemplate>(`${HR_COST_TEMPLATE_API_PATH}/${id}`),

  createTemplate: (payload: HrCostTemplatePayload) =>
    apiPost<HrCostTemplate>(HR_COST_TEMPLATE_API_PATH, payload),

  /** `items` thay NGUYÊN danh sách khoản của mẫu. Kế hoạch đã chép từ mẫu KHÔNG đổi theo. */
  updateTemplate: (id: number, payload: HrCostTemplatePayload) =>
    apiPatch<HrCostTemplate>(`${HR_COST_TEMPLATE_API_PATH}/${id}`, payload),

  removeTemplate: (id: number) => apiDelete<null>(`${HR_COST_TEMPLATE_API_PATH}/${id}`),

  duplicateTemplate: (id: number) => apiPost<HrCostTemplate>(`${HR_COST_TEMPLATE_API_PATH}/${id}/duplicate`, {}),
}
