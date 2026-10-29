import { apiGet } from '@/core/api'

import type { ReportDrilldownResponse } from '../types/report-drilldown'

/** Danh sách người sau một con số báo cáo — cùng bộ tham số `/summary` + `metric`/`group_by`/`group_key`. */
export const reportDrilldownApi = {
  get: (endpoint: string, params: Record<string, string>) =>
    apiGet<ReportDrilldownResponse>(endpoint, { params }),
}
