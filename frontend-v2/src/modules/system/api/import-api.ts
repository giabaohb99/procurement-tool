import { apiGet, apiPost, downloadFile } from '@/core/api'
import type { ListParams } from '@/shared/types/api'

import type {
  ImportBatch,
  ImportListResponse,
  ImportLogListResponse,
  ImportPurgePreview,
  ImportPurgeResult,
} from '../types/import-batch'

const BASE_URL = '/api/imports'

export interface ImportListParams extends ListParams {
  module?: number
  /** Lọc theo PHÂN HỆ (hr | procurement | production | inventory) — backend map ra tập module. */
  phan_he?: string
  status?: number
  mode?: number
  date_from?: string
  date_to?: string
  created_by_name?: string
  filename?: string
}

export interface ImportLogParams extends ListParams {
  level?: number
}

export interface UploadImportPayload {
  module: number
  mode: number
  file: File
}

export const importApi = {
  list: (params?: ImportListParams) =>
    apiGet<ImportListResponse>(BASE_URL, { params }),

  get: (id: number) => apiGet<ImportBatch>(`${BASE_URL}/${id}`),

  logs: (id: number, params?: ImportLogParams) =>
    apiGet<ImportLogListResponse>(`${BASE_URL}/${id}/logs`, { params }),

  upload: ({ module, mode, file }: UploadImportPayload) => {
    const form = new FormData()
    form.append('module', String(module))
    form.append('mode', String(mode))
    form.append('file', file)
    // Không tự đặt Content-Type — axios tự gắn boundary multipart cho FormData.
    return apiPost<ImportBatch>(BASE_URL, form)
  },

  revert: (id: number) => apiPost<ImportBatch>(`${BASE_URL}/${id}/revert`),

  /** Ghi thật từ một bản chạy thử — tạo batch APPLY mới dùng lại đúng file đã tải. */
  commit: (id: number) => apiPost<ImportBatch>(`${BASE_URL}/${id}/commit`),

  /** Xem trước xóa dữ liệu theo lô (định mức / báo giá / sổ Misa): số dòng sẽ xóa + số dòng đã sửa tay. */
  purgePreview: (id: number) => apiGet<ImportPurgePreview>(`${BASE_URL}/${id}/purge-preview`),

  /** Xóa dữ liệu của lô; `includeEdited` = xóa luôn dòng đã sửa tay sau khi nhập. */
  purge: (id: number, includeEdited: boolean) =>
    apiPost<ImportPurgeResult>(`${BASE_URL}/${id}/purge`, { include_edited: includeEdited }),

  /** Tải lại file .xlsx gốc đã upload (qua đường có kiểm quyền + gắn token). */
  downloadFile: (id: number, filename: string) =>
    downloadFile(`${BASE_URL}/${id}/file`, filename),

  /** Tải file .xlsx mẫu (đúng bộ cột) cho một đối tượng danh mục. */
  downloadTemplate: (module: number, filename: string) =>
    downloadFile(`${BASE_URL}/template?module=${module}`, filename),
}
