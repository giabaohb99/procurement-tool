import { Badge } from '@/shared/ui/badge'
import { cn } from '@/shared/utils/cn'

/**
 * Nhóm màu theo Ý NGHĨA của trạng thái, không theo từng mã: mỗi loại chứng từ
 * có một bộ mã riêng nhưng chỉ có bốn tình huống người đọc cần phân biệt —
 * đang nháp, đang chờ, đã xong, bị chặn.
 */
const TONE_CLASS = {
  neutral: 'bg-muted text-muted-foreground',
  pending: 'bg-warning/10 text-warning',
  progress: 'bg-info/10 text-info',
  done: 'bg-success/10 text-success',
  danger: 'bg-destructive/10 text-destructive',
} as const

type Tone = keyof typeof TONE_CLASS

/** Mã trạng thái -> tông màu. Mã của cả 4 loại chứng từ gom chung được vì không đụng nhau. */
const STATUS_TONE: Record<string, Tone> = {
  draft: 'neutral',
  submitted: 'pending',
  approved: 'progress',
  dispatched: 'progress',
  processing: 'progress',
  partial: 'progress',
  survey_done: 'progress',
  pr_created: 'progress',
  received: 'done',
  completed: 'done',
  done: 'done',
  rejected: 'danger',
  cancelled: 'danger',
}

interface StatusBadgeProps {
  /** Mã trạng thái lấy từ API (`draft`, `submitted`…). */
  status: string
  /** Bảng nhãn của loại chứng từ tương ứng (`PR_STATUS_LABELS`…). */
  labels: Record<string, string>
  className?: string
}

/** Huy hiệu trạng thái chứng từ. Mã lạ thì hiện nguyên mã, tông trung tính. */
export function StatusBadge({ status, labels, className }: StatusBadgeProps) {
  if (!status) return <span className="text-muted-foreground">—</span>

  return (
    <Badge
      variant="secondary"
      className={cn('border-0', TONE_CLASS[STATUS_TONE[status] ?? 'neutral'], className)}
    >
      {labels[status] ?? status}
    </Badge>
  )
}

/** Tình trạng hồ sơ chứng từ của ĐMH — lưu chuỗi tiếng Việt nên map riêng. */
const DOCUMENT_TONE: Record<string, Tone> = {
  'chưa có chứng từ': 'danger',
  'đã có thông tin chứng từ': 'pending',
  'đã đủ chứng từ': 'done',
}

export function DocumentStatusBadge({ status }: { status: string }) {
  if (!status) return <span className="text-muted-foreground">—</span>

  return (
    <Badge
      variant="secondary"
      // `first-letter:uppercase` chứ không phải `capitalize`: giá trị lưu là câu
      // tiếng Việt ("đã có thông tin chứng từ"), viết hoa mọi chữ đọc rất kỳ.
      className={cn(
        'border-0 first-letter:uppercase',
        TONE_CLASS[DOCUMENT_TONE[status] ?? 'neutral'],
      )}
    >
      {status}
    </Badge>
  )
}

/** Tiến độ dòng đơn hàng ở màn "Tiến độ mua hàng". */
const PROGRESS_TONE: Record<string, Tone> = {
  'Chưa đặt hàng': 'neutral',
  'Đã đặt hàng': 'progress',
  'Đã nhận hàng': 'progress',
  'Chưa gửi ĐMH cho KT': 'pending',
  'Đã gửi ĐMH cho KT': 'progress',
  'Hoàn thành': 'done',
  'Tạm ngưng': 'pending',
  'Hủy đơn': 'danger',
}

export function ProgressStatusBadge({ status }: { status: string }) {
  if (!status) return <span className="text-muted-foreground">—</span>

  return (
    <Badge
      variant="secondary"
      className={cn('border-0', TONE_CLASS[PROGRESS_TONE[status] ?? 'neutral'])}
    >
      {status}
    </Badge>
  )
}

/** Kết quả duyệt của một dòng khảo sát. */
const LINE_APPROVE_TONE: Record<string, Tone> = {
  'Chờ duyệt': 'pending',
  'Đã duyệt': 'done',
  'Không duyệt': 'danger',
  'Thiếu thông tin': 'pending',
}

export function LineApproveBadge({ status }: { status: string }) {
  if (!status) return <span className="text-muted-foreground">—</span>

  return (
    <Badge
      variant="secondary"
      className={cn('border-0', TONE_CLASS[LINE_APPROVE_TONE[status] ?? 'neutral'])}
    >
      {status}
    </Badge>
  )
}
