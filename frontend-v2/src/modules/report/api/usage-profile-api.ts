import { apiGet, downloadFile } from '@/core/api'

import type { UsageProfileDetail, UsageProfileListResponse } from '../types/usage-profile'

/** Tham số lọc danh sách; `label` là mảng (axios lặp khóa `label=1&label=2`). */
export type UsageListParams = Record<string, string | number | string[]>

const BASE = '/api/usage-profiles'

/** Ba lời gọi của «Hồ sơ cách làm việc» (duoc-CR-641): danh sách · xuất Excel · hồ sơ một người. */
export const usageProfileApi = {
  list: (params: UsageListParams) =>
    apiGet<UsageProfileListResponse>(`${BASE}/summary`, { params }),
  export: (params: UsageListParams, filename: string) =>
    downloadFile(`${BASE}/summary/export`, filename, params),
  detail: (userId: number, weeks: number) =>
    apiGet<UsageProfileDetail>(`${BASE}/${userId}`, { params: { weeks } }),
}
