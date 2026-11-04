import { TriangleAlert } from 'lucide-react'

import type { LeaveBlockConflict } from '../types/leave'
import { describeBlockConflicts } from '../utils/leave-block-conflicts'

interface LeaveBlockWarningBannerProps {
  conflicts: readonly LeaveBlockConflict[] | undefined | null
}

/**
 * Khung VÀNG "ngày cấm nghỉ" (duoc-CR-715) — hiện trên form lập đơn ngay khi chọn ngày và trên trang chi tiết đơn.
 *
 * Chỉ CẢNH BÁO: đơn vẫn lưu và gửi duyệt được; lượt duyệt cuối mới bị chặn (trừ vai trò được miễn). Không có
 * xung đột thì không dựng gì — không chiếm chỗ.
 */
export function LeaveBlockWarningBanner({ conflicts }: LeaveBlockWarningBannerProps) {
  const lines = describeBlockConflicts(conflicts)
  if (lines.length === 0) return null
  return (
    <div
      role="alert"
      data-testid="leave-block-warning"
      className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900 md:col-span-2 dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-100"
    >
      <TriangleAlert className="mt-0.5 size-4 shrink-0" aria-hidden />
      <div className="min-w-0 space-y-1">
        <p className="font-medium">Đơn nghỉ này rơi vào ngày cấm nghỉ.</p>
        <ul className="list-disc space-y-0.5 pl-4">
          {lines.map((line) => (
            <li key={line}>{line}</li>
          ))}
        </ul>
        <p className="text-xs">
          Vẫn lưu và gửi duyệt được, nhưng lượt duyệt cuối sẽ bị chặn trừ khi người duyệt được miễn.
        </p>
      </div>
    </div>
  )
}
