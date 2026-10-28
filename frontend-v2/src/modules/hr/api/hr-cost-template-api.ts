import { apiGet } from '@/core/api'
import type { PaginatedResult } from '@/shared/types/api'

import type { HrCostGroup, HrCostTemplate } from '../types/hr-cost'

/** Nhóm chi phí — `make_crud_router` (đọc `headcount_plan.read`). Giao diện chỉ còn đọc để tự xếp nhóm. */
export const HR_COST_GROUP_API_PATH = '/api/hr-cost-groups'
/**
 * Mẫu khoản chi phí — màn quản lý mẫu đã gỡ (duoc-CR-690); trang kế hoạch chỉ còn ĐỌC mẫu «Mẫu gợi ý»
 * để điền sẵn chi phí cho kế hoạch mới.
 */
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
}
