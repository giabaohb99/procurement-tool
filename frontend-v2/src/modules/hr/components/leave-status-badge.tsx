import { Badge } from '@/shared/ui/badge'
import { LEAVE_STATUS, LEAVE_STATUS_LABELS } from '../types/leave'

interface LeaveStatusBadgeProps {
  status: number
  /** Nhãn backend trả kèm — ưu tiên dùng, xem ghi chú dưới. */
  label?: string
}

/**
 * Sắc thái của từng trạng thái. Ba nhóm, không phải sáu màu:
 *  · đang chờ người khác → hổ phách (chưa xong việc, còn phải theo dõi);
 *  · kết thúc TỐT       → xanh lá;
 *  · kết thúc XẤU       → đỏ.
 * *Trả về chỉnh sửa* nằm ở nhóm xấu chứ không nhóm chờ — nó đang chờ **CHÍNH
 * người nộp** làm gì đó, và đó là thông tin quan trọng hơn cả.
 *
 * Dùng nền ĐẶC chứ không viền mảnh: huy hiệu này là thứ người ta quét mắt tìm
 * đầu tiên trên cả trang danh sách, mà bản viền `outline` thì nhạt ngang chữ
 * thường bên cạnh. Giữ `border` cùng tông để nó không bị bệt vào nền tối.
 *
 * ⚠️ **CẤM token `primary` / `foreground` ở bảng này, và cấm luôn thang `slate`.**
 * Màu chủ đạo của bộ giao diện là navy, mà `slate` là thang xám ÁM XANH — huy
 * hiệu «Nháp»/«Đã hủy» tô `text-slate-700` đọc ra gần như đúng màu chữ thường
 * và màu nút chính, nên nó thôi không còn là huy hiệu trạng thái nữa mà nhìn
 * như một mẩu chữ in đậm. Hai trạng thái trung tính dùng thang `zinc` (xám
 * THẬT, không ám màu nào) để tách hẳn khỏi navy.
 *
 * «Nháp» và «Đã hủy» đều trung tính nên phân biệt bằng độ đậm của cùng thang
 * `zinc` — không mượn thêm một màu nào nữa, vì bốn màu còn lại đã mang nghĩa
 * riêng và thêm màu thứ năm là bắt người dùng học thuộc.
 *
 * ⚠️ Và **chỉ đổi MÀU** — không gạch ngang chữ, không đổi kiểu chữ. Huy hiệu
 * trạng thái phải cùng một hình dạng ở cả sáu ô thì mắt mới quét theo màu được;
 * một ô khác dạng đọc ra như lỗi hiển thị chứ không ra "đây là trạng thái khác".
 */
const TONES: Record<number, string> = {
  [LEAVE_STATUS.DRAFT]:
    'border-zinc-300 bg-zinc-100 text-zinc-600 dark:border-zinc-600 dark:bg-zinc-800 dark:text-zinc-300',
  [LEAVE_STATUS.PENDING]:
    'border-amber-300 bg-amber-100 text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200',
  [LEAVE_STATUS.APPROVED]:
    'border-emerald-300 bg-emerald-100 text-emerald-800 dark:border-emerald-700 dark:bg-emerald-950 dark:text-emerald-200',
  [LEAVE_STATUS.REJECTED]:
    'border-destructive/40 bg-destructive/15 text-destructive dark:bg-destructive/25',
  [LEAVE_STATUS.RETURNED]:
    'border-orange-300 bg-orange-100 text-orange-800 dark:border-orange-700 dark:bg-orange-950 dark:text-orange-200',
  [LEAVE_STATUS.CANCELLED]:
    'border-zinc-400 bg-zinc-200 text-zinc-700 dark:border-zinc-500 dark:bg-zinc-700 dark:text-zinc-200',
}

export function LeaveStatusBadge({ status, label }: LeaveStatusBadgeProps) {
  //  Ưu tiên nhãn của backend: nó là NGUỒN, còn bảng ở `types/leave.ts` là bản
  //  chép để màn hình không phải chờ một lượt gọi. Thêm trạng thái mới ở backend
  //  mà quên chép sang đây thì vẫn hiện đúng chữ, chỉ mất màu.
  const text = label || LEAVE_STATUS_LABELS[status] || '—'
  return (
    <Badge
      variant="outline"
      className={TONES[status] ?? TONES[LEAVE_STATUS.DRAFT]}
    >
      {text}
    </Badge>
  )
}
