import { useMemo } from 'react'

import { TimelineItem } from '@/shared/ui/timeline-item'
import type { EmployeeWorkHistoryRowActions } from '../config/employee-work-history-columns'
import type { EmployeeWorkHistory } from '../types/employee-work-history'
import { sortWorkHistoryNewestFirst, type WorkHistoryTimelineVariant } from '../utils/employee-work-history-display'
import { EmployeeWorkHistoryTimelineRow } from './employee-work-history-timeline-row'

export interface EmployeeWorkHistoryTimelineProps {
  items: EmployeeWorkHistory[]
  /** Khớp `WorkHistoryTimelineVariant` — ngày chính hiện ở đầu mốc khác nhau theo khu. */
  variant: WorkHistoryTimelineVariant
  canOpenFiles: boolean
  onOpenFiles: (row: EmployeeWorkHistory) => void
  /** Bỏ trống = chỉ đọc. Dùng LẠI đúng bộ handler của bảng, không có bản thứ hai. */
  actions?: EmployeeWorkHistoryRowActions
  emptyMessage: string
}

/**
 * Dòng thời gian DÙNG CHUNG cho cả hai khu («Quyết định bổ nhiệm» · «Quá trình
 * công tác») ở tab hồ sơ VÀ thẻ Trang cá nhân `/me` (đại ca chốt 03/10/2026) —
 * một component, nhận `items` đã lọc sẵn (theo khu) từ nơi gọi, không tự gọi
 * API. Mốc MỚI NHẤT ở trên (`sortWorkHistoryNewestFirst`, không tin thứ tự
 * `items` truyền vào).
 *
 * Khuôn trục dọc dùng lại `TimelineItem` của `shared/ui/timeline-item.tsx`
 * (cùng khuôn với Đặt xe/Duyệt dấu) — chấm tròn đặc + đường nối, không gán ý
 * nghĩa trạng thái cho màu chấm (khác `TimelineMarker` done/pending/stopped):
 * «Hiện tại» đã có badge riêng trong nội dung mốc.
 */
export function EmployeeWorkHistoryTimeline({
  items,
  variant,
  canOpenFiles,
  onOpenFiles,
  actions,
  emptyMessage,
}: EmployeeWorkHistoryTimelineProps) {
  const sorted = useMemo(() => sortWorkHistoryNewestFirst(items), [items])

  if (sorted.length === 0) {
    return <p className="py-6 text-center text-sm text-muted-foreground">{emptyMessage}</p>
  }

  return (
    <ol className="flex flex-col">
      {sorted.map((row, index) => (
        <TimelineItem
          key={row.id}
          last={index === sorted.length - 1}
          marker={<span aria-hidden="true" className="mt-1.5 size-2.5 shrink-0 rounded-full bg-primary" />}
        >
          <EmployeeWorkHistoryTimelineRow
            row={row}
            variant={variant}
            canOpenFiles={canOpenFiles}
            onOpenFiles={onOpenFiles}
            actions={actions}
          />
        </TimelineItem>
      ))}
    </ol>
  )
}
