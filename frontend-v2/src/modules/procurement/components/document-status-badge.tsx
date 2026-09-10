import { Badge } from '@/shared/ui/badge'
import {
  PO_DOCUMENT_STATUS,
  PO_PROGRESS_STATUS,
  PR_LINE_STATUS,
  labelOf,
} from '@/shared/constants/statuses'
import { TONE_CLASS, type StatusTone as Tone } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'

/**
 * Mã trạng thái -> tông màu. Mã của cả 4 loại chứng từ gom chung được vì không đụng nhau.
 *
 * bao-CR-363 (10/09/2026) — MỖI MỐC MỘT MÀU, xếp theo đúng thứ tự vòng đời sao cho hai
 * mốc LIỀN KỀ không bao giờ cùng tông:
 *
 *   Nháp (xám) → Chờ duyệt (hổ phách) → Đã duyệt (xanh dương) → Đã điều phối (tím)
 *   → Đang xử lý (hồng sen) → Đang mua hàng / Đã nhận một phần (xanh mòng)
 *   → Đã mua hàng / Đã nhận đủ (xanh lá nhạt) → Hoàn thành (xanh lá ĐẶC)
 *
 * Bảng cũ chép nguyên bản v1, mà chính bản v1 mới là chỗ có lỗi: cả bộ pill của nó chỉ
 * có 5 lớp màu cho 11 mốc, nên `dispatched` · `purchased` · `received` · `completed` dồn
 * hết vào `done` và `submitted` · `rejected` · `processing` · `purchasing` dồn hết vào
 * `pending`. Khách chụp màn YCMH trên prod khoanh đỏ đúng ba dấu trùng màu (ticket 38).
 * Bản v1 đã vá cùng ngày, nên "giữ nguyên cho người dùng cũ khỏi học lại" nay không còn
 * lý do — hai bản dùng CÙNG một bảng màu mới.
 */
const STATUS_TONE: Record<string, Tone> = {
  draft: 'neutral',
  submitted: 'pending',
  approved: 'progress',
  // Điều phối là mốc "đã chốt duyệt, giao cho thu mua làm tiếp" — đúng nghĩa `handoff`.
  dispatched: 'handoff',
  // "Đang xử lý" = ĐÃ có người bắt tay làm (có ĐMH), khác hẳn `pending` là nằm chờ ai
  // đó nhận. Trước CR này nó cùng tông với Chờ duyệt và Bị trả lại.
  processing: 'active',
  // bao-CR-292/297 (ticket 22): hai mốc tách từ "Đang xử lý" theo độ phủ mã hàng trên
  // đơn MISA — mới phủ MỘT PHẦN thì `partial`, phủ ĐỦ thì `done`.
  purchasing: 'partial',
  purchased: 'done',
  partial: 'partial',
  survey_done: 'partial',
  pr_created: 'done',
  received: 'done',
  // Ba mã dưới là mốc CUỐI, phiếu đã đóng -> tô đặc, tách khỏi sắc xanh nhạt của
  // Đã mua hàng / Đã nhận đủ đứng ngay trước nó.
  completed: 'closed',
  done: 'closed',
  // `rejected` = TRẢ VỀ (sửa rồi gửi duyệt lại được) nên KHÔNG tô đỏ; nhưng cũng không
  // để chung tông với Chờ duyệt như trước — cam là tông riêng của nó.
  rejected: 'returned',
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
  if (!status) return null

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
  if (!status) return null

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
 *
 * ⚠️ bao-CR-363: bốn màu tự khai PHẢI tô đặc chữ trắng cho khớp `TONE_CLASS`. Năm mã
 * còn lại tra thẳng `TONE_CLASS` — bảng đó đã đổi sang tô đặc, để bốn màu này ở nền mờ
 * là một cột duy nhất có nửa ô đậm nửa ô nhạt, nhìn như lỗi hiển thị. Đổi `TONE_CLASS`
 * thì rà lại đây.
 */
const PROGRESS_CLASS: Record<string, string> = {
  no_po: TONE_CLASS.neutral,
  not_ordered: TONE_CLASS.neutral,
  ordered: 'bg-blue-700 text-white',
  received: 'bg-cyan-700 text-white',
  doc_pending: 'bg-pink-600 text-white',
  doc_sent: 'bg-violet-600 text-white',
  completed: TONE_CLASS.done,
  paused: TONE_CLASS.pending,
  cancelled: TONE_CLASS.danger,
}

export function ProgressStatusBadge({ status }: { status: string }) {
  if (!status) return null

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
  if (!state) return null

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
  if (!status) return null

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
  if (!result) return null

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
