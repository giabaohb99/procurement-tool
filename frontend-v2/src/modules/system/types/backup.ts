export type BackupStatus = 'running' | 'success' | 'failed'

export type BackupSource = 'auto' | 'manual' | string

export interface DbBackupItem {
  id: number
  source: BackupSource
  status: BackupStatus
  file_key: string | null
  size_bytes: number
  message: string | null
  started_at: string | null
  finished_at: string | null
  created_at: string
  created_by: number | null
  created_by_name: string
}

export interface DbBackupListResponse {
  total: number
  items: DbBackupItem[]
  keep: number
}
