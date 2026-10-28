import type { AxiosRequestConfig } from 'axios'

import { apiDelete, apiGet, apiPost, apiPut, downloadFile, httpClient } from '@/core/api'

import type {
  HeadcountPlanComputed,
  HeadcountPlanCreatePayload,
  HeadcountPlanCreateResult,
  HeadcountPlanDetail,
  HeadcountPlanDocumentLink,
  HeadcountPlanDraftPayload,
  HeadcountPlanLinesImportResult,
  HeadcountPlanPayload,
  HeadcountPlanPositionStat,
} from '../types/headcount-plan'

/**
 * API KẾ HOẠCH NHÂN SỰ THEO KỲ (duoc-CR-690). Danh sách đi qua khung CRUD chung (`CrudListPage`
 * đọc `GET /api/headcount-plans`); trang chi tiết đi qua các hàm dưới đây.
 */
export const HEADCOUNT_PLAN_API_PATH = '/api/headcount-plans'

export const headcountPlanApi = {
  get: (id: number) => apiGet<HeadcountPlanDetail>(`${HEADCOUNT_PLAN_API_PATH}/${id}`),

  create: (payload: HeadcountPlanCreatePayload) =>
    apiPost<HeadcountPlanCreateResult>(HEADCOUNT_PLAN_API_PATH, payload),

  /** Thay header + khoản + dòng vị trí + văn bản liên kết. */
  update: (id: number, payload: HeadcountPlanPayload) =>
    apiPut<HeadcountPlanDetail>(`${HEADCOUNT_PLAN_API_PATH}/${id}`, payload),

  remove: (id: number) => apiDelete<null>(`${HEADCOUNT_PLAN_API_PATH}/${id}`),

  /**
   * Xem trước bảng tự tính — KHÔNG lưu. `_silent`: gọi theo nhịp gõ, lỗi kiểm hợp lệ (422) bày ngay
   * tại khối khoản chi phí; để `httpClient` bật toast thì mỗi lần dừng tay là một toast đỏ.
   */
  compute: (payload: HeadcountPlanDraftPayload) =>
    apiPost<HeadcountPlanComputed>(`${HEADCOUNT_PLAN_API_PATH}/compute`, payload, { _silent: true } as AxiosRequestConfig),

  positionStats: (companyId: number, departmentId: number) =>
    apiGet<HeadcountPlanPositionStat[]>(`${HEADCOUNT_PLAN_API_PATH}/position-stats`, {
      params: { company_id: companyId, department_id: departmentId },
    }),

  /** Xuất MỘT kế hoạch ra Excel (dòng vị trí + bảng tính). */
  exportXlsx: (id: number, filename: string) =>
    downloadFile(`${HEADCOUNT_PLAN_API_PATH}/${id}/export`, filename),

  /**
   * Nhập CSV dòng vị trí vào MỘT kế hoạch (`position_code, hc_1..hc_n, <mã khoản>…`). `httpClient`
   * thẳng vì `multipart/form-data` — KHÔNG đặt tay `Content-Type`, trình duyệt tự sinh `boundary`.
   * `_silent`: lỗi là DANH SÁCH theo dòng, nút nhập tự bày hộp thoại thay cho toast một câu.
   */
  importLinesCsv: async (id: number, file: File): Promise<HeadcountPlanLinesImportResult> => {
    const body = new FormData()
    body.append('file', file)
    const res = await httpClient.post<{ data: HeadcountPlanLinesImportResult }>(
      `${HEADCOUNT_PLAN_API_PATH}/${id}/import/csv`,
      body,
      { _silent: true } as AxiosRequestConfig,
    )
    return res.data.data
  },

  /**
   * TẢI TỆP CĂN CỨ → backend tự tạo một văn bản KÍN ở phân hệ Văn bản có tệp đó, trả dòng để thêm vào
   * `documents` của bản nháp (không cần id kế hoạch). `httpClient` thẳng vì `multipart/form-data` — KHÔNG đặt tay
   * `Content-Type`. `_silent`: nút tải tự bày lỗi ngay dưới nút thay cho toast.
   */
  uploadBasisDocument: async (
    file: File,
    onProgress?: (percent: number) => void,
  ): Promise<HeadcountPlanDocumentLink> => {
    const body = new FormData()
    body.append('file', file)
    const res = await httpClient.post<{ data: HeadcountPlanDocumentLink }>(
      `${HEADCOUNT_PLAN_API_PATH}/documents/upload`,
      body,
      {
        _silent: true,
        onUploadProgress: (e) => onProgress?.(e.total ? Math.round((e.loaded / e.total) * 100) : 0),
      } as AxiosRequestConfig,
    )
    return res.data.data
  },
}

/** Xuất danh sách (header) theo ĐÚNG bộ lọc đang xem. */
export function exportHeadcountPlansCsv(params: Record<string, string>) {
  return downloadFile(`${HEADCOUNT_PLAN_API_PATH}/export/csv`, 'ke-hoach-nhan-su.csv', params)
}
