import { apiGet } from '@/core/api'
import type { OrgChartPayload } from '../types/org-chart'

/** Sơ đồ tổ chức — backend lọc theo phạm vi `employee` / `department` của người xem. */
export const orgChartApi = {
  get: () => apiGet<OrgChartPayload>('/api/org-chart'),
}
