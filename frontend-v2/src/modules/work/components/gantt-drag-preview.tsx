import { useDndMonitor } from '@dnd-kit/core'
import { useState } from 'react'

import { cn } from '@/shared/utils/cn'
import { formatDueLabel } from '../utils/due-date'
import { daysDragged, shiftedRange, type GanttDragData } from '../utils/gantt-drag'
import { ROW_HEIGHT } from '../utils/gantt-layout'
import type { GanttTimeline } from '../utils/gantt-scale'
import { chipClass } from '../utils/work-colors'

interface GanttDragPreviewProps {
  data: GanttDragData
  timeline: GanttTimeline
  /** Cùng màu với thanh thật đang kéo — xem `GanttRow`. */
  barColor: string
}

/**
 * Nội dung lớp phủ lúc kéo trên Gantt — thứ DUY NHẤT vẽ lại theo từng nhịp
 * chuột. Số ngày đang dời được giữ trong state CỦA RIÊNG component này
 * (`useDndMonitor`), không đẩy ngược lên `GanttView`: đẩy lên là cả biểu đồ —
 * lưới trái, hai hàng tiêu đề, hàng trăm ô ngày — dựng lại mỗi lần chuột nhích.
 *
 * dnd-kit đặt lớp phủ đúng chỗ nút đang kéo rồi dịch theo con trỏ, nên kéo cả
 * thanh thì vẽ bản sao của thanh, còn kéo mép thì vẽ một vạch dẫn — người dùng
 * thấy mép sẽ rơi vào ngày nào trước khi thả.
 */
export function GanttDragPreview({ data, timeline, barColor }: GanttDragPreviewProps) {
  const [days, setDays] = useState(0)

  useDndMonitor({
    onDragMove: (e) => {
      const moi = daysDragged(e.delta.x, timeline.dayWidth)
      setDays((cu) => (cu === moi ? cu : moi))
    },
  })

  const { task, kind } = data
  const range = shiftedRange(task, kind, days)
  const nhanNgay = range ? `${formatDueLabel(range.start)} → ${formatDueLabel(range.due)}` : ''
  //  Ngày ngược thì `datesToSave` sẽ bỏ cú kéo — báo trước bằng màu để khỏi thả
  //  ra rồi ngồi đoán vì sao không có gì đổi.
  const hopLe = !range || range.start <= range.due

  if (kind === 'move') {
    return (
      //  Chú thích phải nằm NGOÀI thẻ có `overflow-hidden`, không thì nó bị cắt
      //  đúng ở mép thanh và chỉ còn thấy một mẩu.
      <div className="relative h-full w-full">
        <div
          className={cn(
            'flex h-full w-full items-center overflow-hidden rounded px-2 text-[11px] font-medium shadow-lg ring-2',
            chipClass(barColor),
            hopLe ? 'ring-primary/60' : 'ring-destructive',
          )}
        >
          <span className="truncate">{task.title}</span>
        </div>
        <DateChip valid={hopLe}>{nhanNgay}</DateChip>
      </div>
    )
  }

  return (
    <div className="relative h-full w-full">
      <span
        aria-hidden
        className={cn('absolute left-1/2 w-0.5 rounded', hopLe ? 'bg-primary' : 'bg-destructive')}
        style={{ top: -ROW_HEIGHT / 3, bottom: -ROW_HEIGHT / 3 }}
      />
      <DateChip valid={hopLe}>{nhanNgay}</DateChip>
    </div>
  )
}

/** Chú thích ngày mới, luôn nằm bên phải con trỏ và không bị lớp phủ cắt. */
function DateChip({ valid, children }: { valid: boolean; children: React.ReactNode }) {
  return (
    <span
      className={cn(
        'absolute top-1/2 left-full ml-2 -translate-y-1/2 rounded px-2 py-1 text-[11px] whitespace-nowrap',
        valid ? 'bg-foreground text-background' : 'bg-destructive text-destructive-foreground',
      )}
    >
      {children}
    </span>
  )
}
