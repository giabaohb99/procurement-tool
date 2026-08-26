import { apiGet, downloadFile } from '@/core/api'
import type { ListParams } from '@/shared/types/api'

import type { ExportFormat } from '../config/export-meta'
import type { ExportEntityOption, ExportListResponse, ExportLog } from '../types/export-log'

const BASE_URL = '/api/exports'

export interface ExportListParams extends ListParams {
  entity?: string
  fmt?: string
  date_from?: string
  date_to?: string
  created_by_name?: string
}

export const exportApi = {
  /** Nhật ký các lần xuất. */
  list: (params?: ExportListParams) => apiGet<ExportListResponse>(BASE_URL, { params }),

  /** Các bảng người dùng được phép xuất — cho ô chọn của hộp thoại. */
  entities: () => apiGet<ExportEntityOption[]>(`${BASE_URL}/entities`),

  /** Chạy xuất một bảng ra CSV/XLSX + tải file về (backend tự ghi log). */
  run: (entity: string, format: ExportFormat, filename: string) =>
    downloadFile(`${BASE_URL}/run?entity=${encodeURIComponent(entity)}&format=${format}`, filename),

  /** Chi tiết một lần xuất. */
  get: (id: number) => apiGet<ExportLog>(`${BASE_URL}/${id}`),

  /** Tải lại đúng file đã xuất (đã lưu ở kho). */
  downloadFile: (id: number, filename: string) =>
    downloadFile(`${BASE_URL}/${id}/file`, filename),
}
