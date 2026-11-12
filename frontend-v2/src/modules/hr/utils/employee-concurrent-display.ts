import { CONCURRENT_STATUS, labelOf } from '@/shared/constants/statuses'
import type { StatusTone } from '@/shared/ui/status-tone'
import { formatDate } from '@/shared/utils/format-date'
import {
  CONCURRENT_ACTIVE,
  CONCURRENT_ENDED,
  CONCURRENT_UPCOMING,
  type EmployeeConcurrent,
} from '../types/employee-concurrent'

/** Nhãn trạng thái: ưu tiên nhãn backend gửi kèm, rỗng thì tra bộ mã sinh sẵn. */
export function concurrentStatusLabel(row: Pick<EmployeeConcurrent, 'status' | 'status_label'>): string {
  return row.status_label || labelOf(CONCURRENT_STATUS, String(row.status))
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
 * Dòng kiêm nhiệm sẽ bị ĐỘNG TỚI khi đổi pháp nhân chính khỏi `oldCompanyId` (luật backend
 * `concurrent_transition_service.end_rows_at_company`): đúng công ty cũ và CHƯA hết hạn. Dòng ở công ty khác không đụng.
 */
export function concurrentRowsAtOldCompany(
  rows: readonly EmployeeConcurrent[],
  oldCompanyId: number,
): EmployeeConcurrent[] {
  if (oldCompanyId <= 0) return []
  return rows.filter((r) => r.company_id === oldCompanyId && r.status !== CONCURRENT_ENDED)
}

/**
 * Dòng CHƯA BẮT ĐẦU theo nghĩa của backend khi đổi pháp nhân: `from_date >= hôm nay` (kể cả bắt đầu ĐÚNG hôm nay — dòng
 * đó hiện "Đang hiệu lực" nhưng vẫn bị xóa, không kết thúc được vào hôm qua). Bị xóa kèm tệp nếu không giữ lại.
 */
export function isConcurrentUnstarted(row: Pick<EmployeeConcurrent, 'from_date'>, today: string): boolean {
  return row.from_date !== null && row.from_date >= today
}
