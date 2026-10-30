import type { TONE_CLASS } from '@/shared/ui/status-tone'

import { JOB_RUN_STATUS } from '../api/job-run-api'

type Tone = keyof typeof TONE_CLASS

/**
 * Thời lượng một lần chạy, viết cho người đọc: "350 ms", "4,2 giây", "3 phút 05 giây", "1 giờ 12 phút".
 *
 * `null` / âm / không phải số → gạch ngang: lần chạy chưa xong hoặc tiến trình chết giữa chừng thì KHÔNG có thời lượng,
 * in "0 ms" là nói dối rằng nó chạy tức thì.
 */
export function formatDuration(ms: number | null | undefined): string {
  if (ms == null || !Number.isFinite(ms) || ms < 0) return '—'
  if (ms < 1000) return `${Math.round(ms)} ms`
  const totalSeconds = ms / 1000
  if (totalSeconds < 60) return `${totalSeconds.toFixed(1).replace('.', ',')} giây`
  const seconds = Math.floor(totalSeconds) % 60
  const totalMinutes = Math.floor(totalSeconds / 60)
  if (totalMinutes < 60) return `${totalMinutes} phút ${String(seconds).padStart(2, '0')} giây`
  const hours = Math.floor(totalMinutes / 60)
  return `${hours} giờ ${String(totalMinutes % 60).padStart(2, '0')} phút`
}

/**
 * Màu cho trạng thái một lần chạy.
 *
 * *Bỏ qua* cố ý XÁM chứ không xanh (cùng lý do sổ đồng bộ): tô xanh thì một việc lần nào cũng bỏ qua nhìn y hệt một việc
 * chạy tốt — trong khi câu hỏi của màn này chính là "việc có thật sự làm gì không".
 */
export function jobRunTone(status: number | null | undefined): Tone {
  switch (status) {
    case JOB_RUN_STATUS.SUCCESS:
      return 'done'
    case JOB_RUN_STATUS.FAILED:
      return 'danger'
    case JOB_RUN_STATUS.RUNNING:
      return 'active'
    default:
      return 'neutral'
  }
}

/**
 * Tỷ lệ lỗi 7 ngày, gọn một ô: "12 lần" / "12 lần · 2 lỗi". Không chạy lần nào trong 7 ngày → "Chưa chạy" — một việc
 * hằng ngày mà 7 ngày không có lần nào là dấu hiệu beat đã chết, phải đọc ra được chứ không phải "0 lần" lặng lẽ.
 */
export function runsText(runs: number | null | undefined, failed: number | null | undefined): string {
  const total = Math.max(0, Number(runs) || 0)
  if (total === 0) return 'Chưa chạy'
  const bad = Math.min(total, Math.max(0, Number(failed) || 0))
  return bad > 0 ? `${total} lần · ${bad} lỗi` : `${total} lần`
}
