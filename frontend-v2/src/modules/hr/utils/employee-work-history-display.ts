import { formatDate } from '@/shared/utils/format-date'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { CONCURRENT_TYPE, POSITION_TRACK, RESIGN_TYPE } from './employee-work-history-apply'

/**
 * Hàm thuần dựng cho hai cách HIỂN THỊ «Quá trình công tác & Quyết định» (đại
 * ca chốt 03/10/2026): lọc khu «Quyết định bổ nhiệm», sắp dòng thời gian mới
 * nhất trước, và gom các mẩu chữ lặp lại ở nhiều nơi (nhãn tóm tắt, màu badge).
 *
 * Tách khỏi `employee-work-history-apply.ts` vì hai tệp đổi vì lý do khác hẳn
 * nhau: tệp đó quyết định có nên HỎI/ÁP hồ sơ hay không, tệp này chỉ quyết
 * định HIỂN THỊ cái gì — không hàm nào ở đây gọi API hay mở hộp thoại.
 */

/** Hai khu dùng CHUNG một component dòng thời gian, chỉ khác NGÀY chính hiện ở đầu mốc. */
export type WorkHistoryTimelineVariant = 'history' | 'decision'

/**
 * Khu «Quyết định bổ nhiệm» — CHỈ các dòng có `decision_no`, lọc từ CÙNG nguồn
 * `items` đã nạp (không gọi API thêm). Chuỗi toàn khoảng trắng coi như rỗng.
 */
export function filterDecisionRows(items: EmployeeWorkHistory[]): EmployeeWorkHistory[] {
  return items.filter((row) => row.decision_no.trim() !== '')
}

/**
 * Mới nhất lên trên: `from_date desc, id desc`.
 *
 * Viết lại tường minh thay vì tin thứ tự API trả (`work_history_service.py`
 * đã sắp đúng vậy) — component hiển thị không nên phụ thuộc NGẦM vào một quy
 * ước của backend mà nó không kiểm tra lại được. Không sửa mảng gốc (trả bản
 * sao) vì `items` còn dùng cho bảng và khu kia.
 */
export function sortWorkHistoryNewestFirst(items: EmployeeWorkHistory[]): EmployeeWorkHistory[] {
  return [...items].sort((a, b) => {
    if (a.from_date !== b.from_date) return a.from_date > b.from_date ? -1 : 1
    return b.id - a.id
  })
}

/**
 * Badge màu theo NHÓM loại — semantic token của `Badge` (`default` ·
 * `secondary` · `destructive` · `outline`), không hex. Thôi việc tô đỏ (việc
 * nặng nhất, khóa tài khoản); kiêm nhiệm tô viền (không đổi chức vụ chính);
 * nhóm chính (tuyển/điều chuyển/bổ nhiệm/miễn nhiệm) tô đặc; còn lại (Khác, hay
 * mã lạ không rơi vào nhóm nào) tô xám trung tính.
 */
export function workHistoryBadgeVariant(
  eventType: number,
): 'default' | 'secondary' | 'destructive' | 'outline' {
  if (eventType === RESIGN_TYPE) return 'destructive'
  if (eventType === CONCURRENT_TYPE) return 'outline'
  if (POSITION_TRACK.has(eventType)) return 'default'
  return 'secondary'
}

/** `"Phòng Kế toán · Trưởng phòng · Công ty ABC"` — bỏ phần rỗng, nối bằng " · ". */
export function workHistorySummaryLine(row: EmployeeWorkHistory): string {
  return [row.department_name, row.position_label, row.company_name]
    .filter((part) => part.trim() !== '')
    .join(' · ')
}

/**
 * Ngày chính hiện ở ĐẦU mốc — khác nhau theo khu (đại ca chốt): khu Quá trình
 * công tác đọc khoảng hiệu lực (`from_date → to_date`/`→ nay`), khu Quyết định
 * đọc ngày KÝ (`decision_date`, khác `from_date` — Q1).
 *
 * ⚠️ Không PHẢI mọi dòng có số QĐ đều có ngày ký (`decision_date` để trống —
 * ghi tay thiếu, hoặc nhập bù lịch sử cũ không còn giữ ngày ký). Review
 * 03/10/2026: bản cũ hiện cứng «—» cho cả dòng này, đọc như lỗi dữ liệu. Không
 * có ngày ký thì lấy `from_date` (ngày HIỆU LỰC của dòng) làm mốc thay — ghi
 * rõ tiền tố «Hiệu lực» để không ai đọc nhầm đó là ngày ký.
 */
export function workHistoryTimelineDateLabel(
  row: EmployeeWorkHistory,
  variant: WorkHistoryTimelineVariant,
): string {
  if (variant === 'decision') {
    if (row.decision_date) return formatDate(row.decision_date)
    return `Hiệu lực ${formatDate(row.from_date)}`
  }
  const from = formatDate(row.from_date)
  const to = row.to_date ? formatDate(row.to_date) : 'nay'
  return `${from} → ${to}`
}

/**
 * Chữ ở ô «Đến ngày» khi dòng CHƯA có ngày kết thúc. Trước 05/10/2026 ô này cứ
 * `to_date` rỗng là hiện «Đang hiệu lực» — nhập bù một dòng chính cũ hơn (vd
 * Bổ nhiệm 03/10 nhập sau Điều chuyển 04/10) thì hai dòng cùng «Đang hiệu
 * lực». Nay đọc chung cờ `is_current` của backend (đã xét dòng chính mới hơn
 * thay thế) với huy hiệu «Hiện tại» ở dòng thời gian:
 * - `is_current` → «Đang hiệu lực»;
 * - chưa tới ngày bắt đầu → «Chưa hiệu lực»;
 * - còn lại (đã bị dòng chính mới hơn thay) → `null`, nơi gọi hiện «—».
 */
export function workHistoryOpenEndLabel(
  row: Pick<EmployeeWorkHistory, 'from_date' | 'is_current'>,
  today: string,
): 'Đang hiệu lực' | 'Chưa hiệu lực' | null {
  if (row.is_current) return 'Đang hiệu lực'
  if (row.from_date > today) return 'Chưa hiệu lực'
  return null
}
