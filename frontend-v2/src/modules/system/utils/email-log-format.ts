import type { TONE_CLASS } from '@/shared/ui/status-tone'

import { EMAIL_LOG_STATUS } from '../api/email-log-api'

/** Màu huy hiệu theo trạng thái thư (bao-CR-721). Trạng thái lạ về xám. */
export function emailStatusTone(status: string): keyof typeof TONE_CLASS {
  switch (status) {
    case EMAIL_LOG_STATUS.SENT:
      return 'done'
    case EMAIL_LOG_STATUS.FAILED:
      return 'danger'
    case EMAIL_LOG_STATUS.PENDING:
      return 'pending'
    default:
      return 'neutral'
  }
}

/** Câu lỗi rút cho ô bảng: một dòng, tối đa `max` ký tự. */
export function shortError(error: string, max = 120): string {
  const oneLine = (error || '').replace(/\s+/g, ' ').trim()
  return oneLine.length > max ? `${oneLine.slice(0, max - 1)}…` : oneLine
}
