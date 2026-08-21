import { apiDelete, apiGet, apiPost } from '@/core/api'
import type { ListParams } from '@/shared/types/api'
import type { DbBackupListResponse } from '../types/backup'

const BASE_URL = '/api/backups'

export interface DownloadBackupResponse {
  url: string
  filename: string
}

export const backupApi = {
  list: (params?: ListParams) =>
    apiGet<DbBackupListResponse>(BASE_URL, { params }),

  runNow: () =>
    apiPost<null>(`${BASE_URL}/run`),

  download: (id: number) =>
    apiGet<DownloadBackupResponse>(`${BASE_URL}/${id}/download`),

  deleteBackup: (id: number) =>
    apiDelete<null>(`${BASE_URL}/${id}`),
}
