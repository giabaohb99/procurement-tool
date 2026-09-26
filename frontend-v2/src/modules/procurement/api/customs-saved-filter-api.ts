import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'

import type {
  CustomsBatchRowList,
  CustomsBatchRowSummary,
  CustomsSavedFilter,
  CustomsSavedFilterList,
} from '../types/customs-saved-filter'

/**
 * Đường API của bao-CR-496: bộ lọc đã lưu (riêng từng tài khoản) và nhật ký TỪNG DÒNG của
 * lô nạp. Tách khỏi `customs-api.ts` để không đụng tệp bao-CR-493 đang sửa.
 */
const BASE = '/api/customs'

export function fetchCustomsSavedFilters() {
  return apiGet<CustomsSavedFilterList>(`${BASE}/saved-filters`)
}

export function createCustomsSavedFilter(body: { name: string; params: string }) {
  return apiPost<CustomsSavedFilter>(`${BASE}/saved-filters`, body)
}

export function updateCustomsSavedFilter(id: number, body: { name?: string; params?: string }) {
  return apiPatch<CustomsSavedFilter>(`${BASE}/saved-filters/${id}`, body)
}

export function deleteCustomsSavedFilter(id: number) {
  return apiDelete<null>(`${BASE}/saved-filters/${id}`)
}

export function fetchCustomsBatchRowSummary(batchId: number) {
  return apiGet<CustomsBatchRowSummary>(`${BASE}/imports/${batchId}/rows/summary`)
}

export function fetchCustomsBatchRows(
  batchId: number,
  params: { page: number; page_size: number; row_status?: number },
) {
  return apiGet<CustomsBatchRowList>(`${BASE}/imports/${batchId}/rows`, { params })
}
