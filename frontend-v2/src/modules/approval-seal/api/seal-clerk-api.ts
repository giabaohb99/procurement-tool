import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type { SealClerk, SealClerkBulkPayload, SealClerkGroup } from '../types/seal-clerk'

const BASE_URL = '/api/seal-clerks'

export interface SealClerkUpdatePayload {
  company_id?: number
  is_head?: boolean
}

/** Gộp phân công của một văn thư (cho màn chi tiết). */
export interface SealClerkForEmployee {
  employee_id: number
  company_ids: number[]
  is_head: boolean
  /** 1 = Đang hoạt động, 2 = Tạm dừng. */
  status: number
}

export interface SealClerkSyncPayload {
  employee_id: number
  company_ids: number[]
  is_head: boolean
  /** 1 = Đang hoạt động, 2 = Tạm dừng. Bỏ trống = GIỮ NGUYÊN trạng thái cũ. */
  status?: number
  anchor_id?: number
}

export const sealClerkApi = {
  /** Danh sách GỘP THEO VĂN THƯ (mỗi người một dòng). */
  list: (params: ListParams) => apiGet<PaginatedResult<SealClerkGroup>>(BASE_URL, { params }),
  get: (id: number) => apiGet<SealClerk>(`${BASE_URL}/${id}`),
  byEmployee: (employeeId: number) =>
    apiGet<SealClerkForEmployee>(`${BASE_URL}/by-employee/${employeeId}`),
  /** Gán một văn thư cho nhiều công ty (+ tùy chọn văn thư tổng) một lần. */
  bulk: (payload: SealClerkBulkPayload) =>
    apiPost<{ count: number }>(`${BASE_URL}/bulk`, payload),
  /** Đặt lại TOÀN BỘ công ty một văn thư phụ trách = đúng danh sách (thêm/bớt). */
  sync: (payload: SealClerkSyncPayload) =>
    apiPost<{ count: number }>(`${BASE_URL}/sync`, payload),
  update: (id: number, payload: SealClerkUpdatePayload) =>
    apiPatch<SealClerk>(`${BASE_URL}/${id}`, payload),
  remove: (id: number) => apiDelete<null>(`${BASE_URL}/${id}`),
}
