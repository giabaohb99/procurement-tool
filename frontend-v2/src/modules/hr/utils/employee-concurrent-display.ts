import { CONCURRENT_KIND, CONCURRENT_STATUS, labelOf } from '@/shared/constants/statuses'
import type { StatusTone } from '@/shared/ui/status-tone'
import { formatDate } from '@/shared/utils/format-date'
import {
  CONCURRENT_ACTIVE,
  CONCURRENT_ENDED,
  CONCURRENT_KIND_COMPANY,
  CONCURRENT_KIND_DEPARTMENT,
  CONCURRENT_UPCOMING,
  type EmployeeConcurrent,
} from '../types/employee-concurrent'

/** Nhãn trạng thái: ưu tiên nhãn backend gửi kèm, rỗng thì tra bộ mã sinh sẵn. */
export function concurrentStatusLabel(row: Pick<EmployeeConcurrent, 'status' | 'status_label'>): string {
  return row.status_label || labelOf(CONCURRENT_STATUS, String(row.status))
}

/** Nhãn loại (Phòng ban / Công ty): ưu tiên nhãn backend gửi kèm, rỗng thì tra bộ mã sinh sẵn `CONCURRENT_KIND`. */
export function concurrentKindLabel(row: Pick<EmployeeConcurrent, 'kind' | 'kind_label'>): string {
  return row.kind_label || labelOf(CONCURRENT_KIND, String(row.kind))
}

/**
 * NƠI kiêm nhiệm của một dòng — tên PHÒNG với loại Phòng ban (công ty luôn là công ty hiện tại nên không nhắc), tên
 * CÔNG TY với loại Công ty (không có phòng). Thiếu tên (danh mục đã xóa) thì in mã số, không để ô trống.
 */
export function concurrentPlaceLabel(
  row: Pick<EmployeeConcurrent, 'kind' | 'company_id' | 'company_name' | 'department_id' | 'department_name'>,
): string {
  if (row.kind === CONCURRENT_KIND_COMPANY) return row.company_name || `Công ty #${row.company_id}`
  return row.department_name || `Phòng #${row.department_id}`
}

/** Tông huy hiệu: Đang hiệu lực xanh lá, Sắp tới xanh dương, Đã hết xám. */
export function concurrentStatusTone(status: number): StatusTone {
  if (status === CONCURRENT_ACTIVE) return 'done'
  if (status === CONCURRENT_UPCOMING) return 'progress'
  return 'neutral'
}

/**
 * Thứ tự HIỂN THỊ mặc định (kế hoạch phase 04): Đang hiệu lực → Sắp tới → Đã hết, cùng nhóm thì từ ngày giảm dần.
 * Khác thứ tự khai của bộ mã (Sắp tới là số 1) — người mở tab cần thấy dòng đang có tác dụng trước.
 */
const DEFAULT_RANK: Record<number, number> = {
  [CONCURRENT_ACTIVE]: 0,
  [CONCURRENT_UPCOMING]: 1,
  [CONCURRENT_ENDED]: 2,
}

export function sortConcurrentRowsDefault(rows: readonly EmployeeConcurrent[]): EmployeeConcurrent[] {
  return [...rows].sort((a, b) => {
    const rank = (DEFAULT_RANK[a.status] ?? 9) - (DEFAULT_RANK[b.status] ?? 9)
    if (rank !== 0) return rank
    const af = a.from_date ?? ''
    const bf = b.from_date ?? ''
    if (af !== bf) return af < bf ? 1 : -1
    return b.id - a.id
  })
}

/** `"01/11/2026 – 30/11/2026"`, `"Từ 01/11/2026"`, `"Đến 30/11/2026"`; hai đầu trống = chuỗi rỗng. */
export function concurrentPeriodLabel(row: Pick<EmployeeConcurrent, 'from_date' | 'to_date'>): string {
  const from = formatDate(row.from_date)
  const to = formatDate(row.to_date)
  if (from && to) return `${from} – ${to}`
  if (from) return `Từ ${from}`
  if (to) return `Đến ${to}`
  return ''
}

/**
 * Dòng kiêm nhiệm sẽ bị KẾT THÚC (hoặc xóa nếu chưa bắt đầu) khi đổi pháp nhân chính `oldCompanyId` → `newCompanyId`
 * (luật backend `end_rows_at_company`, duoc-CR-756), chỉ dòng CHƯA hết hạn:
 * - loại Phòng ban ở công ty CŨ — phòng đó không còn là phòng của công ty hiện tại;
 * - loại Công ty trùng công ty MỚI — kiêm nhiệm chính công ty mình là thừa.
 * Dòng loại Công ty ở công ty khác (kể cả công ty cũ) không đụng.
 */
export function concurrentRowsEndingOnCompanyChange(
  rows: readonly EmployeeConcurrent[],
  oldCompanyId: number,
  newCompanyId: number,
): EmployeeConcurrent[] {
  if (oldCompanyId <= 0 || newCompanyId <= 0 || oldCompanyId === newCompanyId) return []
  return rows.filter(
    (r) =>
      r.status !== CONCURRENT_ENDED &&
      ((r.kind === CONCURRENT_KIND_DEPARTMENT && r.company_id === oldCompanyId) ||
        (r.kind === CONCURRENT_KIND_COMPANY && r.company_id === newCompanyId)),
  )
}

/**
 * Đã có dòng loại Công ty ở `companyId` còn hiệu lực hoặc sắp tới — khi đó backend BỎ QUA yêu cầu giữ kiêm nhiệm ở
 * công ty cũ (không tạo dòng trùng), nên hộp đổi pháp nhân nói rõ thay vì hỏi.
 */
export function hasOpenCompanyConcurrent(rows: readonly EmployeeConcurrent[], companyId: number): boolean {
  return rows.some(
    (r) => r.kind === CONCURRENT_KIND_COMPANY && r.company_id === companyId && r.status !== CONCURRENT_ENDED,
  )
}

/**
 * Dòng CHƯA BẮT ĐẦU theo nghĩa của backend khi đổi pháp nhân: `from_date >= hôm nay` (kể cả bắt đầu ĐÚNG hôm nay — dòng
 * đó hiện "Đang hiệu lực" nhưng vẫn bị xóa, không kết thúc được vào hôm qua). Bị xóa kèm tệp nếu không giữ lại.
 */
export function isConcurrentUnstarted(row: Pick<EmployeeConcurrent, 'from_date'>, today: string): boolean {
  return row.from_date !== null && row.from_date >= today
}
