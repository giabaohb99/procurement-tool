export type BackupStatus = 'running' | 'success' | 'failed'

export type BackupSource = 'auto' | 'manual' | string

/** ai-CR-139: màn Sao lưu xem được hai DB — DB ERP và DB của bot (`agent_hub`, chỉ có khi bot chạy tách DB). */
export type BackupTarget = 'erp' | 'agent'

export interface DbBackupItem {
  id: number
  /** Chỉ DB bot có: `restore_test` = lượt khôi phục thử hằng tuần (nạp vào DB tạm rồi xóa). */
  kind?: 'backup' | 'restore_test'
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
  /** Chỉ DB bot: false = bot chạy chung DB ERP, bản sao lưu ERP đã gồm bảng bot. */
  enabled?: boolean
  db_name?: string
  stale_hours?: number
}
