import { formatDate } from '@/shared/utils/format-date'
import type { ConcurrentMember } from '../types/concurrent-member'

/** Mã `ConcurrentStatus` của backend: 2 = Đang hiệu lực (xem `hr_concurrent_codes.py`). */
const STATUS_ACTIVE = 2

/**
 * Khoảng hiệu lực của một dòng kiêm nhiệm: `01/09/2026 – 30/09/2026`, hoặc `Từ 01/09/2026` khi chưa có ngày kết
 * thúc. Dòng chép từ dữ liệu cũ có thể thiếu từ ngày (coi là đã hiệu lực từ trước) — khi đó chỉ nói ngày kết thúc.
 */
export function formatConcurrentPeriod(fromDate: string | null, toDate: string | null): string {
  const from = formatDate(fromDate)
  const to = formatDate(toDate)
  if (from && to) return `${from} – ${to}`
  if (from) return `Từ ${from}`
  if (to) return `Đến ${to}`
  return 'Chưa rõ ngày'
}

/** Nơi người đó thuộc CHÍNH THỨC: `Phòng Kế toán — Công ty A`. Thiếu vế nào bỏ vế đó, thiếu cả hai trả rỗng. */
export function formatPrimaryPlace(member: Pick<ConcurrentMember, 'primary_department_name' | 'primary_company_name'>): string {
  return [member.primary_department_name, member.primary_company_name].filter(Boolean).join(' — ')
}

/** Chỉ dòng KHÔNG ở trạng thái Đang hiệu lực mới cần nhãn trạng thái riêng (Sắp tới / Đã hết) cạnh tên. */
export function needsStatusBadge(member: Pick<ConcurrentMember, 'status'>): boolean {
  return member.status !== STATUS_ACTIVE
}
