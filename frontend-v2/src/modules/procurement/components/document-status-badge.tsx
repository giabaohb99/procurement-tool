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
  // Điều phối là mốc "đã chốt xong khâu duyệt" — bản v1 tô XANH LÁ, giữ nguyên
  // để người dùng cũ không phải học lại bảng màu.
  dispatched: 'done',
  // "Đang xử lý" là đang chờ người khác làm tiếp → cùng tông chờ với v1, không
  // phải tông "đã xong một bước".
  processing: 'pending',
  partial: 'progress',
  survey_done: 'progress',
  pr_created: 'progress',
  received: 'done',
  completed: 'done',
  done: 'done',
  // `rejected` = TRẢ VỀ (sửa rồi gửi duyệt lại được) nên là cảnh báo, không phải
  // lỗi; chỉ `cancelled` (từ chối, khóa phiếu) mới tô đỏ. Giống bảng màu v1.
  rejected: 'pending',
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

/**
 * Tiến độ dòng đơn hàng — chỗ DUY NHẤT không gom theo tông.
 *
 * Tám giá trị này là một dây chuyền tuần tự (chưa đặt → đặt → nhận → gửi KT →
 * xong), người dùng quét bảng vài trăm dòng để tìm dòng kẹt ở khâu nào, nên mỗi
 * khâu phải một màu riêng. Bảng màu bê nguyên từ v1 (`PG_COLOR`) để người dùng
 * cũ không phải học lại. Bốn màu ngoài bộ token dùng thẳng bảng màu Tailwind vì
 * chúng không mang nghĩa "thành công / cảnh báo / lỗi" nào cả.
 */
const PROGRESS_CLASS: Record<string, string> = {
  'Chưa đặt hàng': TONE_CLASS.neutral,
  'Đã đặt hàng': 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
  'Đã nhận hàng': 'bg-cyan-500/10 text-cyan-700 dark:text-cyan-400',
  'Chưa gửi ĐMH cho KT': 'bg-pink-500/10 text-pink-600 dark:text-pink-400',
  'Đã gửi ĐMH cho KT': 'bg-violet-500/10 text-violet-600 dark:text-violet-400',
  'Hoàn thành': TONE_CLASS.done,
  'Tạm ngưng': TONE_CLASS.pending,
  'Hủy đơn': TONE_CLASS.danger,
}

export function ProgressStatusBadge({ status }: { status: string }) {
  if (!status) return <span className="text-muted-foreground">—</span>

  return (
    <Badge
      variant="secondary"
      className={cn('border-0', PROGRESS_CLASS[status] ?? TONE_CLASS.neutral)}
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
