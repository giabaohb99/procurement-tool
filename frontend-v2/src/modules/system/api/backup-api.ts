import { apiDelete, apiGet, apiPost } from '@/core/api'
import type { ListParams } from '@/shared/types/api'
import type { BackupTarget, DbBackupListResponse } from '../types/backup'

/** ai-CR-139: DB bot đi qua proxy `/api/agent-hub/*` như các màn agent khác; gác cùng khóa `backup`. */
const BASE_URL: Record<BackupTarget, string> = {
  erp: '/api/backups',
  agent: '/api/agent-hub/backups',
}

export interface DownloadBackupResponse {
  url: string
  filename: string
}

export const backupApi = {
  list: (params?: ListParams, target: BackupTarget = 'erp') =>
    apiGet<DbBackupListResponse>(BASE_URL[target], { params }),

  runNow: (target: BackupTarget = 'erp') =>
    apiPost<null>(`${BASE_URL[target]}/run`),

  /** Chỉ DB bot — nạp thử bản mới nhất vào DB tạm rồi xóa. KHÔNG có đường khôi phục thật trên web. */
  restoreTest: () =>
    apiPost<null>(`${BASE_URL.agent}/restore-test`),

  download: (id: number, target: BackupTarget = 'erp') =>
    apiGet<DownloadBackupResponse>(`${BASE_URL[target]}/${id}/download`),

  /**
   * *Chấp nhận cỡ mới* (bao-CR-656): CSDL thu nhỏ hợp lệ — gỡ dấu đáng ngờ để lượt sau
   * dọn bản cũ như thường. Không có bản nào bị đánh dấu thì máy chủ trả 400.
   */
  acceptSize: (target: BackupTarget = 'erp') =>
    apiPost<{ accepted: number }>(`${BASE_URL[target]}/accept-size`),

  /** Chỉ DB ERP có đường xóa bản sao lưu. */
  deleteBackup: (id: number) =>
    apiDelete<null>(`${BASE_URL.erp}/${id}`),
}
