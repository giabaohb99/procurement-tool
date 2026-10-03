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
 */
export function workHistoryTimelineDateLabel(
  row: EmployeeWorkHistory,
  variant: WorkHistoryTimelineVariant,
): string {
  if (variant === 'decision') {
    return row.decision_date ? formatDate(row.decision_date) : '—'
  }
  const from = formatDate(row.from_date)
  const to = row.to_date ? formatDate(row.to_date) : 'nay'
  return `${from} → ${to}`
}
