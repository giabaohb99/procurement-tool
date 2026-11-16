import { TriangleAlert } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import type { MissingContractSummary } from '../utils/leave-accrual-status'

interface LeaveBalanceMissingContractStripProps {
  summary: MissingContractSummary
  /** Chữ nối sau số người, vd *trên trang đang xem* cho bảng phân trang ở máy chủ. Bỏ trống = cả danh sách. */
  scopeNote?: string
  /**
   * Nút *Chỉ hiện người chưa đủ HĐLĐ* — CHỈ truyền khi bảng đã nạp trọn danh sách và lọc được ở trình duyệt. Bảng phân
   * trang ở máy chủ thì bỏ trống: lọc một trang là nói sai về cả danh sách.
   */
  filter?: { active: boolean; onToggle: () => void }
}

/**
 * Dải đếm người *chưa đủ HĐLĐ* (mã 3 Chưa có HĐLĐ + mã 4 Lịch sử HĐLĐ chưa đủ) ở đầu bảng Quỹ phép (duoc-CR-762,
 * phương án B). Luôn hiện khi có người thiếu.
 *
 *  · Thiếu ≤ một nửa: nhãn hổ phách đã nằm trên từng dòng, dải chỉ đếm và nhắc đi nhập hợp đồng.
 *  · Thiếu quá nửa: nhãn trên dòng bị ẩn (phủ kín bảng thì mất nghĩa) — dải nói *N/M người*, kèm nút lọc nếu có.
 */
export function LeaveBalanceMissingContractStrip({ summary, scopeNote, filter }: LeaveBalanceMissingContractStripProps) {
  if (summary.missing === 0) return null
  const scope = scopeNote ? ` ${scopeNote}` : ''
  const count = summary.showRowBadges ? `${summary.missing} nhân sự` : `${summary.missing}/${summary.total} người`
  return (
    <div className="mb-2 flex flex-wrap items-center gap-x-3 gap-y-1 rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm text-foreground">
      <span className="flex min-w-0 flex-1 items-center gap-2">
        <TriangleAlert className="size-4 shrink-0 text-amber-600 dark:text-amber-400" />
        <span>
          {count}
          {scope} chưa đủ HĐLĐ trên hệ thống — phép năm đang tính từ ngày vào làm.
          {summary.showRowBadges && ' Nhập hợp đồng lao động để tính đúng.'}
        </span>
      </span>
      {!summary.showRowBadges && filter && (
        <Button
          type="button"
          variant="outline"
          size="sm"
          aria-pressed={filter.active}
          onClick={filter.onToggle}
          className="max-md:w-full"
        >
          {filter.active ? 'Hiện tất cả' : 'Chỉ hiện người chưa đủ HĐLĐ'}
        </Button>
      )}
    </div>
  )
}
