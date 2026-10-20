import { apiGet } from '@/core/api'

import type { CapabilitySummary, WorkLoadResult } from '../types/work-capability'

export type WorkCapabilityParams = Record<string, string | number | string[]>

const BASE = '/api/work-capability'

/** Hai lời gọi của «Năng lực theo loại việc» (duoc-CR-657); xuất Excel đi qua `ReportExportButton`. */
export const workCapabilityApi = {
  summary: (params: WorkCapabilityParams) => apiGet<CapabilitySummary>(`${BASE}/summary`, { params }),
  load: (params: WorkCapabilityParams) => apiGet<WorkLoadResult>(`${BASE}/load`, { params }),
}
