import { Badge } from '@/shared/ui/badge'
import {
  PO_DOCUMENT_STATUS,
  PO_PROGRESS_STATUS,
  PR_LINE_STATUS,
  labelOf,
} from '@/shared/constants/statuses'
import { TONE_CLASS, type StatusTone as Tone } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'

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

/** Tình trạng hồ sơ chứng từ của ĐMH — khóa là MÃ (B-06), xem `PO_DOCUMENT_STATUS`. */
const DOCUMENT_TONE: Record<string, Tone> = {
  none: 'danger',
  partial: 'pending',
  full: 'done',
}

export function DocumentStatusBadge({ status }: { status: string }) {
  if (!status) return <span className="text-muted-foreground">—</span>

  return (
    <Badge variant="secondary" className={cn('border-0', TONE_CLASS[DOCUMENT_TONE[status] ?? 'neutral'])}>
      {labelOf(PO_DOCUMENT_STATUS, status) || status}
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
 *
 * B-06: khóa là MÃ. Huy hiệu này dùng cho CẢ tiến độ dòng ĐMH lẫn trạng thái dòng
 * YCMH — hai bộ mã dùng chung năm mã giữa chuỗi với cùng một nghĩa, YCMH chỉ thêm
 * `no_po` ở đầu, nên gộp một bảng là đúng chứ không phải trùng lặp.
 */
const PROGRESS_CLASS: Record<string, string> = {
  no_po: TONE_CLASS.neutral,
  not_ordered: TONE_CLASS.neutral,
  ordered: 'bg-blue-500/10 text-blue-600 dark:text-blue-400',
  received: 'bg-cyan-500/10 text-cyan-700 dark:text-cyan-400',
  doc_pending: 'bg-pink-500/10 text-pink-600 dark:text-pink-400',
  doc_sent: 'bg-violet-500/10 text-violet-600 dark:text-violet-400',
  completed: TONE_CLASS.done,
  paused: TONE_CLASS.pending,
  cancelled: TONE_CLASS.danger,
}

export function ProgressStatusBadge({ status }: { status: string }) {
  if (!status) return <span className="text-muted-foreground">—</span>

  // Nhãn của hai bộ trùng khít ở phần chung; `no_po` chỉ có ở YCMH nên tra bù bộ kia.
  const nhan = labelOf(PO_PROGRESS_STATUS, status) || labelOf(PR_LINE_STATUS, status) || status

  return (
    <Badge
      variant="secondary"
      className={cn(
        'border-0 whitespace-normal break-words text-center leading-tight py-1 px-2',
        PROGRESS_CLASS[status] ?? TONE_CLASS.neutral,
      )}
    >
      {nhan}
    </Badge>
  )
}

/**
 * Tiến độ MỘT DÒNG của phiếu Yêu cầu báo giá (CR-077).
 *
 * Nhãn lẫn màu đều do backend quyết (`progress_state` / `progress_tone` trong
 * `survey_request/line_state.py`) — FE chỉ dịch mã tông sang lớp CSS. Đừng tự
 * suy nhãn ở đây: trước CR-077 mỗi màn suy một kiểu nên cùng một dòng lại hiện
 * hai chữ khác nhau ở màn chi tiết và màn Tiến độ báo giá.
 */
const LINE_TONE_CLASS: Record<string, string> = {
  gray: TONE_CLASS.neutral,
  warn: TONE_CLASS.pending,
  info: TONE_CLASS.progress,
  ok: TONE_CLASS.done,
  err: TONE_CLASS.danger,
}

export function SurveyLineStateBadge({
  state,
  tone,
  className,
}: {
  state: string
  tone: string
  className?: string
}) {
  if (!state) return <span className="text-muted-foreground">—</span>

  return (
    <Badge
      variant="secondary"
      className={cn('border-0', LINE_TONE_CLASS[tone] ?? TONE_CLASS.neutral, className)}
    >
      {state}
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

/** Kết luận LAB của một dòng khảo sát sản phẩm (CR-109). */
const LAB_RESULT_TONE: Record<string, Tone> = {
  'Mẫu đạt': 'done',
  'Mẫu không đạt': 'danger',
}

export function LabResultBadge({ result }: { result: string }) {
  if (!result) return <span className="text-muted-foreground">—</span>

  return (
    <Badge
      variant="secondary"
      className={cn(
        'border-0 whitespace-normal break-words text-center leading-tight',
        TONE_CLASS[LAB_RESULT_TONE[result] ?? 'neutral'],
      )}
    >
      {result}
    </Badge>
  )
}
