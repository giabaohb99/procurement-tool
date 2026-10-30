import { apiGet } from '@/core/api'

import type { FeatureBreakdown, FeatureSummary } from '../types/feature-usage'

export type FeatureUsageParams = Record<string, string | number>

const BASE = '/api/feature-usage'

/** Hai lời gọi của "Mức dùng chức năng" (duoc-CR-655); xuất Excel đi qua `ReportExportButton`. */
export const featureUsageApi = {
  summary: (params: FeatureUsageParams) => apiGet<FeatureSummary>(`${BASE}/summary`, { params }),
  breakdown: (params: FeatureUsageParams) => apiGet<FeatureBreakdown>(`${BASE}/breakdown`, { params }),
}
